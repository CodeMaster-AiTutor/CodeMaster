import os
import re
import time
import uuid
import shutil
import tempfile
import threading
import docker
import requests
from typing import Dict, Optional
from app.config import Config
from app import db
from app.models.user import User
from flask_jwt_extended import decode_token


def _extract_class_name(java_code: str) -> str:
    match = re.search(r'\bclass\s+([A-Za-z_][A-Za-z0-9_]*)', java_code)
    return match.group(1) if match else "Main"

def _create_docker_client() -> docker.DockerClient:
    try:
        client = docker.from_env()
        client.ping()
        return client
    except Exception as e:
        raise RuntimeError(f"Docker connection failed: {e}")


class TerminalSession:
    def __init__(self, session_id: str, container_id: str, temp_dir: str, user_id: Optional[int]):
        self.session_id = session_id
        self.container_id = container_id
        self.temp_dir = temp_dir
        self.user_id = user_id
        self.created_at = time.time()
        self.last_activity = time.time()
        self.output_bytes = 0
        self.active = True

    def touch(self):
        self.last_activity = time.time()


class TerminalSessionManager:
    def __init__(self):
        self.docker_client = _create_docker_client()
        self.api_client = self.docker_client.api
        self.image = Config.DOCKER_IMAGE
        self.memory_limit = Config.JAVA_MEMORY_LIMIT
        self.cpu_limit = Config.JAVA_CPU_LIMIT
        self.idle_timeout = Config.TERMINAL_IDLE_TIMEOUT
        self.max_runtime = Config.TERMINAL_MAX_RUNTIME
        self.output_limit = Config.TERMINAL_OUTPUT_LIMIT
        self.require_auth = Config.TERMINAL_REQUIRE_AUTH
        self.sessions: Dict[str, TerminalSession] = {}
        self.lock = threading.Lock()

    def resolve_user(self, token: Optional[str]) -> Optional[User]:
        if not token:
            return None
        try:
            decoded = decode_token(token)
            identity = decoded.get("sub")
            user_id = int(identity) if isinstance(identity, str) and str(identity).isdigit() else identity
            return db.session.get(User, user_id)
        except Exception:
            return None

    def _ensure_image(self):
        try:
            self.docker_client.images.get(self.image)
        except docker.errors.ImageNotFound:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "docker_env", "java17"))
            self.docker_client.images.build(path=base_dir, tag=self.image)

    def _docker_compile(self, code_dir: str, class_name: str) -> Dict:
        start_time = time.time()
        container = None
        try:
            self._ensure_image()
            nano_cpus = int(self.cpu_limit * 1_000_000_000) if self.cpu_limit > 0 else None
            container = self.docker_client.containers.create(
                image=self.image,
                command=["/opt/jdk-17.0.12/bin/javac", "-d", "/app/workspace", f"{class_name}.java"],
                volumes={code_dir: {"bind": "/app/workspace", "mode": "rw"}},
                working_dir="/app/workspace",
                mem_limit=self.memory_limit,
                nano_cpus=nano_cpus,
                network_disabled=True,
                read_only=True,
                tmpfs={"/tmp": "size=50m"},
                user="runner",
                detach=True
            )
            container.start()
            result = container.wait(timeout=Config.JAVA_TIMEOUT)
            exit_code = result.get("StatusCode", 1)
            logs = container.logs(stdout=True, stderr=True).decode("utf-8")
            container.remove()
            if exit_code == 0:
                return {"success": True, "errors": [], "compilation_time": time.time() - start_time}
            return {
                "success": False,
                "errors": [{"type": "compilation_error", "line": 0, "column": 0, "message": logs.strip() or "Compilation failed"}],
                "compilation_time": time.time() - start_time
            }
        except requests.exceptions.ReadTimeout:
            if container:
                container.kill()
                container.remove(force=True)
            return {
                "success": False,
                "errors": [{"type": "timeout", "line": 0, "column": 0, "message": f"Compilation timeout ({Config.JAVA_TIMEOUT}s)"}],
                "compilation_time": time.time() - start_time
            }
        except Exception as e:
            if container:
                try:
                    container.remove(force=True)
                except Exception:
                    pass
            return {
                "success": False,
                "errors": [{"type": "system_error", "line": 0, "column": 0, "message": str(e)}],
                "compilation_time": time.time() - start_time
            }

    def start_session(self, java_code: str, user_id: Optional[int]) -> Dict:
        temp_dir = tempfile.mkdtemp(prefix="codemaster-java-")
        class_name = _extract_class_name(java_code)
        java_file = os.path.join(temp_dir, f"{class_name}.java")
        with open(java_file, "w", encoding="utf-8") as f:
            f.write(java_code)
        compile_result = self._docker_compile(temp_dir, class_name)
        if not compile_result["success"]:
            shutil.rmtree(temp_dir, ignore_errors=True)
            return {"success": False, "errors": compile_result["errors"], "compilation_time": compile_result["compilation_time"]}
        try:
            self._ensure_image()
            nano_cpus = int(self.cpu_limit * 1_000_000_000) if self.cpu_limit > 0 else None
            # Create container with unbuffered output to ensure prompts appear immediately
            container = self.docker_client.containers.create(
                image=self.image,
                command=["/usr/bin/stdbuf", "-o0", "-e0", "/opt/jdk-17.0.12/bin/java", "-cp", "/app/workspace", class_name],
                volumes={temp_dir: {"bind": "/app/workspace", "mode": "rw"}},
                working_dir="/app/workspace",
                mem_limit=self.memory_limit,
                nano_cpus=nano_cpus,
                network_disabled=True,
                read_only=True,
                tmpfs={"/tmp": "size=50m"},
                user="runner",
                detach=True,
                stdin_open=True,
                tty=True
            )
            container.start()
            session_id = str(uuid.uuid4())
            session = TerminalSession(session_id=session_id, container_id=container.id, temp_dir=temp_dir, user_id=user_id)
            with self.lock:
                self.sessions[session_id] = session
            self._start_monitor(session_id)
            return {"success": True, "session_id": session_id, "compilation_time": compile_result["compilation_time"]}
        except Exception as e:
            shutil.rmtree(temp_dir, ignore_errors=True)
            return {"success": False, "errors": [{"type": "system_error", "line": 0, "column": 0, "message": str(e)}]}

    def get_session(self, session_id: str) -> Optional[TerminalSession]:
        with self.lock:
            return self.sessions.get(session_id)

    def attach_socket(self, session_id: str):
        session = self.get_session(session_id)
        if not session:
            return None
        socket = self.api_client.attach_socket(
            session.container_id,
            params={"stdin": 1, "stdout": 1, "stderr": 1, "stream": 1, "logs": 1}
        )
        try:
            if hasattr(socket, '_sock'):
                sock = socket._sock
            else:
                sock = socket
            if hasattr(sock, 'setblocking'):
                sock.setblocking(False)
            if hasattr(sock, 'settimeout'):
                sock.settimeout(0.01)
            return sock
        except Exception as e:
            print(f"Warning: Failed to set socket timeout: {e}")
            return socket._sock if hasattr(socket, '_sock') else socket

    def stop_session(self, session_id: str):
        session = self.get_session(session_id)
        if not session:
            return
        session.active = False
        try:
            container = self.docker_client.containers.get(session.container_id)
            container.remove(force=True)
        except Exception:
            pass
        shutil.rmtree(session.temp_dir, ignore_errors=True)
        with self.lock:
            self.sessions.pop(session_id, None)

    def _start_monitor(self, session_id: str):
        def monitor():
            while True:
                session = self.get_session(session_id)
                if not session or not session.active:
                    return
                now = time.time()
                if now - session.created_at > self.max_runtime:
                    self.stop_session(session_id)
                    return
                if now - session.last_activity > self.idle_timeout:
                    self.stop_session(session_id)
                    return
                time.sleep(1)
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()


_terminal_manager_instance: Optional[TerminalSessionManager] = None


def get_terminal_manager() -> TerminalSessionManager:
    global _terminal_manager_instance
    if _terminal_manager_instance is None:
        _terminal_manager_instance = TerminalSessionManager()
    return _terminal_manager_instance
