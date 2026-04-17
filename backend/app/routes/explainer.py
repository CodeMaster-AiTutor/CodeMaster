from flask import Blueprint, request, jsonify
from app.middleware.auth import token_required
from app.services.ai_service import get_ai_service
from app.services.llm_proxy import call_llm_service, use_external_llm_service
from app.services.java_executor import get_java_executor

explainer_bp = Blueprint('explainer', __name__)

@explainer_bp.route('/explain', methods=['POST'])
@token_required
def explain_code(current_user):
    """Code explanation endpoint with Java-specific analysis"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        java_code = data.get('code', '').strip()
        
        if not java_code:
            return jsonify({'error': 'Java code is required'}), 400

        # Strict pre-validation: only explain syntactically correct Java code.
        # Compile-only validation keeps strictness while avoiding runtime latency/timeouts.
        executor = get_java_executor()
        validation_result = executor.compile_only(java_code)
        compilation_errors = [
            err for err in (validation_result.get('errors') or [])
            if str(err.get('type', '')).strip().lower() == 'compilation_error'
        ]
        if compilation_errors:
            first_error = str(compilation_errors[0].get('message', '')).strip()
            explanation = (
                "Please enter corrected Java code for explanation. "
                "Your current code has compilation errors."
            )
            if first_error:
                explanation += f"\n\nFirst compiler error: {first_error}"
            explanation += (
                "\n\nTip: Use the Error Explainer feature in the Compiler section "
                "to get line-by-line fix guidance, then come back for code explanation."
            )
            return jsonify({
                'message': 'Code validation failed',
                'explanation': explanation,
                'code': java_code
            }), 200
        
        if use_external_llm_service():
            explanation = str(call_llm_service("/explain", {"code": java_code}).get("explanation", "")).strip()
        else:
            ai_service = get_ai_service()
            explanation = ai_service.explain_code(java_code)
        
        return jsonify({
            'message': 'Explanation generated successfully',
            'explanation': explanation,
            'code': java_code
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Explanation failed', 'message': str(e)}), 500

@explainer_bp.route('/history', methods=['GET'])
@token_required
def get_history(current_user):
    """Get explanation history endpoint"""
    # TODO: Implement history storage and retrieval
    return jsonify({
        'message': 'History endpoint - to be implemented',
        'history': []
    }), 200
