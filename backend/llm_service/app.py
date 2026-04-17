import os
import sys
import threading
from flask import Flask, jsonify, request

_SERVICE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app"))
if _SERVICE_ROOT not in sys.path:
    sys.path.insert(0, _SERVICE_ROOT)

from services.ai_service import get_ai_service

_llm_lock = threading.Lock()


def _get_internal_service_key() -> str:
    return os.getenv("LLM_SERVICE_INTERNAL_KEY", "")


def _is_authorized() -> bool:
    expected = _get_internal_service_key()
    if not expected:
        return True
    provided = request.headers.get("X-LLM-Service-Key", "")
    return provided == expected


def create_app() -> Flask:
    app = Flask(__name__)

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "healthy", "service": "CodeMaster LLM Service"}), 200

    @app.before_request
    def authorize_internal_calls():
        if request.path == "/health":
            return None
        if not _is_authorized():
            return jsonify({"error": "Unauthorized"}), 401
        return None

    @app.route("/generate", methods=["POST"])
    def generate():
        data = request.get_json(silent=True) or {}
        prompt = str(data.get("prompt", "")).strip()
        context = data.get("context")
        if not prompt:
            return jsonify({"error": "Prompt is required"}), 400
        ai_service = get_ai_service()
        with _llm_lock:
            code = ai_service.generate_code(prompt, context)
        return jsonify({"code": code}), 200

    @app.route("/explain", methods=["POST"])
    def explain():
        data = request.get_json(silent=True) or {}
        java_code = str(data.get("code", "")).strip()
        if not java_code:
            return jsonify({"error": "Java code is required"}), 400
        ai_service = get_ai_service()
        with _llm_lock:
            explanation = ai_service.explain_code(java_code)
        return jsonify({"explanation": explanation}), 200

    @app.route("/suggest-fix", methods=["POST"])
    def suggest_fix():
        data = request.get_json(silent=True) or {}
        error_message = str(data.get("error", "")).strip()
        code_context = str(data.get("code_context", "")).strip()
        error_type = str(data.get("error_type", "compilation_error")).strip() or "compilation_error"
        error_line = data.get("error_line")
        error_column = data.get("error_column")
        if not error_message or not code_context:
            return jsonify({"error": "Error message and code context are required"}), 400
        ai_service = get_ai_service()
        with _llm_lock:
            suggestion = ai_service.suggest_error_fix(
                error_message,
                code_context,
                error_type,
                error_line=error_line if isinstance(error_line, int) else None,
                error_column=error_column if isinstance(error_column, int) else None,
            )
        return jsonify(suggestion), 200

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("LLM_SERVICE_PORT", "5002"))
    host = os.getenv("LLM_SERVICE_HOST", "0.0.0.0")
    debug = os.getenv("LLM_SERVICE_DEBUG", "0").strip() in {"1", "true", "True"}
    app.run(host=host, port=port, debug=debug, use_reloader=False, threaded=True)
