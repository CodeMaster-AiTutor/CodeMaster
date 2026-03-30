"""AI Service for code generation, explanation, and error fix suggestions using free models (Ollama/Hugging Face)"""
import os
import requests
import importlib.util
from typing import Dict, List, Optional

class AIService:
    """AI Service using Ollama (free, local) or Hugging Face Inference API"""
    
    def __init__(self):
        requested_service = os.getenv('AI_SERVICE', 'local_llm').lower().strip()
        if requested_service in ('', 'local', 'local_llm', 'rag'):
            self.service_type = 'local_llm'
        elif requested_service == 'ollama':
            self.service_type = 'ollama'
        else:
            self.service_type = requested_service
        self.ollama_base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.ollama_model = os.getenv('OLLAMA_MODEL', 'codellama:13b')
        self.huggingface_api_key = os.getenv('HUGGINGFACE_API_KEY', '')
        self.openrouter_api_key = os.getenv('OPENROUTER_API_KEY', '').strip()
        self.openrouter_model = os.getenv('OPENROUTER_MODEL', 'qwen/qwen3-coder:free').strip()
        self.openrouter_url = os.getenv('OPENROUTER_API_URL', 'https://openrouter.ai/api/v1/chat/completions').strip()
        self.error_fix_source = os.getenv('AI_ERROR_FIX_SOURCE', 'local_llm').lower().strip()
        self._rag_instance = None
        
    def _build_ollama_prompt(self, task: str, context: str, java_code: Optional[str] = None) -> str:
        """Build prompt for Ollama/Codellama with Java-specific context"""
        base_prompt = f"""You are a Java programming expert and code assistant. 
Focus only on Java programming language. Provide clear, concise, and educational responses.

Task: {task}
"""
        if java_code:
            base_prompt += f"\nJava Code:\n```java\n{java_code}\n```\n"
        if context:
            base_prompt += f"\nContext: {context}\n"
        
        base_prompt += "\nProvide your response:"
        return base_prompt
    
    def generate_code(self, prompt: str, context: Optional[str] = None) -> str:
        """
        Generate Java code from natural language prompt
        
        Args:
            prompt: User's natural language request
            context: Optional context or previous conversation
            
        Returns:
            Generated Java code
        """
        if self.service_type == 'openrouter':
            return self._generate_with_openrouter(prompt, context)
        elif self.service_type == 'ollama':
            return self._generate_with_ollama(prompt, context)
        elif self.service_type == 'huggingface':
            return self._generate_with_huggingface(prompt, context)
        elif self.service_type == 'local_llm':
            return self._generate_with_local_llm(prompt, context)
        else:
            raise ValueError(f"Unknown AI service type: {self.service_type}")
    
    def explain_code(self, java_code: str) -> str:
        """
        Explain Java code with line-by-line analysis
        
        Args:
            java_code: Java code to explain
            
        Returns:
            Explanation text
        """
        task = "Explain this Java code line by line, including: concepts used, how it works, and what each part does."
        context = "Focus on Java syntax, OOP concepts, and best practices."
        
        if self.service_type == 'openrouter':
            return self._explain_with_openrouter(java_code)
        elif self.service_type == 'ollama':
            full_prompt = self._build_ollama_prompt(task, context, java_code)
            return self._generate_with_ollama(full_prompt)
        elif self.service_type == 'huggingface':
            full_prompt = f"Explain this Java code:\n```java\n{java_code}\n```"
            return self._generate_with_huggingface(full_prompt)
        elif self.service_type == 'local_llm':
            return self._explain_with_local_llm(java_code)
        else:
            raise ValueError(f"Unknown AI service type: {self.service_type}")
    
    def suggest_error_fix(
        self,
        error_message: str,
        code_context: str,
        error_type: str,
        error_line: Optional[int] = None,
        error_column: Optional[int] = None
    ) -> Dict:
        """
        Suggest fix for compilation/runtime error
        
        Args:
            error_message: Error message from compiler/runtime
            code_context: Code snippet around the error
            error_type: Type of error (compilation_error, runtime_error, etc.)
            
        Returns:
            Dict with fix_suggestion, corrected_code, explanation
        """
        if self.error_fix_source in ('local', 'local_llm', 'rag', ''):
            try:
                return self._suggest_error_fix_with_local_llm(
                    error_message, code_context, error_type, error_line, error_column
                )
            except Exception:
                pass
        if self.service_type == 'openrouter' and self.openrouter_api_key:
            return self._suggest_error_fix_with_openrouter(
                error_message, code_context, error_type, error_line, error_column
            )
        task = f"Fix this Java {error_type}: {error_message}"
        context = "Provide: 1) Specific fix suggestion, 2) Corrected code snippet, 3) Brief explanation"
        if self.service_type == 'local_llm':
            full_prompt = f"Fix Java {error_type}: {error_message}\n\nCode:\n{code_context}"
            response = self._generate_with_local_llm(full_prompt)
        elif self.service_type == 'ollama':
            full_prompt = self._build_ollama_prompt(task, context, code_context)
            response = self._generate_with_ollama(full_prompt)
        elif self.service_type == 'huggingface':
            full_prompt = f"Fix Java error: {error_message}\nCode:\n{code_context}"
            response = self._generate_with_huggingface(full_prompt)
        else:
            raise ValueError(f"Unknown AI service type: {self.service_type}")
        return {
            'fix_suggestion': self._extract_fix_suggestion(response),
            'corrected_code': self._extract_code_snippet(response),
            'explanation': response[:500]  # First 500 chars as explanation
        }

    def _suggest_error_fix_with_local_llm(
        self,
        error_message: str,
        code_context: str,
        error_type: str,
        error_line: Optional[int] = None,
        error_column: Optional[int] = None
    ) -> Dict:
        rag = self._get_rag()
        error_line_text = self._get_line_text(code_context, error_line)
        if hasattr(rag, "explain_error"):
            content = rag.explain_error(
                error_message,
                code_context,
                error_type,
                error_line=error_line,
                error_column=error_column,
                error_line_text=error_line_text
            )
        else:
            prompt = (
                "You are a Java compiler error assistant.\n"
                f"Error type: {error_type}\n"
                f"Error message: {error_message}\n"
                f"Error line: {error_line if isinstance(error_line, int) and error_line > 0 else 'unknown'}\n"
                f"Error column: {error_column if isinstance(error_column, int) and error_column > 0 else 'unknown'}\n"
                f"Error line text: {error_line_text or 'unknown'}\n"
                f"Current Java code:\n{code_context}\n\n"
                "Respond in exactly 2 sections and keep headings exactly the same:\n"
                "Error Summary:\n"
                "<short explanation>\n\n"
                "Suggested Fix:\n"
                "<detailed explanation of why this error happened and how to resolve it>\n"
            )
            content = rag.ask(prompt)
        content = str(content or '').strip()
        summary = self._extract_section(content, "Error Summary")
        fix = self._extract_section(content, "Suggested Fix")
        combined_fix = fix or self._extract_fix_suggestion(content)
        if summary:
            combined_fix = f"Error Summary: {summary}\n\nSuggested Fix: {combined_fix}".strip()
        return {
            "fix_suggestion": combined_fix[:2400],
            "corrected_code": "",
            "explanation": "",
        }

    def _suggest_error_fix_with_openrouter(
        self,
        error_message: str,
        code_context: str,
        error_type: str,
        error_line: Optional[int] = None,
        error_column: Optional[int] = None
    ) -> Dict:
        if not self.openrouter_api_key:
            raise ValueError("OpenRouter API key not configured")
        error_line_text = self._get_line_text(code_context, error_line)
        user_prompt = (
            f"You are a Java compiler error assistant.\n"
            f"Error type: {error_type}\n"
            f"Error message: {error_message}\n"
            f"Error line: {error_line if isinstance(error_line, int) and error_line > 0 else 'unknown'}\n"
            f"Error column: {error_column if isinstance(error_column, int) and error_column > 0 else 'unknown'}\n"
            f"Error line text: {error_line_text or 'unknown'}\n"
            f"Current Java code:\n{code_context}\n\n"
            f"Explain in very simple language for beginners.\n"
            f"Respond in exactly 2 sections and keep headings exactly the same:\n"
            f"Suggested Fix:\n"
            f"<one concise actionable fix>\n\n"
            f"Detailed Explanation:\n"
            f"<detailed explanation of why this error happened in this code and how the fix solves it>"
        )
        content = self._openrouter_chat(user_prompt, temperature=0.2)
        fix = self._extract_section(content, "Suggested Fix")
        explanation = self._extract_section(content, "Detailed Explanation")
        return {
            "fix_suggestion": fix or self._extract_fix_suggestion(content),
            "corrected_code": "",
            "explanation": (explanation or content)[:2200],
        }

    def _get_line_text(self, code_context: str, error_line: Optional[int]) -> str:
        if not code_context or not isinstance(error_line, int) or error_line <= 0:
            return ""
        lines = code_context.replace('\r\n', '\n').replace('\r', '\n').split('\n')
        if error_line > len(lines):
            return ""
        return lines[error_line - 1].strip()

    def _openrouter_chat(self, prompt: str, temperature: float = 0.2) -> str:
        if not self.openrouter_api_key:
            raise ValueError("OpenRouter API key not configured")
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.openrouter_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
        }
        response = requests.post(self.openrouter_url, headers=headers, json=payload, timeout=60)
        if response.status_code == 429:
            raise Exception("OpenRouter rate limit reached (429). Please retry after a short delay.")
        response.raise_for_status()
        data = response.json() if response.content else {}
        content = (
            (((data.get("choices") or [{}])[0]).get("message") or {}).get("content")
            if isinstance(data, dict)
            else ""
        ) or ""
        return str(content).strip()

    def _generate_with_openrouter(self, prompt: str, context: Optional[str] = None) -> str:
        full_prompt = (
            "Generate only compilable Java code. Do not include markdown fences, headings, "
            "or explanation.\n\n"
            f"Request:\n{prompt.strip()}"
        )
        if context:
            full_prompt += f"\n\nContext:\n{context.strip()}"
        content = self._openrouter_chat(full_prompt, temperature=0.2)
        return self._sanitize_generated_code(self._extract_code_snippet(content) or content)

    def _explain_with_openrouter(self, java_code: str) -> str:
        prompt = (
            "Explain this Java code in simple language.\n"
            "Return only bullet points, one point per line, no paragraph blocks.\n\n"
            f"Code:\n{java_code}"
        )
        content = self._openrouter_chat(prompt, temperature=0.2)
        return self._format_explanation_as_bullets(content)

    def _extract_section(self, text: str, heading: str) -> str:
        import re
        if not text:
            return ""
        pattern = rf"{re.escape(heading)}\s*:\s*([\s\S]*?)(?:\n[A-Za-z][A-Za-z ]{{2,40}}:\s*|$)"
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if not match:
            return ""
        return match.group(1).strip()
    
    def improve_code(self, java_code: str, focus_areas: Optional[List[str]] = None) -> List[Dict]:
        """
        Suggest code improvements
        
        Args:
            java_code: Java code to improve
            focus_areas: Optional list of areas to focus on (optimization, best_practices, etc.)
            
        Returns:
            List of improvement suggestions with before/after code
        """
        focus = ', '.join(focus_areas) if focus_areas else 'optimization, best practices, code style'
        task = f"Suggest improvements for this Java code focusing on: {focus}"
        context = "For each improvement, provide: 1) Type of improvement, 2) Current code, 3) Improved code, 4) Reason"
        
        if self.service_type == 'openrouter':
            response = self._openrouter_chat(
                f"Suggest Java code improvements focused on {focus}. "
                f"Keep suggestions practical and concise.\n\nCode:\n{java_code}",
                temperature=0.2
            )
        elif self.service_type == 'local_llm':
            response = self._generate_with_local_llm(
                f"Improve this Java code ({focus}). Return practical improvements with examples:\n{java_code}"
            )
        elif self.service_type == 'ollama':
            full_prompt = self._build_ollama_prompt(task, context, java_code)
            response = self._generate_with_ollama(full_prompt)
        elif self.service_type == 'huggingface':
            full_prompt = f"Improve this Java code ({focus}):\n```java\n{java_code}\n```"
            response = self._generate_with_huggingface(full_prompt)
        else:
            raise ValueError(f"Unknown AI service type: {self.service_type}")
        
        # Parse improvements from response
        return self._parse_improvements(response, java_code)
    
    def _generate_with_ollama(self, prompt: str, context: Optional[str] = None) -> str:
        """Generate response using Ollama API"""
        try:
            final_prompt = prompt
            if context:
                final_prompt = f"{prompt}\n\nContext:\n{context}"
            url = f"{self.ollama_base_url}/api/generate"
            payload = {
                "model": self.ollama_model,
                "prompt": final_prompt,
                "stream": False
            }
            
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            return result.get('response', '')
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Ollama API error: {str(e)}")
    
    def _generate_with_huggingface(self, prompt: str, context: Optional[str] = None) -> str:
        """Generate response using Hugging Face Inference API"""
        if not self.huggingface_api_key:
            raise ValueError("Hugging Face API key not configured")
        
        try:
            final_prompt = prompt
            if context:
                final_prompt = f"{prompt}\n\nContext:\n{context}"
            # Using a code generation model
            model = "bigcode/starcoder"  # or "microsoft/CodeBERT"
            url = f"https://api-inference.huggingface.co/models/{model}"
            
            headers = {
                "Authorization": f"Bearer {self.huggingface_api_key}"
            }
            
            payload = {
                "inputs": final_prompt,
                "parameters": {
                    "max_new_tokens": 500,
                    "temperature": 0.7
                }
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return result[0].get('generated_text', '')
            return str(result)
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Hugging Face API error: {str(e)}")

    def _get_rag(self):
        if self._rag_instance is not None:
            return self._rag_instance
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        rag_path = os.path.join(repo_root, "LLM", "Rag.py")
        if not os.path.exists(rag_path):
            raise FileNotFoundError(f"LLM module not found at {rag_path}")
        spec = importlib.util.spec_from_file_location("codemaster_rag", rag_path)
        if spec is None or spec.loader is None:
            raise RuntimeError("Unable to load LLM RAG module")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self._rag_instance = module.RAG()
        return self._rag_instance

    def _generate_with_local_llm(self, prompt: str, context: Optional[str] = None) -> str:
        rag = self._get_rag()
        query = (
            "Generate Java code for this request. "
            "Prioritize reading user input from stdin using Scanner unless user asks for hardcoded values:\n"
            f"{prompt.strip()}"
        )
        if context:
            query += f"\n\nAdditional context:\n{context.strip()}"
        raw = rag.ask(query)
        code = self._sanitize_generated_code(self._extract_code_snippet(raw) or raw)
        if self._looks_like_java_code(code):
            return code
        retry = rag.ask(
            f"{query}\n\nReturn only compilable Java code. "
            f"No markdown, no Topic line, no Status line, no explanation."
        )
        retry_code = self._sanitize_generated_code(self._extract_code_snippet(retry) or retry)
        return retry_code if retry_code else code

    def _explain_with_local_llm(self, java_code: str) -> str:
        rag = self._get_rag()
        raw = rag.explain_code(java_code)
        return self._format_explanation_as_bullets(raw)
    
    def _extract_code_snippet(self, text: str) -> str:
        """Extract code block from AI response"""
        import re
        # Look for code blocks
        code_match = re.search(r'```java\n(.*?)\n```', text, re.DOTALL)
        if code_match:
            return code_match.group(1)
        
        code_match = re.search(r'```\n(.*?)\n```', text, re.DOTALL)
        if code_match:
            return code_match.group(1)
        
        return text.strip()

    def _sanitize_generated_code(self, text: str) -> str:
        import re
        if not text:
            return ""
        cleaned = text.replace("```java", "").replace("```", "").strip()
        cleaned_lines = []
        for line in cleaned.splitlines():
            stripped = line.strip()
            lowered = stripped.lower()
            if lowered.startswith("topic:"):
                continue
            if lowered.startswith("status:"):
                continue
            if lowered.startswith("here's a java solution for your request"):
                continue
            if lowered.startswith("answer:"):
                continue
            cleaned_lines.append(line)
        cleaned = "\n".join(cleaned_lines).strip()
        cleaned = re.sub(r'^\s*java\s*$', '', cleaned, flags=re.IGNORECASE | re.MULTILINE).strip()
        return cleaned

    def _looks_like_java_code(self, text: str) -> bool:
        if not text:
            return False
        markers = ["public class", "class ", "public static void main", "System.out", ";", "{", "}"]
        score = sum(1 for marker in markers if marker in text)
        return score >= 2

    def _format_explanation_as_bullets(self, text: str) -> str:
        import re
        if not text:
            return ""
        normalized = text.replace("\r\n", "\n").strip()
        if not normalized:
            return ""
        chunks = [chunk.strip() for chunk in re.split(r'(?i)(?=line\s*\d+\s*:)', normalized) if chunk.strip()]
        items = []
        if len(chunks) > 1 or re.match(r'(?i)^line\s*\d+\s*:', normalized):
            for chunk in chunks:
                cleaned = re.sub(r'(?i)^line\s*\d+\s*:\s*', '', chunk).strip()
                if cleaned:
                    items.append(cleaned)
        else:
            for line in normalized.split("\n"):
                cleaned = line.strip()
                if not cleaned:
                    continue
                cleaned = re.sub(r'^[\-\*\u2022]\s*', '', cleaned).strip()
                cleaned = re.sub(r'(?i)^line\s*\d+\s*:\s*', '', cleaned).strip()
                if cleaned:
                    items.append(cleaned)
        if not items:
            return normalized
        return "\n".join([f"- {item}" for item in items])
    
    def _extract_fix_suggestion(self, text: str) -> str:
        """Extract fix suggestion from AI response"""
        # Look for suggestions (first paragraph or bullet point)
        lines = text.split('\n')
        for line in lines:
            if line.strip() and not line.startswith('```'):
                return line.strip()[:200]
        return text[:200]
    
    def _parse_improvements(self, response: str, original_code: str) -> List[Dict]:
        """Parse improvement suggestions from AI response"""
        improvements = []
        
        # Simple parsing - extract improvements from response
        # In production, you'd want more sophisticated parsing
        lines = response.split('\n')
        current_improvement = None
        
        for line in lines:
            if 'improvement' in line.lower() or 'suggestion' in line.lower():
                if current_improvement:
                    improvements.append(current_improvement)
                current_improvement = {
                    'type': 'optimization',
                    'suggestion': line.strip(),
                    'before': original_code[:200],
                    'after': '',
                    'reason': ''
                }
        
        if current_improvement:
            improvements.append(current_improvement)
        
        # If no improvements found, return a default one
        if not improvements:
            improvements.append({
                'type': 'general',
                'suggestion': 'Review code for Java best practices',
                'before': original_code[:200],
                'after': original_code[:200],
                'reason': 'Code structure looks good. Consider adding comments and error handling.'
            })
        
        return improvements

# Singleton instance
_ai_service_instance = None

def get_ai_service() -> AIService:
    """Get singleton AI service instance"""
    global _ai_service_instance
    if _ai_service_instance is None:
        _ai_service_instance = AIService()
    return _ai_service_instance
