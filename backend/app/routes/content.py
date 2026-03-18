from flask import Blueprint, jsonify

from app.middleware.auth import token_required
from app.models.featured_course import FeaturedCourse
from app.models.learning_path import LearningPathConcept
from app.models.theory_course import TheoryCoursePage


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
    return jsonify([concept.to_detail() for concept in concepts])


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

