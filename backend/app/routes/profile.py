import os
import uuid
import time
from datetime import date, timedelta, datetime
from email.message import EmailMessage
import smtplib

from flask import Blueprint, jsonify, request, current_app
from sqlalchemy import func
from werkzeug.utils import secure_filename

from app import db
from app.middleware.auth import token_required
from app.models.user import User
from app.models.practice import PracticeAttempt, PracticeProblem, PracticeDraft
from app.models.code_submission import CodeSubmission
from app.models.assessment import Assessment
from app.models.analytics import AnalyticsEvent
from app.models.settings import UserSettings
from app.utils.validators import validate_email, validate_username, validate_password
from app.config import Config

profile_bp = Blueprint('profile', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
PASSWORD_UPDATE_LIMIT = 5
PASSWORD_UPDATE_WINDOW_SECONDS = 15 * 60
ACCOUNT_DELETE_LIMIT = 3
ACCOUNT_DELETE_WINDOW_SECONDS = 60 * 60
_password_update_attempts = {}
_account_delete_attempts = {}

def _allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def _check_rate_limit(key: str, limit: int, window_seconds: int, store: dict | None = None) -> bool:
    attempts_store = store if store is not None else _password_update_attempts
    now = time.time()
    window_start = now - window_seconds
    attempts = attempts_store.get(key, [])
    attempts = [ts for ts in attempts if ts >= window_start]
    if len(attempts) >= limit:
        attempts_store[key] = attempts
        return False
    attempts.append(now)
    attempts_store[key] = attempts
    return True

def _send_deletion_email(to_email: str, username: str) -> bool:
    if not Config.SMTP_HOST or not Config.SMTP_FROM_EMAIL:
        current_app.logger.warning('Email not configured for account deletion notifications')
        return False
    message = EmailMessage()
    message['Subject'] = 'Your CodeMaster account has been deleted'
    message['From'] = Config.SMTP_FROM_EMAIL
    message['To'] = to_email
    message.set_content(
        f"Hi {username},\n\nYour CodeMaster account and associated data have been deleted.\n\nIf this wasn't you, contact support immediately."
    )
    try:
        server = smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT, timeout=10)
        if Config.SMTP_USE_TLS:
            server.starttls()
        if Config.SMTP_USERNAME and Config.SMTP_PASSWORD:
            server.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)
        server.send_message(message)
        server.quit()
        return True
    except Exception as exc:
        current_app.logger.warning(f'Failed to send deletion email: {exc}')
        return False

def _compute_streak(user: User) -> dict:
    today = date.today()
    if not user.last_active_date:
        return {'streak_days': 0, 'active_today': False}

    active_today = user.last_active_date == today
    still_alive = user.last_active_date >= today - timedelta(days=1)

    if not still_alive:
        user.streak_days = 0
        db.session.commit()

    return {
        'streak_days': user.streak_days or 0,
        'active_today': active_today
    }

def update_streak_on_submit(user: User):
    if not user:
        return

    today = date.today()
    if user.last_active_date == today:
        return

    if user.last_active_date == today - timedelta(days=1):
        user.streak_days = (user.streak_days or 0) + 1
    else:
        user.streak_days = 1

    user.last_active_date = today
    db.session.commit()

@profile_bp.route('', methods=['GET'])
@token_required
def get_profile(current_user):
    solved_rows = (
        db.session.query(PracticeProblem.difficulty, func.count(PracticeAttempt.id))
        .join(PracticeAttempt, PracticeAttempt.problem_id == PracticeProblem.id)
        .filter(
            PracticeAttempt.user_id == current_user.id,
            PracticeAttempt.status == 'passed'
        )
        .group_by(PracticeProblem.difficulty)
        .all()
    )
    solved_map = {row[0]: row[1] for row in solved_rows}

    total_rows = (
        db.session.query(PracticeProblem.difficulty, func.count(PracticeProblem.id))
        .group_by(PracticeProblem.difficulty)
        .all()
    )
    total_map = {row[0]: row[1] for row in total_rows}

    streak = _compute_streak(current_user)

    return jsonify({
        'id': current_user.id,
        'username': current_user.username,
        'email': current_user.email,
        'profile_image_url': current_user.profile_image_url,
        'bio': current_user.bio,
        'skill_level': current_user.skill_level,
        'created_at': current_user.created_at.isoformat() if current_user.created_at else None,
        'streak_days': streak['streak_days'],
        'active_today': streak['active_today'],
        'stats': {
            'beginner': {
                'solved': solved_map.get('beginner', 0),
                'total': total_map.get('beginner', 0)
            },
            'intermediate': {
                'solved': solved_map.get('intermediate', 0),
                'total': total_map.get('intermediate', 0)
            },
            'advanced': {
                'solved': solved_map.get('advanced', 0),
                'total': total_map.get('advanced', 0)
            }
        }
    })

@profile_bp.route('', methods=['PATCH'])
@token_required
def update_profile(current_user):
    data = request.get_json(silent=True) or {}

    if 'username' in data:
        username = data.get('username', '').strip()
        valid, message = validate_username(username)
        if not valid:
            return jsonify({'error': message}), 400
        exists = User.query.filter(User.username == username, User.id != current_user.id).first()
        if exists:
            return jsonify({'error': 'Username already taken'}), 409
        current_user.username = username

    if 'email' in data:
        email = data.get('email', '').strip().lower()
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        exists = User.query.filter(User.email == email, User.id != current_user.id).first()
        if exists:
            return jsonify({'error': 'Email already in use'}), 409
        current_user.email = email

    if 'bio' in data:
        current_user.bio = data.get('bio')

    if 'skill_level' in data:
        level = str(data.get('skill_level', '')).lower()
        if level not in ('beginner', 'intermediate', 'advanced'):
            return jsonify({'error': 'Invalid skill_level'}), 400
        current_user.skill_level = level

    db.session.commit()
    return jsonify(current_user.to_dict())

