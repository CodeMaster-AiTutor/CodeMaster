from flask import Blueprint, request, jsonify
from app import db
from app.middleware.auth import token_required
from app.models.generator_chat import GeneratorChat, GeneratorChatMessage
from app.services.ai_service import get_ai_service
from app.services.skill_points_service import consume_generation_points, GENERATION_COST
import re

generator_bp = Blueprint('generator', __name__)


def _build_chat_title(prompt: str):
    normalized = " ".join((prompt or "").strip().split())
    if not normalized:
        return "New Generation Chat"
    trimmed = normalized[:80]
    if trimmed.lower().startswith("write "):
        trimmed = trimmed[6:]
    if trimmed.lower().startswith("generate "):
        trimmed = trimmed[9:]
    return trimmed[:1].upper() + trimmed[1:] if trimmed else "New Generation Chat"


def _get_user_chat(user_id: int, chat_id):
    if not chat_id:
        return None
    return GeneratorChat.query.filter_by(id=chat_id, user_id=user_id).first()


def _build_context_from_chat(chat: GeneratorChat):
    if not chat:
        return None
    recent = chat.messages[-8:]
    if not recent:
        return None
    return "\n".join([f"{m.role}: {m.content}" for m in recent])


def _is_non_java_language_request(text: str) -> bool:
    prompt = (text or "").lower()
    if not prompt:
        return False
    non_java_languages = [
        "python", "javascript", "typescript", "c++", "c#", "golang", "go language",
        "rust", "php", "ruby", "swift", "kotlin", "scala", "r language", "matlab",
        "perl", "dart"
    ]
    if any(lang in prompt for lang in non_java_languages):
        return True
    in_lang = re.search(r"\bin\s+([a-z+#]+)\b", prompt)
    if in_lang:
        requested = in_lang.group(1)
        if requested not in ("java",):
            return True
    return False

