import os
import uuid
from datetime import date, timedelta

from flask import Blueprint, jsonify, request, current_app
from sqlalchemy import func
from werkzeug.utils import secure_filename

from app import db
from app.middleware.auth import token_required
from app.models.user import User
from app.models.practice import PracticeAttempt, PracticeProblem
from app.utils.validators import validate_email, validate_username

profile_bp = Blueprint('profile', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def _allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
