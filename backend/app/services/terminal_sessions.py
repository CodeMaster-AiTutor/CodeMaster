import os
import re
import time
import uuid
import shutil
import tempfile
import threading
import subprocess
import queue
import io
import tarfile
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

def _normalize_newlines(java_code: str) -> str:
    return java_code.replace('\r\n', '\n').replace('\r', '\n')

def _create_docker_client() -> docker.DockerClient:
    try:
        client = docker.from_env()
        client.ping()
        return client
    except Exception as e:
        raise RuntimeError(f"Docker connection failed: {e}")


class TerminalSession:
    def __init__(self, session_id: str, container_id: Optional[str], temp_dir: str, user_id: Optional[int], process: Optional[subprocess.Popen] = None):
        self.session_id = session_id
        self.container_id = container_id
        self.temp_dir = temp_dir
        self.user_id = user_id
        self.process = process
        self.created_at = time.time()
        self.last_activity = time.time()
        self.output_bytes = 0
        self.active = True
        self.output_queue: Optional[queue.Queue] = None
        self.socket = None
        self.stop_event: Optional[threading.Event] = None
        self.reader_thread: Optional[threading.Thread] = None

    def touch(self):
        self.last_activity = time.time()


class TerminalSessionManager:
    def __init__(self):
        self.use_docker = True
        self.docker_client = _create_docker_client()
        self.api_client = self.docker_client.api if self.docker_client else None
        self.image = Config.DOCKER_IMAGE
        self.memory_limit = Config.JAVA_MEMORY_LIMIT
        self.cpu_limit = Config.JAVA_CPU_LIMIT
        self.idle_timeout = Config.TERMINAL_IDLE_TIMEOUT
        self.max_runtime = Config.TERMINAL_MAX_RUNTIME
        self.output_limit = Config.TERMINAL_OUTPUT_LIMIT
        self.require_auth = Config.TERMINAL_REQUIRE_AUTH
        self.javac_path = Config.JAVAC_PATH
        self.java_path = Config.JAVA_PATH
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
        if not self.use_docker:
            return
        try:
            self.docker_client.images.get(self.image)
        except docker.errors.ImageNotFound:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "docker_env", "java17"))
            self.docker_client.images.build(path=base_dir, tag=self.image)

    def _normalize_line_for_match(self, line: str) -> str:
        cleaned = []
        in_string = False
        in_char = False
        escape = False
        string_len = 0
        char_len = 0
        for ch in line:
            if in_string:
                if escape:
                    escape = False
                    string_len += 1
                    continue
                if ch == '\\':
                    escape = True
                    string_len += 1
                    continue
                if ch == '"':
                    cleaned.append(f'"<str:{string_len}>"')
                    in_string = False
                    string_len = 0
                    continue
                string_len += 1
                continue
            if in_char:
                if escape:
                    escape = False
                    char_len += 1
                    continue
                if ch == '\\':
                    escape = True
                    char_len += 1
                    continue
                if ch == "'":
                    cleaned.append(f"'<char:{char_len}>'")
                    in_char = False
                    char_len = 0
                    continue
                char_len += 1
                continue
            if ch == '"':
                in_string = True
                string_len = 0
                continue
            if ch == "'":
                in_char = True
                char_len = 0
                continue
            cleaned.append(ch)
        if in_string:
            cleaned.append(f'"<str:{string_len}>"')
        if in_char:
            cleaned.append(f"'<char:{char_len}>'")
        return re.sub(r'\s+', '', ''.join(cleaned)).strip()

    def _normalize_line_for_fuzzy(self, line: str) -> str:
        return re.sub(r'\s+', '', line).strip()

    def _strip_ansi(self, text: str) -> str:
        return re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '', text)

    def _build_line_index(self, java_code: str):
        lines = []
        index_map = {}
        fuzzy_lines = []
        fuzzy_map = {}
        try:
            line_chars = []
            line_no = 1
            in_single = False
            in_multi = False
            in_string = False
            in_char = False
            escape = False
            index = 0
            while index < len(java_code):
                ch = java_code[index]
                next_ch = java_code[index + 1] if index + 1 < len(java_code) else ''
                if ch == '\n':
                    raw_line = ''.join(line_chars)
                    normalized = self._normalize_line_for_match(raw_line)
                    fuzzy = self._normalize_line_for_fuzzy(raw_line)
                    lines.append(normalized)
                    fuzzy_lines.append(fuzzy)
                    if normalized:
                        index_map.setdefault(normalized, []).append(line_no)
                    if fuzzy:
                        fuzzy_map.setdefault(fuzzy, []).append(line_no)
                    line_chars = []
                    line_no += 1
                    in_single = False
                    index += 1
                    continue
                if in_single:
                    index += 1
                    continue
                if in_multi:
                    if ch == '*' and next_ch == '/':
                        in_multi = False
                        index += 2
                        continue
                    index += 1
                    continue
                if in_string:
                    if escape:
                        escape = False
                    elif ch == '\\':
                        escape = True
                    elif ch == '"':
                        in_string = False
                    line_chars.append(ch)
                    index += 1
                    continue
                if in_char:
                    if escape:
                        escape = False
                    elif ch == '\\':
                        escape = True
                    elif ch == "'":
                        in_char = False
                    line_chars.append(ch)
                    index += 1
                    continue
                if ch == '/' and next_ch == '/':
                    in_single = True
                    index += 2
                    continue
                if ch == '/' and next_ch == '*':
                    in_multi = True
                    index += 2
                    continue
                if ch == '"':
                    in_string = True
                    line_chars.append(ch)
                    index += 1
                    continue
                if ch == "'":
                    in_char = True
                    line_chars.append(ch)
                    index += 1
                    continue
                line_chars.append(ch)
                index += 1
            raw_line = ''.join(line_chars)
            normalized = self._normalize_line_for_match(raw_line)
            fuzzy = self._normalize_line_for_fuzzy(raw_line)
            lines.append(normalized)
            fuzzy_lines.append(fuzzy)
            if normalized:
                index_map.setdefault(normalized, []).append(line_no)
            if fuzzy:
                fuzzy_map.setdefault(fuzzy, []).append(line_no)
        except Exception:
            return [], {}, [], {}
        return lines, index_map, fuzzy_lines, fuzzy_map

    def _find_best_line_match(
        self,
        normalized_context: str,
        fuzzy_context: str,
        reported_line: int,
        line_keys: list,
        index_map: Dict[str, list],
        fuzzy_keys: list,
        fuzzy_map: Dict[str, list]
    ) -> int:
        if not normalized_context:
            return reported_line
        if reported_line > 0 and reported_line <= len(line_keys):
            if line_keys[reported_line - 1] == normalized_context:
                return reported_line
        candidates = index_map.get(normalized_context)
        if not candidates:
            if not fuzzy_context:
                return reported_line
            if reported_line > 0 and reported_line <= len(fuzzy_keys):
                if fuzzy_keys[reported_line - 1] == fuzzy_context:
                    return reported_line
            fuzzy_candidates = fuzzy_map.get(fuzzy_context)
            if not fuzzy_candidates:
                return reported_line
            if reported_line > 0:
                return min(fuzzy_candidates, key=lambda value: abs(value - reported_line))
            return fuzzy_candidates[0]
        if reported_line > 0:
            return min(candidates, key=lambda value: abs(value - reported_line))
        return candidates[0]

    def _parse_compiler_errors(self, error_output: str, java_code: Optional[str] = None) -> list:
        errors = []
        source_line_count = 0
        if java_code:
            source_line_count = len(java_code.replace('\r\n', '\n').replace('\r', '\n').split('\n'))
        cleaned_output = self._strip_ansi(error_output)
        lines = cleaned_output.splitlines()
        index = 0
        while index < len(lines):
            line = lines[index]
            line_text = line.strip()
            if 'error:' in line_text.lower():
                match = re.search(r'(.+\.java):(\d+)(?::(\d+))?:\s*error:\s*(.+)', line_text)
                if match:
                    filename, line_num, col_num, message = match.groups()
                    column = int(col_num) if col_num else 0
                    if column == 0 and index + 2 < len(lines):
                        caret_index = lines[index + 2].find('^')
                        if caret_index != -1:
                            column = caret_index + 1
                    reported_line = int(line_num)
                    if source_line_count > 0 and (reported_line < 1 or reported_line > source_line_count):
                        reported_line = 0
                    errors.append({
                        "type": "compilation_error",
                        "line": reported_line,
                        "column": column,
                        "message": message.strip(),
                        "file": filename
                    })
            index += 1
        return errors

    def _validate_structure(self, java_code: str) -> list:
        errors = []
        stack = []
        line = 1
        column = 0
        in_single = False
        in_multi = False
        in_string = False
        in_char = False
        escape = False
        index = 0
        while index < len(java_code):
            ch = java_code[index]
            next_ch = java_code[index + 1] if index + 1 < len(java_code) else ''
            if ch == '\n':
                line += 1
                column = 0
                in_single = False
                index += 1
                continue
            column += 1
            if in_single:
                index += 1
                continue
            if in_multi:
                if ch == '*' and next_ch == '/':
                    in_multi = False
                    index += 2
                    column += 1
                    continue
                index += 1
                continue
            if in_string:
                if escape:
                    escape = False
                elif ch == '\\':
                    escape = True
                elif ch == '"':
                    in_string = False
                index += 1
                continue
            if in_char:
                if escape:
                    escape = False
                elif ch == '\\':
                    escape = True
                elif ch == "'":
                    in_char = False
                index += 1
                continue
            if ch == '/' and next_ch == '/':
                in_single = True
                index += 2
                column += 1
                continue
            if ch == '/' and next_ch == '*':
                in_multi = True
                index += 2
                column += 1
                continue
            if ch == '"':
                in_string = True
                index += 1
                continue
            if ch == "'":
                in_char = True
                index += 1
                continue
            if ch == '{' or ch == '(':
                stack.append((ch, line, column))
            elif ch == '}' or ch == ')':
                if not stack:
                    errors.append({
                        "type": "compilation_error",
                        "line": line,
                        "column": column,
                        "message": f"Unmatched closing '{ch}'"
                    })
                else:
                    opener, open_line, open_column = stack.pop()
                    if (opener == '{' and ch != '}') or (opener == '(' and ch != ')'):
                        errors.append({
                            "type": "compilation_error",
                            "line": line,
                            "column": column,
                            "message": f"Mismatched closing '{ch}'"
                        })
                        stack.append((opener, open_line, open_column))
            index += 1
        while stack:
            opener, open_line, open_column = stack.pop()
            errors.append({
                "type": "compilation_error",
                "line": open_line,
                "column": open_column,
                "message": f"Unmatched '{opener}'"
            })
        return errors

    def _docker_compile(self, code_dir: str, class_name: str, java_code: str) -> Dict:
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
            errors = self._parse_compiler_errors(logs, java_code)
            if not errors:
                errors = [{"type": "compilation_error", "line": 0, "column": 0, "message": logs.strip() or "Compilation failed"}]
            return {
                "success": False,
                "errors": errors,
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

    def _attach_container_socket(self, container_id: str):
        socket = self.api_client.attach_socket(
            container_id,
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
        except Exception:
            return socket._sock if hasattr(socket, '_sock') else socket

    def _start_output_reader(self, session: "TerminalSession"):
        if not session.socket or session.output_queue is None or session.stop_event is None:
            return

        def docker_reader():
            while not session.stop_event.is_set():
                try:
                    chunk = session.socket.recv(4096)
                    if chunk:
                        session.output_queue.put(chunk)
                    else:
                        time.sleep(0.01)
                except BlockingIOError:
                    time.sleep(0.01)
                except TimeoutError:
                    time.sleep(0.01)
                except Exception as e:
                    if "The pipe has been ended" in str(e) or "109" in str(e):
                        session.output_queue.put(None)
                        return
                    if "timed out" in str(e):
                        time.sleep(0.01)
                    else:
                        session.output_queue.put(None)
                        return

        session.reader_thread = threading.Thread(target=docker_reader, daemon=True)
        session.reader_thread.start()

    def _subprocess_compile(self, code_dir: str, class_name: str, java_code: str) -> Dict:
        start_time = time.time()
        process = None
        try:
            compile_cmd = [self.javac_path, "-d", code_dir, f"{class_name}.java"]
            process = subprocess.Popen(
                compile_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=code_dir
            )
            stdout, stderr = process.communicate(timeout=Config.JAVA_TIMEOUT)
            exit_code = process.returncode
            if exit_code == 0:
                return {"success": True, "errors": [], "compilation_time": time.time() - start_time}
            error_text = (stderr or stdout or b"").decode("utf-8", errors="replace")
            errors = self._parse_compiler_errors(error_text, java_code)
            if not errors:
                errors = [{"type": "compilation_error", "line": 0, "column": 0, "message": error_text.strip() or "Compilation failed"}]
            return {
                "success": False,
                "errors": errors,
                "compilation_time": time.time() - start_time
            }
        except subprocess.TimeoutExpired:
            if process:
                process.kill()
            return {
                "success": False,
                "errors": [{"type": "timeout", "line": 0, "column": 0, "message": f"Compilation timeout ({Config.JAVA_TIMEOUT}s)"}],
                "compilation_time": time.time() - start_time
            }
        except Exception as e:
            if process:
                try:
                    process.kill()
                except Exception:
                    pass
            return {
                "success": False,
                "errors": [{"type": "system_error", "line": 0, "column": 0, "message": str(e)}],
                "compilation_time": time.time() - start_time
            }

    def start_session(self, java_code: str, user_id: Optional[int]) -> Dict:
        java_code = _normalize_newlines(java_code)
        temp_dir = tempfile.mkdtemp(prefix="codemaster-java-")
        class_name = _extract_class_name(java_code)
        java_file = os.path.join(temp_dir, f"{class_name}.java")
        with open(java_file, "w", encoding="utf-8") as f:
            f.write(java_code)
        validation_errors = self._validate_structure(java_code)
        try:
            if self.use_docker:
                self._ensure_image()
                nano_cpus = int(self.cpu_limit * 1_000_000_000) if self.cpu_limit > 0 else None
                container = self.docker_client.containers.create(
                    image=self.image,
                    command=["/bin/sh", "-lc", f"while [ ! -f /app/workspace/.start ]; do sleep 0.05; done; /usr/bin/script -qf -c '/usr/bin/stdbuf -o0 -e0 /opt/jdk-17.0.12/bin/java -cp /app/workspace {class_name}' /dev/null"],
                    working_dir="/app/workspace",
                    mem_limit=self.memory_limit,
                    nano_cpus=nano_cpus,
                    network_disabled=True,
                    user="0",
                    detach=True,
                    stdin_open=True,
                    tty=True
                )
                session_socket = self._attach_container_socket(container.id)
                if not session_socket:
                    container.remove(force=True)
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    return {"success": False, "errors": [{"type": "system_error", "line": 0, "column": 0, "message": "Unable to attach to container"}]}
                container.start()
                container.exec_run(["/bin/sh", "-lc", "mkdir -p /app/workspace && chmod 777 /app/workspace"], stdout=True, stderr=True)
                self._docker_put_text(container, f"/app/workspace/{class_name}.java", java_code)
                compile_start = time.time()
                compile_exec = container.exec_run(
                    ["/opt/jdk-17.0.12/bin/javac", "-d", "/app/workspace", f"{class_name}.java"],
                    stdout=True,
                    stderr=True
                )
                compilation_time = time.time() - compile_start
                if compile_exec.exit_code != 0:
                    compile_output = (compile_exec.output or b"").decode("utf-8", errors="replace")
                    errors = self._parse_compiler_errors(compile_output, java_code)
                    if not errors:
                        errors = [{"type": "compilation_error", "line": 0, "column": 0, "message": compile_output.strip() or "Compilation failed"}]
                    if not errors and validation_errors:
                        errors = validation_errors
                    try:
                        session_socket.close()
                    except Exception:
                        pass
                    container.remove(force=True)
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    return {"success": False, "errors": errors, "compilation_time": compilation_time}
                container.exec_run(["/bin/sh", "-lc", "touch /app/workspace/.start"], stdout=True, stderr=True)
                session_id = str(uuid.uuid4())
                session = TerminalSession(session_id=session_id, container_id=container.id, temp_dir=temp_dir, user_id=user_id)
                session.socket = session_socket
                session.output_queue = queue.Queue()
                session.stop_event = threading.Event()
                self._start_output_reader(session)
            else:
                compile_result = self._subprocess_compile(temp_dir, class_name, java_code)
                if not compile_result["success"]:
                    if not compile_result.get("errors") and validation_errors:
                        compile_result["errors"] = validation_errors
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    return {"success": False, "errors": compile_result["errors"], "compilation_time": compile_result["compilation_time"]}
                process = subprocess.Popen(
                    [self.java_path, "-cp", temp_dir, class_name],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=temp_dir
                )
                session_id = str(uuid.uuid4())
                session = TerminalSession(session_id=session_id, container_id=None, temp_dir=temp_dir, user_id=user_id, process=process)
            with self.lock:
                self.sessions[session_id] = session
            self._start_monitor(session_id)
            return {"success": True, "session_id": session_id, "compilation_time": compilation_time if self.use_docker else compile_result["compilation_time"]}
        except Exception as e:
            shutil.rmtree(temp_dir, ignore_errors=True)
            return {"success": False, "errors": [{"type": "system_error", "line": 0, "column": 0, "message": str(e)}]}

    def _docker_put_text(self, container, target_path: str, content: str) -> None:
        directory = os.path.dirname(target_path)
        filename = os.path.basename(target_path)
        buffer = io.BytesIO()
        data = content.encode("utf-8")
        with tarfile.open(fileobj=buffer, mode="w") as tar:
            info = tarfile.TarInfo(name=filename)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
        buffer.seek(0)
        container.put_archive(directory, buffer.read())

    def get_session(self, session_id: str) -> Optional[TerminalSession]:
        with self.lock:
            return self.sessions.get(session_id)

    def attach_socket(self, session_id: str):
        if not self.use_docker:
            return None
        session = self.get_session(session_id)
        if not session:
            return None
        return session.socket

    def stop_session(self, session_id: str):
        session = self.get_session(session_id)
        if not session:
            return
        session.active = False
        if session.stop_event:
            session.stop_event.set()
        if session.reader_thread and session.reader_thread.is_alive():
            session.reader_thread.join(timeout=0.2)
        if self.use_docker and session.container_id:
            try:
                container = self.docker_client.containers.get(session.container_id)
                container.remove(force=True)
            except Exception:
                pass
        if session.socket:
            try:
                session.socket.close()
            except Exception:
                pass
        if session.process:
            try:
                session.process.terminate()
                session.process.wait(timeout=2)
            except Exception:
                try:
                    session.process.kill()
                except Exception:
                    pass
            try:
                if session.process.stdin:
                    session.process.stdin.close()
                if session.process.stdout:
                    session.process.stdout.close()
                if session.process.stderr:
                    session.process.stderr.close()
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
                if session.process and session.process.poll() is not None:
                    self.stop_session(session_id)
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