@generator_bp.route('/generate', methods=['POST'])
@token_required
def generate_code(current_user):
    """AI code generation endpoint"""
    try:
        data = request.get_json(silent=True) or {}
        
        prompt = data.get('prompt', '').strip()
        context = data.get('context', None)
        chat_id = data.get('chat_id')
        
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400
        if _is_non_java_language_request(prompt):
            return jsonify({'error': 'Only Java Language Supported. '}), 400
        if int(current_user.total_points or 0) < GENERATION_COST:
            return jsonify({'error': f'Insufficient skill points. {GENERATION_COST} points required per generation.'}), 402

        chat = _get_user_chat(current_user.id, chat_id)
        if chat is None:
            chat = GeneratorChat(
                user_id=current_user.id,
                title=_build_chat_title(prompt),
            )
            db.session.add(chat)
            db.session.flush()

        merged_context = context

        db.session.add(GeneratorChatMessage(
            chat_id=chat.id,
            role='user',
            content=prompt,
            code=None,
        ))
        
        # Generate code using AI service
        ai_service = get_ai_service()
        generated_code = ai_service.generate_code(prompt, merged_context)
        spent_ok, spent_error, remaining_points = consume_generation_points(current_user, prompt)
        if not spent_ok:
            return jsonify({'error': spent_error}), 402

        db.session.add(GeneratorChatMessage(
            chat_id=chat.id,
            role='assistant',
            content=generated_code,
            code=generated_code,
        ))
        db.session.commit()
        
        return jsonify({
            'message': 'Code generated successfully',
            'code': generated_code,
            'prompt': prompt,
            'chat_id': chat.id,
            'chat_title': chat.title,
            'points_spent': GENERATION_COST,
            'remaining_points': int(current_user.total_points or remaining_points),
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Code generation failed', 'message': str(e)}), 500

@generator_bp.route('/chat', methods=['POST'])
@token_required
def chat(current_user):
    """Chat-based code generation endpoint"""
    try:
        data = request.get_json(silent=True) or {}
        
        message = data.get('message', '').strip()
        history = data.get('history', [])
        chat_id = data.get('chat_id')
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        if _is_non_java_language_request(message):
            return jsonify({'error': 'Only Java Language Supported. '}), 400
        if int(current_user.total_points or 0) < GENERATION_COST:
            return jsonify({'error': f'Insufficient skill points. {GENERATION_COST} points required per generation.'}), 402

        chat = _get_user_chat(current_user.id, chat_id)
        if chat is None:
            chat = GeneratorChat(
                user_id=current_user.id,
                title=_build_chat_title(message),
            )
            db.session.add(chat)
            db.session.flush()

        context = None

        db.session.add(GeneratorChatMessage(
            chat_id=chat.id,
            role='user',
            content=message,
            code=None,
        ))
        
        # Generate response
        ai_service = get_ai_service()
        response = ai_service.generate_code(message, context)
        spent_ok, spent_error, remaining_points = consume_generation_points(current_user, message)
        if not spent_ok:
            return jsonify({'error': spent_error}), 402

        db.session.add(GeneratorChatMessage(
            chat_id=chat.id,
            role='assistant',
            content=response,
            code=response,
        ))
        db.session.commit()
        
        return jsonify({
            'message': response,
            'role': 'assistant',
            'chat_id': chat.id,
            'chat_title': chat.title,
            'points_spent': GENERATION_COST,
            'remaining_points': int(current_user.total_points or remaining_points),
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Chat failed', 'message': str(e)}), 500


@generator_bp.route('/history', methods=['POST'])
@token_required
def create_chat(current_user):
    data = request.get_json(silent=True) or {}
    title = (data.get('title') or '').strip()
    if not title:
        title = "New Generation Chat"
    chat = GeneratorChat(user_id=current_user.id, title=title[:255])
    db.session.add(chat)
    db.session.commit()
    return jsonify({
        'message': 'Chat created',
        'chat': chat.to_dict(),
    }), 201

@generator_bp.route('/history', methods=['GET'])
@token_required
def get_history(current_user):
    """Get generation history endpoint"""
    chats = (
        GeneratorChat.query
        .filter_by(user_id=current_user.id)
        .order_by(GeneratorChat.updated_at.desc(), GeneratorChat.id.desc())
        .all()
    )
    return jsonify({
        'message': 'History fetched successfully',
        'history': [c.to_summary() for c in chats]
    }), 200


@generator_bp.route('/history/<int:chat_id>', methods=['GET'])
@token_required
def get_chat(current_user, chat_id: int):
    chat = GeneratorChat.query.filter_by(id=chat_id, user_id=current_user.id).first()
    if not chat:
        return jsonify({'error': 'Chat not found'}), 404
    return jsonify({
        'message': 'Chat fetched successfully',
        'chat': chat.to_dict(),
    }), 200


@generator_bp.route('/history/<int:chat_id>', methods=['PATCH', 'PUT'])
@token_required
def rename_chat(current_user, chat_id: int):
    chat = GeneratorChat.query.filter_by(id=chat_id, user_id=current_user.id).first()
    if not chat:
        return jsonify({'error': 'Chat not found'}), 404
    data = request.get_json(silent=True) or {}
    title = " ".join(str(data.get('title', '')).strip().split())
    if not title:
        return jsonify({'error': 'title is required'}), 400
    chat.title = title[:255]
    db.session.commit()
    return jsonify({
        'message': 'Chat renamed successfully',
        'chat': chat.to_dict(),
    }), 200


@generator_bp.route('/history/<int:chat_id>', methods=['DELETE'])
@token_required
def delete_chat(current_user, chat_id: int):
    chat = GeneratorChat.query.filter_by(id=chat_id, user_id=current_user.id).first()
    if not chat:
        return jsonify({'error': 'Chat not found'}), 404
    db.session.delete(chat)
    db.session.commit()
    return jsonify({'message': 'Chat deleted successfully'}), 200
