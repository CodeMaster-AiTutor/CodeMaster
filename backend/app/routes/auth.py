from flask import Blueprint, request, jsonify, url_for, redirect
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt
from datetime import datetime
from app import db
from app.models.user import User
from app.utils.validators import validate_email, validate_password, validate_username
from app.middleware.auth import token_required
from app.config import Config
import requests
import secrets
import string

auth_bp = Blueprint('auth', __name__)

def _password_claim(user: User) -> float:
    return user.password_updated_at.timestamp() if user.password_updated_at else 0.0

@auth_bp.route('/register', methods=['POST'])
def register():
    """User registration endpoint"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        email = data.get('email', '').strip().lower()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        # Validate email
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Validate username
        if not username:
            return jsonify({'error': 'Username is required'}), 400
        
        username_valid, username_error = validate_username(username)
        if not username_valid:
            return jsonify({'error': username_error}), 400
        
        # Validate password
        if not password:
            return jsonify({'error': 'Password is required'}), 400
        
        password_valid, password_error = validate_password(password)
        if not password_valid:
            return jsonify({'error': password_error}), 400
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already registered'}), 409
        
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already taken'}), 409
        
        # Create new user
        user = User(
            email=email,
            username=username,
            skill_level='beginner',
            total_points=0
        )
        user.set_password(password)
        user.password_updated_at = datetime.utcnow()
        user.ensure_csrf_token()
        
        db.session.add(user)
        db.session.commit()
        
        # Create tokens
        access_token = create_access_token(identity=str(user.id), additional_claims={'pwd': _password_claim(user)})
        refresh_token = create_refresh_token(identity=str(user.id))
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token,
            'csrf_token': user.csrf_token
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Registration failed', 'message': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Find user
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return jsonify({'error': 'Invalid email or password'}), 401
        if user.deleted_at:
            return jsonify({'error': 'Account deleted'}), 403
        if not user.check_password(password):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Update last login
        user.last_login = datetime.utcnow()
        user.ensure_csrf_token()
        db.session.commit()
        
        # Create tokens
        access_token = create_access_token(identity=str(user.id), additional_claims={'pwd': _password_claim(user)})
        refresh_token = create_refresh_token(identity=str(user.id))
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token,
            'csrf_token': user.csrf_token
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Login failed', 'message': str(e)}), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh JWT token endpoint"""
    try:
        current_user_id = get_jwt_identity()
        user_id = int(current_user_id) if isinstance(current_user_id, str) and current_user_id.isdigit() else current_user_id
        user = db.session.get(User, user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        if user.deleted_at:
            return jsonify({'error': 'Account deleted'}), 403
        
        # Create new access token
        access_token = create_access_token(identity=str(user.id), additional_claims={'pwd': _password_claim(user)})
        
        return jsonify({
            'access_token': access_token
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Token refresh failed', 'message': str(e)}), 500

@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    """Get current user endpoint"""
    try:
        return jsonify({
            'user': current_user.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'error': 'Failed to get user', 'message': str(e)}), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout endpoint (token blacklisting can be added here)"""
    try:
        return jsonify({'message': 'Logout successful'}), 200
    except Exception as e:
        return jsonify({'error': 'Logout failed', 'message': str(e)}), 500

@auth_bp.route('/csrf', methods=['GET'])
@token_required
def get_csrf_token(current_user):
    try:
        token = current_user.ensure_csrf_token()
        db.session.commit()
        return jsonify({'csrf_token': token}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to generate CSRF token', 'message': str(e)}), 500

@auth_bp.route('/google/url', methods=['GET'])
def google_auth_url():
    """Generate Google OAuth URL"""
    try:
        if not Config.GOOGLE_CLIENT_ID:
            return jsonify({'error': 'Google OAuth not configured'}), 500
        
        # Generate state token for CSRF protection
        state = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
        
        # Store state in session or return it to frontend
        # For simplicity, we'll return it and frontend will send it back
        
        # Google OAuth URL
        base_url = "https://accounts.google.com/o/oauth2/v2/auth"
        params = {
            'client_id': Config.GOOGLE_CLIENT_ID,
            'redirect_uri': Config.GOOGLE_REDIRECT_URI,
            'response_type': 'code',
            'scope': 'openid email profile',
            'access_type': 'offline',
            'prompt': 'consent',
            'state': state
        }
        
        auth_url = f"{base_url}?" + "&".join([f"{k}={v}" for k, v in params.items()])
        
        return jsonify({
            'auth_url': auth_url,
            'state': state
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to generate Google auth URL', 'message': str(e)}), 500

@auth_bp.route('/google/callback', methods=['POST'])
def google_callback():
    """Handle Google OAuth callback"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        code = data.get('code')
        state = data.get('state')  # Verify state for CSRF protection
        
        if not code:
            return jsonify({'error': 'Authorization code not provided'}), 400
        
        if not Config.GOOGLE_CLIENT_ID or not Config.GOOGLE_CLIENT_SECRET:
            return jsonify({'error': 'Google OAuth not configured'}), 500
        
        # Exchange code for tokens
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            'code': code,
            'client_id': Config.GOOGLE_CLIENT_ID,
            'client_secret': Config.GOOGLE_CLIENT_SECRET,
            'redirect_uri': Config.GOOGLE_REDIRECT_URI,
            'grant_type': 'authorization_code'
        }
        
        token_response = requests.post(token_url, data=token_data)
        token_response.raise_for_status()
        tokens = token_response.json()
        
        access_token = tokens.get('access_token')
        if not access_token:
            return jsonify({'error': 'Failed to get access token from Google'}), 500
        
        # Get user info from Google
        user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {'Authorization': f'Bearer {access_token}'}
        user_info_response = requests.get(user_info_url, headers=headers)
        user_info_response.raise_for_status()
        google_user = user_info_response.json()
        
        # Extract user information
        google_id = google_user.get('id')
        email = google_user.get('email', '').lower()
        name = google_user.get('name', '')
        picture = google_user.get('picture', '')
        
        if not email:
            return jsonify({'error': 'Email not provided by Google'}), 400
        
        # Check if user exists by Google ID
        user = User.query.filter_by(google_id=google_id).first()
        
        # If not found by Google ID, check by email
        if not user:
            user = User.query.filter_by(email=email).first()
        
        # Create user if doesn't exist
        if not user:
            # Generate username from email or name
            if name:
                base_username = ''.join(c if c.isalnum() or c == '_' else '_' for c in name.lower())
            else:
                base_username = email.split('@')[0]
            
            # Ensure username is unique
            username = base_username
            counter = 1
            while User.query.filter_by(username=username).first():
                username = f"{base_username}_{counter}"
                counter += 1
            
            user = User(
                email=email,
                username=username,
                google_id=google_id,
                password_hash=None,  # No password for OAuth users
                skill_level='beginner',
                total_points=0
            )
            user.ensure_csrf_token()
            db.session.add(user)
        else:
            if user.deleted_at:
                return jsonify({'error': 'Account deleted'}), 403
            # Update Google ID if not set
            if not user.google_id:
                user.google_id = google_id
            # Update last login
            user.last_login = datetime.utcnow()
            user.ensure_csrf_token()
        
        db.session.commit()
        
        # Create JWT tokens
        jwt_access_token = create_access_token(identity=user.id, additional_claims={'pwd': _password_claim(user)})
        jwt_refresh_token = create_refresh_token(identity=user.id)
        
        return jsonify({
            'message': 'Google authentication successful',
            'user': user.to_dict(),
            'access_token': jwt_access_token,
            'refresh_token': jwt_refresh_token,
            'csrf_token': user.csrf_token
        }), 200
        
    except requests.exceptions.RequestException as e:
        return jsonify({'error': 'Google OAuth request failed', 'message': str(e)}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Google authentication failed', 'message': str(e)}), 500
