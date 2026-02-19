"""Authentication middleware and decorators"""
from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from app import db
from app.models.user import User

def token_required(f):
    """Decorator to require JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            user_id = int(current_user_id) if isinstance(current_user_id, str) and current_user_id.isdigit() else current_user_id
            current_user = db.session.get(User, user_id)
            
            if not current_user:
                return jsonify({'error': 'User not found'}), 404
            if current_user.deleted_at:
                return jsonify({'error': 'Account deleted'}), 403

            token_data = get_jwt()
            password_marker = token_data.get('pwd') if token_data else None
            if password_marker is not None and current_user.password_updated_at:
                if float(password_marker) < current_user.password_updated_at.timestamp():
                    return jsonify({'error': 'Token expired'}), 401
            
            # Add current_user to kwargs
            kwargs['current_user'] = current_user
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({'error': 'Invalid or expired token', 'message': str(e)}), 401
    
    return decorated

def get_current_user():
    """Get current user from JWT token"""
    try:
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        resolved_id = int(user_id) if isinstance(user_id, str) and user_id.isdigit() else user_id
        return db.session.get(User, resolved_id)
    except Exception:
        return None