@profile_bp.route('/password', methods=['POST'])
@token_required
def update_password(current_user):
    data = request.get_json(silent=True) or {}
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')
    csrf_token = request.headers.get('X-CSRF-Token', '')
    rate_key = f"{current_user.id}:{request.remote_addr or 'unknown'}"

    if not csrf_token or csrf_token != current_user.csrf_token:
        return jsonify({'error': 'Invalid CSRF token'}), 403
    if not _check_rate_limit(rate_key, PASSWORD_UPDATE_LIMIT, PASSWORD_UPDATE_WINDOW_SECONDS, _password_update_attempts):
        return jsonify({'error': 'Too many password update attempts'}), 429
    if not current_user.password_hash:
        return jsonify({'error': 'Password update not available for this account'}), 400
    if not current_password or not new_password:
        return jsonify({'error': 'Current and new password are required'}), 400
    if current_password == new_password:
        return jsonify({'error': 'New password must be different'}), 400
    if not current_user.check_password(current_password):
        return jsonify({'error': 'Current password is incorrect'}), 401

    valid, message = validate_password(new_password)
    if not valid:
        return jsonify({'error': message}), 400

    try:
        current_user.set_password(new_password)
        current_user.password_updated_at = datetime.utcnow()
        current_user.csrf_token = None
        current_user.ensure_csrf_token()
        db.session.commit()
        current_app.logger.info(f'Password updated for user {current_user.id}')
        return jsonify({'message': 'Password updated successfully', 'csrf_token': current_user.csrf_token}), 200
    except Exception as exc:
        db.session.rollback()
        current_app.logger.warning(f'Password update failed for user {current_user.id}: {exc}')
        return jsonify({'error': 'Failed to update password'}), 500

@profile_bp.route('', methods=['DELETE'])
@token_required
def delete_account(current_user):
    data = request.get_json(silent=True) or {}
    password = data.get('password', '')
    csrf_token = request.headers.get('X-CSRF-Token', '')
    rate_key = f"{current_user.id}:{request.remote_addr or 'unknown'}"

    if not csrf_token or csrf_token != current_user.csrf_token:
        return jsonify({'error': 'Invalid CSRF token'}), 403
    if not _check_rate_limit(rate_key, ACCOUNT_DELETE_LIMIT, ACCOUNT_DELETE_WINDOW_SECONDS, _account_delete_attempts):
        return jsonify({'error': 'Too many account deletion attempts'}), 429
    if not current_user.password_hash:
        return jsonify({'error': 'Password confirmation required for this account'}), 400
    if not password:
        return jsonify({'error': 'Password is required'}), 400
    if not current_user.check_password(password):
        return jsonify({'error': 'Password is incorrect'}), 401

    original_email = current_user.email
    original_username = current_user.username
    now = datetime.utcnow()
    try:
        db.session.query(CodeSubmission).filter(CodeSubmission.user_id == current_user.id).delete(synchronize_session=False)
        db.session.query(Assessment).filter(Assessment.user_id == current_user.id).delete(synchronize_session=False)
        db.session.query(AnalyticsEvent).filter(AnalyticsEvent.user_id == current_user.id).delete(synchronize_session=False)
        db.session.query(PracticeAttempt).filter(PracticeAttempt.user_id == current_user.id).delete(synchronize_session=False)
        db.session.query(PracticeDraft).filter(PracticeDraft.user_id == current_user.id).delete(synchronize_session=False)
        db.session.query(UserSettings).filter(UserSettings.user_id == current_user.id).delete(synchronize_session=False)

        current_user.deletion_requested_at = current_user.deletion_requested_at or now
        current_user.deleted_at = now
        current_user.password_hash = None
        current_user.google_id = None
        current_user.profile_image_url = None
        current_user.bio = None
        current_user.total_points = 0
        current_user.streak_days = 0
        current_user.last_active_date = None
        current_user.last_login = None
        current_user.csrf_token = None
        current_user.password_updated_at = now

        anon_suffix = uuid.uuid4().hex[:10]
        current_user.email = f"deleted-{current_user.id}-{anon_suffix}@deleted.local"
        current_user.username = f"deleted_{current_user.id}_{anon_suffix}"

        db.session.commit()
        current_app.logger.info(f'Account deleted for user {current_user.id}')
    except Exception as exc:
        db.session.rollback()
        current_app.logger.warning(f'Account deletion failed for user {current_user.id}: {exc}')
        return jsonify({'error': 'Failed to delete account'}), 500

    _send_deletion_email(original_email, original_username)
    return jsonify({'message': 'Account deleted successfully'}), 200

@profile_bp.route('/avatar', methods=['POST'])
@token_required
def upload_avatar(current_user):
    file = request.files.get('photo')
    if not file or not file.filename:
        return jsonify({'error': 'No file provided'}), 400
    if not _allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400

    filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
    upload_dir = os.path.join(current_app.root_path, 'static', 'avatars')
    os.makedirs(upload_dir, exist_ok=True)
    file.save(os.path.join(upload_dir, filename))

    current_user.profile_image_url = f'/static/avatars/{filename}'
    db.session.commit()

    return jsonify({'profile_image_url': current_user.profile_image_url})

@profile_bp.route('/submissions', methods=['GET'])
@token_required
def get_submission_history(current_user):
    limit = min(int(request.args.get('limit', 20)), 50)

    attempts = (
        PracticeAttempt.query
        .filter_by(user_id=current_user.id)
        .order_by(PracticeAttempt.submitted_at.desc())
        .limit(limit)
        .all()
    )

    return jsonify([a.to_dict() for a in attempts])
