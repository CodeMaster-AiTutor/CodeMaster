from flask import Blueprint, request, jsonify
from app import db
from app.models.assessment import Assessment, Question
from app.middleware.auth import token_required
from app.services.assessment_service import get_assessment_service
from datetime import datetime
import json

assessment_bp = Blueprint('assessment', __name__)

@assessment_bp.route('/questions', methods=['GET'])
@token_required
def get_questions(current_user):
    """Get 20 assessment questions for current level"""
    try:
        level = request.args.get('level', 'beginner')  # beginner, intermediate, advanced
        
        if level not in ['beginner', 'intermediate', 'advanced']:
            return jsonify({'error': 'Invalid level. Must be beginner, intermediate, or advanced'}), 400
        
        user_level = current_user.skill_level if current_user.skill_level else level
        assessment_id = request.args.get('assessment_id', type=int)
        service = get_assessment_service()
        questions = []
        if assessment_id:
            assessment = Assessment.query.filter_by(id=assessment_id, user_id=current_user.id).first()
            if not assessment:
                return jsonify({'error': 'Assessment not found'}), 404
            ids = []
            if isinstance(assessment.answers, dict):
                ids = assessment.answers.get('_question_ids', []) or []
            if ids:
                questions = Question.query.filter(Question.id.in_(ids)).all()
        if not questions:
            questions = service.build_assessment_question_set(user_level)
        
        # Convert to dict (without correct_answer for security - only send after submission)
        questions_dict = []
        for q in questions:
            q_dict = {
                'id': q.id,
                'type': q.question_type,
                'question': q.question_text,
                'options': q.options if q.question_type in ('mcq', 'msq') else None,
                'test_cases': _extract_coding_test_cases(q) if q.question_type == 'coding' else None,
                'difficulty': q.difficulty
            }
            questions_dict.append(q_dict)
        
        return jsonify({
            'questions': questions_dict,
            'level': user_level,
            'total_questions': len(questions_dict)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch questions', 'message': str(e)}), 500

@assessment_bp.route('/start', methods=['POST'])
@token_required
def start_assessment(current_user):
    """Start a new assessment"""
    try:
        data = request.get_json()
        level = data.get('level', current_user.skill_level or 'beginner')
        if level not in ['beginner', 'intermediate', 'advanced']:
            return jsonify({'error': 'Invalid level. Must be beginner, intermediate, or advanced'}), 400
        service = get_assessment_service()
        questions = service.build_assessment_question_set(level)
        question_ids = [q.id for q in questions]
        
        # Create assessment record
        assessment = Assessment(
            user_id=current_user.id,
            level=level,
            score=0,
            total_questions=len(question_ids),
            answers={'_question_ids': question_ids},
            started_at=datetime.utcnow()
        )
        
        db.session.add(assessment)
        db.session.commit()
        
        return jsonify({
            'message': 'Assessment started',
            'assessment_id': assessment.id,
            'level': level,
            'question_ids': question_ids
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to start assessment', 'message': str(e)}), 500

@assessment_bp.route('/submit', methods=['POST'])
@token_required
def submit_assessment(current_user):
    """Submit assessment answers and calculate score"""
    try:
        data = request.get_json()
        
        assessment_id = data.get('assessment_id')
        answers = data.get('answers', {})
        
        if not assessment_id:
            return jsonify({'error': 'Assessment ID is required'}), 400
        
        # Get assessment
        assessment = Assessment.query.filter_by(
            id=assessment_id,
            user_id=current_user.id
        ).first()
        
        if not assessment:
            return jsonify({'error': 'Assessment not found'}), 404
        
        if assessment.completed_at:
            return jsonify({'error': 'Assessment already completed'}), 400
        
        service = get_assessment_service()
        question_ids = []
        if isinstance(assessment.answers, dict):
            question_ids = assessment.answers.get('_question_ids', []) or []
        if question_ids:
            loaded = Question.query.filter(Question.id.in_(question_ids)).all()
            by_id = {q.id: q for q in loaded}
            questions = [by_id[qid] for qid in question_ids if qid in by_id]
        else:
            questions = service.build_assessment_question_set(assessment.level)
        score, result_meta = service.calculate_score(questions, answers if isinstance(answers, dict) else {})
        
        # Update assessment
        assessment.answers = {
            '_question_ids': [q.id for q in questions],
            'responses': answers if isinstance(answers, dict) else {}
        }
        assessment.score = score
        assessment.completed_at = datetime.utcnow()
        
        # Add points
        current_user.total_points += score // 10
        
        db.session.commit()
        
        proposed_next_level = None
        if score >= 80:
            if assessment.level == 'beginner':
                proposed_next_level = 'intermediate'
            elif assessment.level == 'intermediate':
                proposed_next_level = 'advanced'
        can_advance = bool(
            proposed_next_level
            and current_user.skill_level == assessment.level
        )

        return jsonify({
            'message': 'Assessment submitted successfully',
            'score': score,
            'total_questions': assessment.total_questions,
            'passed': score >= 80,
            'skill_level_updated': False,
            'new_skill_level': current_user.skill_level,
            'can_advance': can_advance,
            'proposed_next_level': proposed_next_level,
            'result_meta': result_meta
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to submit assessment', 'message': str(e)}), 500

@assessment_bp.route('/results/<int:assessment_id>', methods=['GET'])
@token_required
def get_results(current_user, assessment_id):
    """Get assessment results with detailed feedback"""
    try:
        assessment = Assessment.query.filter_by(
            id=assessment_id,
            user_id=current_user.id
        ).first()
        
        if not assessment:
            return jsonify({'error': 'Assessment not found'}), 404
        
        service = get_assessment_service()
        question_ids = []
        responses = {}
        if isinstance(assessment.answers, dict):
            question_ids = assessment.answers.get('_question_ids', []) or []
            responses = assessment.answers.get('responses', {}) or {}
        if question_ids:
            loaded = Question.query.filter(Question.id.in_(question_ids)).all()
            by_id = {q.id: q for q in loaded}
            questions = [by_id[qid] for qid in question_ids if qid in by_id]
        else:
            questions = service.build_assessment_question_set(assessment.level)
        
        # Build detailed results
        results = []
        for q in questions:
            user_answer = responses.get(str(q.id), responses.get(q.id, ''))
            is_correct = service._is_correct(q, user_answer)
            
            results.append({
                'question_id': q.id,
                'question': q.question_text,
                'user_answer': user_answer,
                'correct_answer': q.correct_answer if q.question_type != 'coding' else 'Testcase validation',
                'is_correct': is_correct,
                'explanation': q.explanation
            })
        
        return jsonify({
            'assessment': assessment.to_dict(),
            'results': results,
            'score': assessment.score,
            'passed': assessment.score >= 80
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch results', 'message': str(e)}), 500

@assessment_bp.route('/coding/run-testcases', methods=['POST'])
@token_required
def run_assessment_coding_testcases(current_user):
    try:
        data = request.get_json()
        question_id = data.get('question_id')
        code = data.get('code', '')
        if not question_id or not str(code).strip():
            return jsonify({'error': 'question_id and code are required'}), 400
        question = Question.query.filter_by(id=question_id, question_type='coding').first()
        if not question:
            return jsonify({'error': 'Coding question not found'}), 404
        service = get_assessment_service()
        result = service.run_coding_test_cases(question, code)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': 'Failed to run coding testcases', 'message': str(e)}), 500

@assessment_bp.route('/accept-level-up', methods=['POST'])
@token_required
def accept_level_up(current_user):
    try:
        data = request.get_json()
        assessment_id = data.get('assessment_id')
        if not assessment_id:
            return jsonify({'error': 'Assessment ID is required'}), 400
        assessment = Assessment.query.filter_by(
            id=assessment_id,
            user_id=current_user.id
        ).first()
        if not assessment:
            return jsonify({'error': 'Assessment not found'}), 404
        if not assessment.completed_at:
            return jsonify({'error': 'Assessment is not completed'}), 400
        if assessment.score < 80:
            return jsonify({'error': 'Minimum passing score not met'}), 400
        if assessment.level == 'beginner' and current_user.skill_level == 'beginner':
            current_user.skill_level = 'intermediate'
        elif assessment.level == 'intermediate' and current_user.skill_level == 'intermediate':
            current_user.skill_level = 'advanced'
        db.session.commit()
        return jsonify({
            'message': 'Level updated successfully',
            'new_skill_level': current_user.skill_level
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update level', 'message': str(e)}), 500

def _extract_coding_test_cases(question: Question):
    try:
        payload = json.loads(question.correct_answer or '{}')
        if isinstance(payload, dict):
            cases = payload.get('test_cases', [])
            if isinstance(cases, list):
                return cases
    except Exception:
        pass
    return []
