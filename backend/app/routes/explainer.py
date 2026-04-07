from flask import Blueprint, request, jsonify
from app.middleware.auth import token_required
from app.services.ai_service import get_ai_service
from app.services.llm_proxy import call_llm_service, use_external_llm_service

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
