"""Java code execution service using OpenJDK (Docker or Subprocess)"""
import os
import subprocess
import tempfile
import re
import time
import io
import tarfile
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
    
    def compile_and_execute(self, java_code: str, input_data: str = "") -> Dict:
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
        java_code = self._normalize_newlines(java_code)
        validation_errors = self._validate_structure(java_code)
        if self.use_docker:
            result = self._execute_with_docker(java_code, input_data=input_data)
        else:
            result = self._execute_with_subprocess(java_code, input_data=input_data)
        if (not result.get("success")) and (not result.get("errors")) and validation_errors:
            result["errors"] = validation_errors
        return result

    def compile_only(self, java_code: str) -> Dict:
        """
        Compile Java code without executing it.

        Useful for fast syntax validation flows (e.g., explainer pre-checks)
        where runtime execution is unnecessary and can add latency/timeouts.
        """
        java_code = self._normalize_newlines(java_code)
        validation_errors = self._validate_structure(java_code)
        with tempfile.TemporaryDirectory() as temp_dir:
            class_name = self._extract_class_name(java_code)
            java_file = os.path.join(temp_dir, f"{class_name}.java")
            with open(java_file, 'w', encoding='utf-8') as f:
                f.write(java_code)

            if self.use_docker:
                compile_result = self._docker_compile(temp_dir, class_name, java_code)
            else:
                compile_result = self._subprocess_compile(temp_dir, class_name, java_code)

        errors = compile_result.get("errors", [])
        if (not compile_result.get("success")) and (not errors) and validation_errors:
            errors = validation_errors

        return {
            "success": bool(compile_result.get("success")),
            "output": "",
            "errors": errors,
            "execution_time": 0,
            "compilation_time": float(compile_result.get("compilation_time", 0.0) or 0.0),
        }
    
    def _extract_class_name(self, java_code: str) -> str:
        """Extract class name from Java code"""
        match = re.search(r'public\s+class\s+(\w+)', java_code)
        if match:
            return match.group(1)
        fallback = re.search(r'\bclass\s+(\w+)', java_code)
        return fallback.group(1) if fallback else 'Main'

    def _normalize_newlines(self, java_code: str) -> str:
        return java_code.replace('\r\n', '\n').replace('\r', '\n')
    
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
        line_keys: List[str],
        index_map: Dict[str, List[int]],
        fuzzy_keys: List[str],
        fuzzy_map: Dict[str, List[int]]
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

    def _parse_compiler_errors(self, error_output: str, java_code: Optional[str] = None) -> List[Dict]:
        """Parse javac error output into structured error objects"""
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
                        "severity": "error",
                        "line": reported_line,
                        "column": column,
                        "message": message.strip(),
                        "file": filename
                    })
            index += 1
        return errors

    def _parse_runtime_error(self, error_output: str, class_name: Optional[str] = None) -> Dict:
        message_lines = [line for line in error_output.split('\n') if line.strip()]
        message = message_lines[0].strip() if message_lines else "Runtime error"
        matches = re.findall(r'\(([^)]+\.java):(\d+)\)', error_output)
        if matches:
            if class_name:
                target = f"{class_name}.java"
                for filename, line_num in matches:
                    if filename.endswith(target):
                        return {
                            "type": "runtime_error",
                            "line": int(line_num),
                            "column": 0,
                            "message": message,
                            "file": filename
                        }
            filename, line_num = matches[0]
            return {
                "type": "runtime_error",
                "line": int(line_num),
                "column": 0,
                "message": message,
                "file": filename
            }
        return {
            "type": "runtime_error",
            "line": 0,
            "column": 0,
            "message": message
        }

    def _validate_structure(self, java_code: str) -> List[Dict]:
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
    
    def _execute_with_docker(self, java_code: str, input_data: str = "") -> Dict:
        """Execute Java code using Docker"""
        class_name = self._extract_class_name(java_code)
        container = None
        compile_start = time.time()
        try:
            nano_cpus = int(self.cpu_limit * 1_000_000_000) if self.cpu_limit > 0 else None
            container = self.docker_client.containers.create(
                image=self.docker_image,
                command=["/bin/sh", "-c", "sleep 300"],
                working_dir='/app/workspace',
                mem_limit=self.memory_limit,
                nano_cpus=nano_cpus,
                network_disabled=True,
                user="0",
                detach=True
            )
            container.start()
            container.exec_run(["/bin/sh", "-lc", "mkdir -p /app/workspace && chmod 777 /app/workspace"], stdout=True, stderr=True)
            self._docker_put_text(container, f"/app/workspace/{class_name}.java", java_code)
            self._docker_put_text(container, "/app/workspace/__input.txt", input_data or "")
            compile_exec = container.exec_run(
                ["/opt/jdk-17.0.12/bin/javac", "-d", "/app/workspace", f"{class_name}.java"],
                stdout=True,
                stderr=True
            )
            compile_output = (compile_exec.output or b"").decode("utf-8", errors="replace")
            compilation_time = time.time() - compile_start
            if compile_exec.exit_code != 0:
                errors = self._parse_compiler_errors(compile_output, java_code)
                if not errors:
                    errors = [{
                        "type": "compilation_error",
                        "line": 0,
                        "column": 0,
                        "message": compile_output.strip() or "Compilation failed"
                    }]
                return {
                    "success": False,
                    "output": "",
                    "errors": errors,
                    "execution_time": 0,
                    "compilation_time": compilation_time
                }
            exec_start = time.time()
            run_exec = container.exec_run(
                ["/bin/sh", "-lc", f"/opt/jdk-17.0.12/bin/java -cp /app/workspace {class_name} < /app/workspace/__input.txt"],
                stdout=True,
                stderr=True
            )
            run_output = (run_exec.output or b"").decode("utf-8", errors="replace")
            execution_time = time.time() - exec_start
            if run_exec.exit_code == 0:
                return {
                    "success": True,
                    "output": run_output,
                    "errors": [],
                    "execution_time": execution_time,
                    "compilation_time": compilation_time
                }
            runtime_error = self._parse_runtime_error(run_output, class_name)
            return {
                "success": False,
                "output": run_output,
                "errors": [runtime_error],
                "execution_time": execution_time,
                "compilation_time": compilation_time
            }
        except Exception as e:
            self.logger.error(f"Docker execution error: {e}")
            return {
                "success": False,
                "output": "",
                "errors": [{"type": "system_error", "line": 0, "column": 0, "message": str(e)}],
                "execution_time": 0,
                "compilation_time": time.time() - compile_start
            }
        finally:
            if container:
                try:
                    container.remove(force=True)
                except Exception:
                    pass

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
    
    def _docker_compile(self, code_dir: str, class_name: str, java_code: str) -> Dict:
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
            
            errors = self._parse_compiler_errors(logs, java_code) if exit_code != 0 else []
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
    
    def _docker_execute(self, code_dir: str, class_name: str, input_data: str = "") -> Dict:
        """Execute compiled Java code in Docker container"""
        start_time = time.time()
        container = None
        
        try:
            nano_cpus = int(self.cpu_limit * 1_000_000_000) if self.cpu_limit > 0 else None
            input_file = "__input.txt"
            input_path = os.path.join(code_dir, input_file)
            with open(input_path, "w", encoding="utf-8") as f:
                f.write(input_data or "")
            execute_command = [
                "/bin/sh",
                "-lc",
                f"/opt/jdk-17.0.12/bin/java -cp /app/workspace {class_name} < /app/workspace/{input_file}",
            ]
            container = self.docker_client.containers.create(
                image=self.docker_image,
                command=execute_command,
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
            
            runtime_error = self._parse_runtime_error(logs, class_name)
            return {
                "success": False,
                "output": logs,
                "errors": [runtime_error],
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
    
    def _execute_with_subprocess(self, java_code: str, input_data: str = "") -> Dict:
        """Execute Java code using subprocess (OpenJDK on host)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            class_name = self._extract_class_name(java_code)
            java_file = os.path.join(temp_dir, f"{class_name}.java")
            
            with open(java_file, 'w', encoding='utf-8') as f:
                f.write(java_code)
            
            # Compile
            compile_result = self._subprocess_compile(temp_dir, class_name, java_code)
            if not compile_result["success"]:
                return {
                    "success": False,
                    "output": "",
                    "errors": compile_result["errors"],
                    "execution_time": 0,
                    "compilation_time": compile_result["compilation_time"]
                }
            
            # Execute
            execute_result = self._subprocess_execute(temp_dir, class_name, input_data=input_data)
            
            return {
                "success": execute_result["success"],
                "output": execute_result["output"],
                "errors": execute_result.get("errors", []),
                "execution_time": execute_result["execution_time"],
                "compilation_time": compile_result["compilation_time"]
            }
    
    def _subprocess_compile(self, code_dir: str, class_name: str, java_code: str) -> Dict:
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
            error_text = stderr or ""
            errors = self._parse_compiler_errors(error_text, java_code) if exit_code != 0 else []
            if exit_code != 0 and not errors:
                errors = [{"type": "compilation_error", "line": 0, "column": 0, "message": error_text.strip() or "Compilation failed"}]
            
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
    
    def _subprocess_execute(self, code_dir: str, class_name: str, input_data: str = "") -> Dict:
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
            
            stdout, stderr = process.communicate(input=input_data or "", timeout=self.timeout)
            exit_code = process.returncode
            output = stdout + (stderr if exit_code != 0 else "")
            
            if exit_code == 0:
                return {
                    "success": True,
                    "output": output,
                    "execution_time": time.time() - start_time
                }
            return {
                "success": False,
                "output": output,
                "errors": [self._parse_runtime_error(output, class_name)],
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
