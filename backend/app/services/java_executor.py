"""Java code execution service using OpenJDK (Docker or Subprocess)"""
import os
import subprocess
import tempfile
import re
import time
import docker
import requests
from typing import Dict, List, Optional
from app.config import Config
import logging

def _create_docker_client() -> docker.DockerClient:
    try:
        client = docker.from_env()
        client.ping()
        return client
    except Exception as e:
        raise RuntimeError(f"Docker connection failed: {e}")

class JavaExecutor:
    """Execute Java code using OpenJDK with error detection and parsing"""
    
    def __init__(self):
        self.logger = logging.getLogger('java_executor')
        self.use_docker = os.getenv('USE_DOCKER', 'true').lower() == 'true'
        self.timeout = int(os.getenv('JAVA_TIMEOUT', 10))
        self.memory_limit = os.getenv('JAVA_MEMORY_LIMIT', '128m')
        self.cpu_limit = float(os.getenv('JAVA_CPU_LIMIT', 0.5))
        
        if self.use_docker:
            try:
                self.docker_client = _create_docker_client()
                self.docker_image = os.getenv('DOCKER_IMAGE', 'codemaster-java17:local').lower()
            except Exception as e:
                self.logger.warning(f"Docker not available: {e}. Falling back to subprocess.")
                self.use_docker = False
        
        if not self.use_docker:
            self.javac_path = os.getenv('JAVAC_PATH', 'javac')
            self.java_path = os.getenv('JAVA_PATH', 'java')
            self._verify_openjdk()
    
    def _verify_openjdk(self):
        """Verify OpenJDK installation"""
        try:
            subprocess.run([self.javac_path, '-version'], 
                         capture_output=True, timeout=5, check=True)
            subprocess.run([self.java_path, '-version'], 
                         capture_output=True, timeout=5, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            raise Exception(f"OpenJDK not found. Install OpenJDK 17+ or use Docker.")
    
    def compile_and_execute(self, java_code: str) -> Dict:
        """
        Compile and execute Java code
        
        Returns:
        {
            "success": bool,
            "output": str,
            "errors": List[Dict],
            "execution_time": float,
            "compilation_time": float
        }
        """
        if self.use_docker:
            return self._execute_with_docker(java_code)
        else:
            return self._execute_with_subprocess(java_code)
    
    def _extract_class_name(self, java_code: str) -> str:
        """Extract class name from Java code"""
        match = re.search(r'public\s+class\s+(\w+)', java_code)
        if match:
            return match.group(1)
        fallback = re.search(r'\bclass\s+(\w+)', java_code)
        return fallback.group(1) if fallback else 'Main'
    
    def _parse_compiler_errors(self, error_output: str) -> List[Dict]:
        """Parse javac error output into structured error objects"""
        errors = []
        lines = error_output.split('\n')
        
        for line in lines:
            if 'error:' in line.lower():
                # Pattern: Main.java:5:12: error: cannot find symbol
                match = re.match(r'(\w+\.java):(\d+):(\d+):\s*error:\s*(.+)', line)
                if match:
                    filename, line_num, col_num, message = match.groups()
                    errors.append({
                        "type": "compilation_error",
                        "severity": "error",
                        "line": int(line_num),
                        "column": int(col_num),
                        "message": message.strip(),
                        "file": filename
                    })
        
        return errors
    
    def _execute_with_docker(self, java_code: str) -> Dict:
        """Execute Java code using Docker"""
        with tempfile.TemporaryDirectory() as temp_dir:
            class_name = self._extract_class_name(java_code)
            java_file = os.path.join(temp_dir, f"{class_name}.java")
            
            with open(java_file, 'w', encoding='utf-8') as f:
                f.write(java_code)
            
            # Compile
            compile_result = self._docker_compile(temp_dir, class_name)
            if not compile_result["success"]:
                return {
                    "success": False,
                    "output": "",
                    "errors": compile_result["errors"],
                    "execution_time": 0,
                    "compilation_time": compile_result["compilation_time"]
                }
            
            # Execute
            execute_result = self._docker_execute(temp_dir, class_name)
            
            return {
                "success": execute_result["success"],
                "output": execute_result["output"],
                "errors": execute_result.get("errors", []),
                "execution_time": execute_result["execution_time"],
                "compilation_time": compile_result["compilation_time"]
            }
    
    def _docker_compile(self, code_dir: str, class_name: str) -> Dict:
        """Compile Java code in Docker container"""
        start_time = time.time()
        container = None
        
        try:
            nano_cpus = int(self.cpu_limit * 1_000_000_000) if self.cpu_limit > 0 else None
            container = self.docker_client.containers.create(
                image=self.docker_image,
                command=["/opt/jdk-17.0.12/bin/javac", "-d", "/app/workspace", f"{class_name}.java"],
                volumes={code_dir: {'bind': '/app/workspace', 'mode': 'rw'}},
                working_dir='/app/workspace',
                mem_limit=self.memory_limit,
                nano_cpus=nano_cpus,
                network_disabled=True,
                read_only=True,
                tmpfs={'/tmp': 'size=50m'},
                user="0",
                detach=True
            )
            
            container.start()
            try:
                result = container.wait(timeout=self.timeout)
                exit_code = result['StatusCode']
            except requests.exceptions.ReadTimeout:
                container.kill()
                container.remove(force=True)
                return {
                    "success": False,
                    "errors": [{"type": "timeout", "line": 0, "column": 0,
                               "message": f"Compilation timeout ({self.timeout}s)"}],
                    "compilation_time": time.time() - start_time
                }
            logs = container.logs(stdout=True, stderr=True).decode('utf-8')
            container.remove()
            
            errors = self._parse_compiler_errors(logs) if exit_code != 0 else []
            if exit_code != 0 and not errors:
                errors = [{"type": "compilation_error", "line": 0, "column": 0, "message": logs.strip() or "Compilation failed"}]
            
            return {
                "success": exit_code == 0,
                "errors": errors,
                "compilation_time": time.time() - start_time
            }
        except docker.errors.ImageNotFound:
            self.logger.error(f"Docker image not found: {self.docker_image}")
            return {
                "success": False,
                "errors": [{"type": "system_error", "line": 0, "column": 0,
                           "message": f"Docker image '{self.docker_image}' not found. Build it first."}],
                "compilation_time": time.time() - start_time
            }
        except Exception as e:
            self.logger.error(f"Docker compile error: {e}")
            if container:
                try:
                    container.remove()
                except:
                    pass
            return {
                "success": False,
                "errors": [{"type": "system_error", "line": 0, "column": 0, "message": str(e)}],
                "compilation_time": time.time() - start_time
            }
    
    def _docker_execute(self, code_dir: str, class_name: str) -> Dict:
        """Execute compiled Java code in Docker container"""
        start_time = time.time()
        container = None
        
        try:
            nano_cpus = int(self.cpu_limit * 1_000_000_000) if self.cpu_limit > 0 else None
            container = self.docker_client.containers.create(
                image=self.docker_image,
                command=["/opt/jdk-17.0.12/bin/java", "-cp", "/app/workspace", class_name],
                volumes={code_dir: {'bind': '/app/workspace', 'mode': 'rw'}},
                working_dir='/app/workspace',
                mem_limit=self.memory_limit,
                nano_cpus=nano_cpus,
                network_disabled=True,
                read_only=True,
                tmpfs={'/tmp': 'size=50m'},
                user="0",
                detach=True
            )
            
            container.start()
            try:
                result = container.wait(timeout=self.timeout)
                exit_code = result['StatusCode']
            except requests.exceptions.ReadTimeout:
                container.kill()
                container.remove(force=True)
                return {
                    "success": False,
                    "output": "",
                    "errors": [{"type": "timeout", "line": 0, "column": 0,
                               "message": f"Execution timeout ({self.timeout}s)"}],
                    "execution_time": time.time() - start_time
                }
            logs = container.logs(stdout=True, stderr=True).decode('utf-8')
            container.remove()
            if exit_code == 0:
                return {
                    "success": True,
                    "output": logs,
                    "execution_time": time.time() - start_time
                }
            
            error_message = logs.strip() or "Execution failed with non-zero exit code"
            return {
                "success": False,
                "output": logs,
                "errors": [{"type": "runtime_error", "line": 0, "column": 0, "message": error_message}],
                "execution_time": time.time() - start_time
            }
        except Exception as e:
            self.logger.error(f"Docker execute error: {e}")
            if container:
                try:
                    container.remove()
                except:
                    pass
            return {
                "success": False,
                "output": "",
                "errors": [{"type": "system_error", "line": 0, "column": 0, "message": str(e)}],
                "execution_time": time.time() - start_time
            }
    
    def _execute_with_subprocess(self, java_code: str) -> Dict:
        """Execute Java code using subprocess (OpenJDK on host)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            class_name = self._extract_class_name(java_code)
            java_file = os.path.join(temp_dir, f"{class_name}.java")
            
            with open(java_file, 'w', encoding='utf-8') as f:
                f.write(java_code)
            
            # Compile
            compile_result = self._subprocess_compile(temp_dir, class_name)
            if not compile_result["success"]:
                return {
                    "success": False,
                    "output": "",
                    "errors": compile_result["errors"],
                    "execution_time": 0,
                    "compilation_time": compile_result["compilation_time"]
                }
            
            # Execute
            execute_result = self._subprocess_execute(temp_dir, class_name)
            
            return {
                "success": execute_result["success"],
                "output": execute_result["output"],
                "errors": execute_result.get("errors", []),
                "execution_time": execute_result["execution_time"],
                "compilation_time": compile_result["compilation_time"]
            }
    
    def _subprocess_compile(self, code_dir: str, class_name: str) -> Dict:
        """Compile Java code using subprocess"""
        start_time = time.time()
        
        try:
            compile_cmd = [self.javac_path, '-d', code_dir, f"{class_name}.java"]
            process = subprocess.Popen(
                compile_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=code_dir
            )
            
            stdout, stderr = process.communicate(timeout=self.timeout)
            exit_code = process.returncode
            errors = self._parse_compiler_errors(stderr) if exit_code != 0 else []
            
            return {
                "success": exit_code == 0,
                "errors": errors,
                "compilation_time": time.time() - start_time
            }
        except subprocess.TimeoutExpired:
            process.kill()
            return {
                "success": False,
                "errors": [{"type": "timeout", "line": 0, "column": 0,
                           "message": f"Compilation timeout ({self.timeout}s)"}],
                "compilation_time": time.time() - start_time
            }
        except Exception as e:
            return {
                "success": False,
                "errors": [{"type": "system_error", "line": 0, "column": 0, "message": str(e)}],
                "compilation_time": time.time() - start_time
            }
    
    def _subprocess_execute(self, code_dir: str, class_name: str) -> Dict:
        """Execute compiled Java code using subprocess"""
        start_time = time.time()
        
        try:
            execute_cmd = [self.java_path, '-cp', code_dir, class_name]
            process = subprocess.Popen(
                execute_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=code_dir
            )
            
            stdout, stderr = process.communicate(timeout=self.timeout)
            exit_code = process.returncode
            output = stdout + (stderr if exit_code != 0 else "")
            
            return {
                "success": exit_code == 0,
                "output": output,
                "execution_time": time.time() - start_time
            }
        except subprocess.TimeoutExpired:
            process.kill()
            return {
                "success": False,
                "output": "",
                "errors": [{"type": "timeout", "line": 0, "column": 0,
                           "message": f"Execution timeout ({self.timeout}s)"}],
                "execution_time": time.time() - start_time
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "errors": [{"type": "system_error", "line": 0, "column": 0, "message": str(e)}],
                "execution_time": time.time() - start_time
            }

# Singleton instance
_java_executor_instance = None

def get_java_executor() -> JavaExecutor:
    """Get singleton Java executor instance"""
    global _java_executor_instance
    if _java_executor_instance is None:
        _java_executor_instance = JavaExecutor()
    return _java_executor_instance
