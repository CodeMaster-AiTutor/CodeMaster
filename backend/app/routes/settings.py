from flask import Blueprint, jsonify, request

from app import db
from app.middleware.auth import token_required
from app.models.settings import UserSettings

settings_bp = Blueprint('settings', __name__)

ALLOWED_SETTINGS = {'theme', 'editor_theme', 'font_size', 'tab_size', 'word_wrap', 'vim_mode', 'language'}

DEFAULTS = {
    'theme': 'dark',
    'editor_theme': 'vs-dark',
    'font_size': 14,
    'tab_size': 4,
    'word_wrap': False,
    'vim_mode': False,
    'language': 'java'
}

def _get_or_create_settings(user_id: int) -> UserSettings:
    settings = UserSettings.query.filter_by(user_id=user_id).first()
    if not settings:
        settings = UserSettings(user_id=user_id, **DEFAULTS)
        db.session.add(settings)
        db.session.commit()
    return settings

@settings_bp.route('', methods=['GET'])
@token_required
def get_settings(current_user):
    settings = _get_or_create_settings(current_user.id)
    return jsonify(settings.to_dict())

@settings_bp.route('', methods=['PATCH'])
@token_required
def update_settings(current_user):
    settings = _get_or_create_settings(current_user.id)
    data = request.get_json(silent=True) or {}

    unknown = set(data.keys()) - ALLOWED_SETTINGS
    if unknown:
        return jsonify({'error': f'Unknown settings: {", ".join(sorted(unknown))}'}), 400

    for key, value in data.items():
        setattr(settings, key, value)

    db.session.commit()
    return jsonify(settings.to_dict())
