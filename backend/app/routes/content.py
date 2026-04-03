from flask import Blueprint, jsonify, request

from app import db
from app.middleware.auth import token_required
from app.models.featured_course import FeaturedCourse
from app.models.learning_path import LearningPathConcept
from app.models.skill_points import SkillPointTransaction
from app.models.theory_course import TheoryCoursePage
from app.services.skill_points_service import award_video_points, get_video_points


content_bp = Blueprint("content", __name__)


@content_bp.route("/featured-courses", methods=["GET"])
@token_required
def get_featured_courses(current_user):
    courses = (
        FeaturedCourse.query.order_by(FeaturedCourse.order_index.asc(), FeaturedCourse.id.asc()).all()
    )
    return jsonify([course.to_dict() for course in courses])


@content_bp.route("/learning-paths", methods=["GET"])
@token_required
def get_learning_paths(current_user):
    concepts = (
        LearningPathConcept.query.order_by(
            LearningPathConcept.level.asc(),
            LearningPathConcept.order_index.asc(),
            LearningPathConcept.id.asc(),
        ).all()
    )
    earned_keys = {
        row.event_key
        for row in SkillPointTransaction.query.filter_by(
            user_id=current_user.id,
            event_type='video_watched'
        ).all()
    }
    payload = []
    for concept in concepts:
        item = concept.to_detail()
        level = str(item.get('level', 'beginner')).lower()
        normalized_level = 'beginner' if level == 'basic' else level
        item['earnable_points'] = get_video_points(normalized_level)
        item['points_earned'] = f"video:{item.get('id')}" in earned_keys
        payload.append(item)
    return jsonify(payload)


@content_bp.route("/theory-pages", methods=["GET"])
@token_required
def get_theory_pages(current_user):
    pages = (
        TheoryCoursePage.query.order_by(
            TheoryCoursePage.level.asc(),
            TheoryCoursePage.order_index.asc(),
            TheoryCoursePage.id.asc(),
        ).all()
    )
    return jsonify([page.to_dict() for page in pages])


@content_bp.route("/videos/complete", methods=["POST"])
@token_required
def complete_video(current_user):
    data = request.get_json(silent=True) or {}
    video_key = str(data.get("video_key", "")).strip()
    level = str(data.get("level", "beginner")).strip().lower()
    if not video_key:
        return jsonify({"error": "video_key is required"}), 400
    normalized_level = "beginner" if level == "basic" else level
    awarded, points = award_video_points(current_user, video_key, normalized_level)
    db.session.commit()
    return jsonify({
        "awarded": awarded,
        "points_awarded": points if awarded else 0,
        "current_points": int(current_user.total_points or 0),
        "earnable_points": get_video_points(normalized_level),
    }), 200
