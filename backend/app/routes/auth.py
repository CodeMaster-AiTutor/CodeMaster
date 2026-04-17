from flask import Blueprint, request, jsonify, Response, current_app
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, timedelta
from app import db
from app.models.user import User
from app.utils.validators import validate_email, validate_password, validate_username
from app.middleware.auth import token_required
from app.config import Config
from app.services.skill_points_service import apply_daily_login_streak
import requests
import secrets
import string
import hashlib
import smtplib
from email.message import EmailMessage
from urllib.parse import quote

auth_bp = Blueprint('auth', __name__)

def _password_claim(user: User) -> float:
    return user.password_updated_at.timestamp() if user.password_updated_at else 0.0


def _hash_verification_token(token: str) -> str:
    return hashlib.sha256((token or '').encode('utf-8')).hexdigest()


def _build_verification_link(email: str, token: str) -> str:
    return f"{Config.BACKEND_PUBLIC_BASE_URL}/api/auth/verify-email-link?email={quote(email)}&token={quote(token)}"


def _build_frontend_login_link(email: str) -> str:
    return f"{Config.FRONTEND_BASE_URL}/login?email={quote(email)}&verified=1"


def _hash_otp(value: str) -> str:
    return hashlib.sha256((value or '').encode('utf-8')).hexdigest()


def _generate_otp() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def _send_reset_password_otp_email(email: str, username: str, otp: str):
    if not Config.SMTP_HOST:
        raise RuntimeError('Email service is not configured')
    sender = Config.SMTP_FROM_EMAIL or Config.SMTP_USERNAME
    if not sender:
        raise RuntimeError('Sender email is not configured')
    message = EmailMessage()
    message['Subject'] = 'CodeMaster password reset OTP'
    message['From'] = sender
    message['To'] = email
    message.set_content(
        f"Hi {username},\n\n"
        f"Your CodeMaster password reset OTP is: {otp}\n\n"
        "This OTP expires in 10 minutes.\n\n"
        "If you did not request a password reset, you can ignore this email."
    )
    server = smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT, timeout=15)
    password = (Config.SMTP_PASSWORD or '').replace(' ', '')
    try:
        server.ehlo()
        if Config.SMTP_USE_TLS:
            server.starttls()
            server.ehlo()
        if Config.SMTP_USERNAME and password:
            server.login(Config.SMTP_USERNAME, password)
        server.send_message(message)
    finally:
        server.quit()


def _send_verification_email(email: str, username: str, verify_link: str):
    if not Config.SMTP_HOST:
        raise RuntimeError('Email service is not configured')
    sender = Config.SMTP_FROM_EMAIL or Config.SMTP_USERNAME
    if not sender:
        raise RuntimeError('Sender email is not configured')
    message = EmailMessage()
    message['Subject'] = 'Verify your CodeMaster account'
    message['From'] = sender
    message['To'] = email
    message.set_content(
        f"Hi {username},\n\n"
        f"Please verify your email by clicking this link:\n{verify_link}\n\n"
        "This link expires in 10 minutes.\n\n"
        "If you did not sign up for CodeMaster, you can ignore this email."
    )
    server = smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT, timeout=10)
    password = (Config.SMTP_PASSWORD or '').replace(' ', '')
    try:
        server.ehlo()
        if Config.SMTP_USE_TLS:
            server.starttls()
            server.ehlo()
        if Config.SMTP_USERNAME and password:
            server.login(Config.SMTP_USERNAME, password)
        server.send_message(message)
    finally:
        server.quit()


def _issue_email_verification(user: User):
    verification_token = secrets.token_urlsafe(48)
    user.email_verified = False
    user.email_verification_token_hash = _hash_verification_token(verification_token)
    user.email_verification_expires_at = datetime.utcnow() + timedelta(minutes=10)
    verify_link = _build_verification_link(user.email, verification_token)
    return verification_token, verify_link


def _verify_email_for_user(email: str, token: str):
    user = User.query.filter_by(email=email).first()
    if not user:
        return None, 'Invalid verification link'
    if bool(user.email_verified):
        return user, None
    if not user.email_verification_token_hash or not user.email_verification_expires_at:
        return None, 'Invalid verification link'
    if user.email_verification_expires_at < datetime.utcnow():
        return None, 'Verification link has expired'
    if user.email_verification_token_hash != _hash_verification_token(token):
        return None, 'Invalid verification link'
    user.email_verified = True
    user.email_verification_token_hash = None
    user.email_verification_expires_at = None
    db.session.commit()
    return user, None


