"""AI Service for code generation, explanation, and error fix suggestions using local RAG model only."""
import os
import importlib.util
from typing import Dict, List, Optional

class AIService:
    """AI Service using local RAG model only"""
    
    def __init__(self):
        self.service_type = 'local_llm'
        self.error_fix_source = 'local_llm'
        self._rag_instance = None
        
    def generate_code(self, prompt: str, context: Optional[str] = None) -> str:
        """
        Generate Java code from natural language prompt
        
        Args:
            prompt: User's natural language request
            context: Optional context or previous conversation
            
        Returns:
            Generated Java code
        """
        return self._generate_with_local_llm(prompt, context)
    
    def explain_code(self, java_code: str) -> str:
        """
        Explain Java code with line-by-line analysis
        
        Args:
            java_code: Java code to explain
            
        Returns:
            Explanation text
        """
        return self._explain_with_local_llm(java_code)
    
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
        return self._suggest_error_fix_with_local_llm(
            error_message, code_context, error_type, error_line, error_column
        )

    def _suggest_error_fix_with_local_llm(
        self,
        error_message: str,
        code_context: str,
        error_type: str,
        error_line: Optional[int] = None,
        error_column: Optional[int] = None
    ) -> Dict:
        error_line_text = self._get_line_text(code_context, error_line)
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
        rag = self._get_rag()
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

    def _get_line_text(self, code_context: str, error_line: Optional[int]) -> str:
        if not code_context or not isinstance(error_line, int) or error_line <= 0:
            return ""
        lines = code_context.replace('\r\n', '\n').replace('\r', '\n').split('\n')
        if error_line > len(lines):
            return ""
        return lines[error_line - 1].strip()

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
        response = self._generate_with_local_llm(
            f"Improve this Java code ({focus}). Return practical improvements with examples:\n{java_code}"
        )
        
        # Parse improvements from response
        return self._parse_improvements(response, java_code)
    
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
        query = (
            "Generate Java code for this request. "
            "Prioritize reading user input from stdin using Scanner unless user asks for hardcoded values:\n"
            f"{prompt.strip()}"
        )
        if context:
            query += f"\n\nAdditional context:\n{context.strip()}"
        rag = self._get_rag()
        raw = rag.ask(query)
        code = self._sanitize_generated_code(self._extract_code_snippet(raw) or raw)
        if self._looks_like_java_code(code):
            return code
        retry = rag.ask(
            f"{query}\n\nReturn only compilable Java code. "
            f"No markdown, no Topic line, no Status line, no explanation."
        )
        retry_code = self._sanitize_generated_code(self._extract_code_snippet(retry) or retry)
        if retry_code:
            return retry_code
        raise RuntimeError("Local RAG model returned non-code output")

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
        raw_lines = [line.strip() for line in normalized.split("\n") if line.strip()]
        items = []
        has_explicit_line_labels = any(re.match(r'(?i)^line\s*\d+\s*:', re.sub(r'^[\-\*\u2022]\s*', '', line).strip()) for line in raw_lines)
        line_counter = 1
        for line in raw_lines:
            cleaned = re.sub(r'^[\-\*\u2022]\s*', '', line).strip()
            cleaned = cleaned.replace("```", "").strip()
            if not cleaned:
                continue
            if re.match(r'^\d+\)\s+', cleaned):
                items.append(cleaned)
                continue
            if re.match(r'(?i)^line\s*\d+\s*:', cleaned):
                items.append(cleaned)
            elif re.match(r'(?i)^(logic\s*flow|condition\s*and\s*flow|end-to-end\s*flow|program\s*goal)\s*:', cleaned):
                items.append(cleaned)
            else:
                if has_explicit_line_labels:
                    items.append(cleaned)
                else:
                    items.append(f"Line {line_counter}: {cleaned}")
                    line_counter += 1
        # If model accidentally restarts the same explanation, keep only the first block.
        duplicate_start = next(
            (
                idx for idx in range(1, len(items))
                if re.match(r'(?i)^\s*1\)\s*program\s*goal\s*:?', items[idx])
            ),
            None
        )
        if duplicate_start is not None:
            items = items[:duplicate_start]
        # Remove immediate duplicate items.
        deduped = []
        for item in items:
            if deduped and deduped[-1].strip().lower() == item.strip().lower():
                continue
            deduped.append(item)
        items = deduped
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