def _build_unique_username(seed_value: str) -> str:
    seed = ''.join(c if c.isalnum() or c == '_' else '_' for c in (seed_value or '').lower()).strip('_')
    base_username = seed or f'user_{secrets.randbelow(100000)}'
    username = base_username
    counter = 1
    while User.query.filter_by(username=username).first():
        username = f"{base_username}_{counter}"
        counter += 1
    return username

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
        skill_level = str(data.get('skill_level', 'beginner')).strip().lower()
        
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
        
        if skill_level not in ('beginner', 'intermediate', 'advanced'):
            return jsonify({'error': 'Invalid skill_level'}), 400

        # Check if user already exists
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already registered'}), 409
        
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already taken'}), 409
        
        user = User(
            email=email,
            username=username,
            skill_level=skill_level,
            total_points=50,
            email_verified=False
        )
        user.set_password(password)
        user.password_updated_at = datetime.utcnow()
        user.ensure_csrf_token()
        _, verify_link = _issue_email_verification(user)

        db.session.add(user)
        db.session.commit()
        delivery_failed = False
        try:
            _send_verification_email(email, username, verify_link)
        except Exception:
            delivery_failed = True
        
        return jsonify({
            'message': 'Registration successful. Verification email sent.' if not delivery_failed else 'Registration successful, but email delivery failed. Please use resend verification.',
            'verification_required': True,
            'email': user.email,
            'expires_in_seconds': 600,
            'email_delivery_failed': delivery_failed
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
        if not bool(user.email_verified):
            return jsonify({'error': 'Please verify your email before logging in'}), 403
        if not user.check_password(password):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Update last login
        user.last_login = datetime.utcnow()
        apply_daily_login_streak(user, user.last_login)
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
        if not bool(user.email_verified):
            return jsonify({'error': 'Please verify your email before logging in'}), 403
        
        # Create new access token
        access_token = create_access_token(identity=str(user.id), additional_claims={'pwd': _password_claim(user)})
        
        return jsonify({
            'access_token': access_token
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Token refresh failed', 'message': str(e)}), 500


@auth_bp.route('/verify-email', methods=['POST'])
def verify_email():
    try:
        data = request.get_json(silent=True) or {}
        email = str(data.get('email', '')).strip().lower()
        token = str(data.get('token', '')).strip()
        if not email or not token:
            return jsonify({'error': 'Email and token are required'}), 400
        user, error_message = _verify_email_for_user(email, token)
        if error_message:
            return jsonify({'error': error_message}), 400
        return jsonify({
            'message': 'Email verified successfully',
            'verified': True,
            'email': user.email,
            'redirect_url': _build_frontend_login_link(user.email)
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Email verification failed', 'message': str(e)}), 500


@auth_bp.route('/verify-email-link', methods=['GET'])
def verify_email_link():
    email = str(request.args.get('email', '')).strip().lower()
    token = str(request.args.get('token', '')).strip()
    if not email or not token:
        return Response('<html><body><h2>Invalid verification link.</h2></body></html>', status=400, mimetype='text/html')
    try:
        user, error_message = _verify_email_for_user(email, token)
        if error_message:
            return Response(f'<html><body><h2>{error_message}</h2></body></html>', status=400, mimetype='text/html')
        login_link = _build_frontend_login_link(user.email)
        html = (
            '<html><head><meta charset="utf-8"></head>'
            '<body style="font-family: Arial, sans-serif; padding: 24px;">'
            '<h2>Email verified successfully.</h2>'
            '<p>Your account is verified. Redirecting to login...</p>'
            f'<p><a id="login-link" href="{login_link}">Continue to Login</a></p>'
            '<p id="status" style="color:#555;">Redirecting...</p>'
            '<script>'
            f'setTimeout(function() {{ window.location.href = "{login_link}"; }}, 450);'
            '</script>'
            '</body></html>'
        )
        return Response(html, status=200, mimetype='text/html')
    except Exception:
        db.session.rollback()
        return Response('<html><body><h2>Email verification failed.</h2></body></html>', status=500, mimetype='text/html')


@auth_bp.route('/resend-verification', methods=['POST'])
def resend_verification():
    try:
        data = request.get_json(silent=True) or {}
        email = str(data.get('email', '')).strip().lower()
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'error': 'Account not found'}), 404
        if bool(user.email_verified):
            return jsonify({'error': 'Email is already verified'}), 400
        _, verify_link = _issue_email_verification(user)
        db.session.commit()
        try:
            _send_verification_email(user.email, user.username, verify_link)
        except Exception:
            return jsonify({'error': 'Unable to send verification email right now. Please try again.'}), 503
        return jsonify({
            'message': 'Verification email sent',
            'verification_required': True,
            'email': user.email,
            'expires_in_seconds': 600
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to resend verification email', 'message': str(e)}), 500


@auth_bp.route('/forgot-password/request-otp', methods=['POST'])
def request_password_reset_otp():
    try:
        data = request.get_json(silent=True) or {}
        email = str(data.get('email', '')).strip().lower()
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        user = User.query.filter_by(email=email).first()
        if not user or user.deleted_at or not user.password_hash or not bool(user.email_verified):
            return jsonify({'message': 'If this email exists, OTP has been sent.'}), 200
        otp = _generate_otp()
        user.reset_password_otp_hash = _hash_otp(otp)
        user.reset_password_otp_expires_at = datetime.utcnow() + timedelta(minutes=10)
        db.session.commit()
        try:
            _send_reset_password_otp_email(user.email, user.username, otp)
            return jsonify({'message': 'OTP sent successfully', 'expires_in_seconds': 600}), 200
        except Exception as smtp_error:
            current_app.logger.exception('Failed to send reset OTP email')
            if bool(current_app.config.get('DEBUG', False)):
                return jsonify({
                    'message': 'OTP generated but email delivery failed. Use this OTP for local testing.',
                    'expires_in_seconds': 600,
                    'delivery_failed': True,
                    'dev_otp': otp,
                    'reason': str(smtp_error)
                }), 200
            return jsonify({'error': 'Failed to send OTP. Email service is unavailable or not configured.'}), 503
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to send OTP. Email service is unavailable or not configured.'}), 503


@auth_bp.route('/forgot-password/reset', methods=['POST'])
def reset_password_with_otp():
    try:
        data = request.get_json(silent=True) or {}
        email = str(data.get('email', '')).strip().lower()
        otp = str(data.get('otp', '')).strip()
        new_password = str(data.get('new_password', '')).strip()
        if not email or not otp or not new_password:
            return jsonify({'error': 'Email, OTP and new password are required'}), 400
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        user = User.query.filter_by(email=email).first()
        if not user or user.deleted_at:
            return jsonify({'error': 'Invalid OTP or email'}), 400
        if not user.reset_password_otp_hash or not user.reset_password_otp_expires_at:
            return jsonify({'error': 'OTP is not requested or expired'}), 400
        if user.reset_password_otp_expires_at < datetime.utcnow():
            return jsonify({'error': 'OTP has expired'}), 400
        if user.reset_password_otp_hash != _hash_otp(otp):
            return jsonify({'error': 'Invalid OTP'}), 400
        if user.check_password(new_password):
            return jsonify({'error': 'Please use a different password from your current password'}), 400
        valid, message = validate_password(new_password)
        if not valid:
            return jsonify({'error': message}), 400
        user.set_password(new_password)
        user.password_updated_at = datetime.utcnow()
        user.reset_password_otp_hash = None
        user.reset_password_otp_expires_at = None
        db.session.commit()
        return jsonify({'message': 'Password changed successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to reset password', 'message': str(e)}), 500

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
        is_new_user = False
        user = User.query.filter_by(google_id=google_id).first()
        
        # If not found by Google ID, check by email
        if not user:
            user = User.query.filter_by(email=email).first()
        
        # Create user if doesn't exist
        if not user:
            is_new_user = True
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
                total_points=50,
                email_verified=True,
                email_verification_token_hash=None,
                email_verification_expires_at=None
            )
            user.last_login = datetime.utcnow()
            apply_daily_login_streak(user, user.last_login)
            user.ensure_csrf_token()
            db.session.add(user)
        else:
            if user.deleted_at:
                return jsonify({'error': 'Account deleted'}), 403
            # Update Google ID if not set
            if not user.google_id:
                user.google_id = google_id
            user.email_verified = True
            user.email_verification_token_hash = None
            user.email_verification_expires_at = None
            # Update last login
            user.last_login = datetime.utcnow()
            apply_daily_login_streak(user, user.last_login)
            user.ensure_csrf_token()
        
        db.session.commit()
        
        # Create JWT tokens
        jwt_access_token = create_access_token(identity=str(user.id), additional_claims={'pwd': _password_claim(user)})
        jwt_refresh_token = create_refresh_token(identity=str(user.id))
        
        return jsonify({
            'message': 'Google authentication successful',
            'user': user.to_dict(),
            'access_token': jwt_access_token,
            'refresh_token': jwt_refresh_token,
            'csrf_token': user.csrf_token,
            'is_new_user': is_new_user
        }), 200
        
    except requests.exceptions.RequestException as e:
        return jsonify({'error': 'Google OAuth request failed', 'message': str(e)}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Google authentication failed', 'message': str(e)}), 500


@auth_bp.route('/github/url', methods=['GET'])
def github_auth_url():
    try:
        if not Config.GITHUB_CLIENT_ID:
            return jsonify({'error': 'GitHub OAuth not configured'}), 500
        state = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
        params = {
            'client_id': Config.GITHUB_CLIENT_ID,
            'redirect_uri': Config.GITHUB_REDIRECT_URI,
            'scope': 'read:user user:email',
            'state': state
        }
        auth_url = "https://github.com/login/oauth/authorize?" + "&".join([f"{k}={quote(str(v))}" for k, v in params.items()])
        return jsonify({'auth_url': auth_url, 'state': state}), 200
    except Exception as e:
        return jsonify({'error': 'Failed to generate GitHub auth URL', 'message': str(e)}), 500


@auth_bp.route('/github/callback', methods=['POST'])
def github_callback():
    try:
        data = request.get_json(silent=True) or {}
        code = str(data.get('code', '')).strip()
        if not code:
            return jsonify({'error': 'Authorization code not provided'}), 400
        if not Config.GITHUB_CLIENT_ID or not Config.GITHUB_CLIENT_SECRET:
            return jsonify({'error': 'GitHub OAuth not configured'}), 500
        token_response = requests.post(
            "https://github.com/login/oauth/access_token",
            data={
                'client_id': Config.GITHUB_CLIENT_ID,
                'client_secret': Config.GITHUB_CLIENT_SECRET,
                'code': code,
                'redirect_uri': Config.GITHUB_REDIRECT_URI
            },
            headers={'Accept': 'application/json'},
            timeout=20
        )
        token_response.raise_for_status()
        access_token = (token_response.json() or {}).get('access_token')
        if not access_token:
            return jsonify({'error': 'Failed to get access token from GitHub'}), 500
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/vnd.github+json',
            'User-Agent': 'CodeMaster-App'
        }
        user_response = requests.get("https://api.github.com/user", headers=headers, timeout=20)
        user_response.raise_for_status()
        github_user = user_response.json() or {}
        github_id = str(github_user.get('id', '')).strip()
        github_login = str(github_user.get('login', '')).strip()
        email = str(github_user.get('email', '')).strip().lower()
        if not email:
            emails_response = requests.get("https://api.github.com/user/emails", headers=headers, timeout=20)
            emails_response.raise_for_status()
            emails_payload = emails_response.json() or []
            primary_verified = next((item for item in emails_payload if item.get('primary') and item.get('verified')), None)
            any_verified = next((item for item in emails_payload if item.get('verified')), None)
            selected = primary_verified or any_verified
            email = str((selected or {}).get('email', '')).strip().lower()
        if not github_id:
            return jsonify({'error': 'GitHub account id not provided'}), 400
        if not email:
            return jsonify({'error': 'Email not provided by GitHub account'}), 400
        is_new_user = False
        user = User.query.filter_by(github_id=github_id).first()
        if not user:
            user = User.query.filter_by(email=email).first()
        if not user:
            is_new_user = True
            username_seed = github_login or email.split('@')[0]
            user = User(
                email=email,
                username=_build_unique_username(username_seed),
                github_id=github_id,
                password_hash=None,
                skill_level='beginner',
                total_points=50,
                email_verified=True,
                email_verification_token_hash=None,
                email_verification_expires_at=None
            )
            user.last_login = datetime.utcnow()
            apply_daily_login_streak(user, user.last_login)
            user.ensure_csrf_token()
            db.session.add(user)
        else:
            if user.deleted_at:
                return jsonify({'error': 'Account deleted'}), 403
            if not user.github_id:
                user.github_id = github_id
            user.email_verified = True
            user.email_verification_token_hash = None
            user.email_verification_expires_at = None
            user.last_login = datetime.utcnow()
            apply_daily_login_streak(user, user.last_login)
            user.ensure_csrf_token()
        db.session.commit()
        jwt_access_token = create_access_token(identity=str(user.id), additional_claims={'pwd': _password_claim(user)})
        jwt_refresh_token = create_refresh_token(identity=str(user.id))
        return jsonify({
            'message': 'GitHub authentication successful',
            'user': user.to_dict(),
            'access_token': jwt_access_token,
            'refresh_token': jwt_refresh_token,
            'csrf_token': user.csrf_token,
            'is_new_user': is_new_user
        }), 200
    except requests.exceptions.RequestException as e:
        return jsonify({'error': 'GitHub OAuth request failed', 'message': str(e)}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'GitHub authentication failed', 'message': str(e)}), 500
