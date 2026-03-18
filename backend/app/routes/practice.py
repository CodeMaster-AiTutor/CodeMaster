from flask import Blueprint, jsonify, request

from app import db
from app.middleware.auth import token_required
from app.models.practice import PracticeProblem, PracticeAttempt, PracticeDraft
from app.routes.profile import update_streak_on_submit
from app.services.java_executor import get_java_executor

practice_bp = Blueprint('practice', __name__)

LEVEL_ORDER = ['beginner', 'intermediate', 'advanced']
LEVEL_MIX = 0.0

def _problems_for_level(level: str, include_mix: bool = True):
    main_problems = (
        PracticeProblem.query.filter_by(level=level)
        .order_by(PracticeProblem.order_index.asc(), PracticeProblem.id.asc())
        .all()
    )

    if not include_mix or not main_problems:
        return main_problems

    if LEVEL_MIX <= 0:
        return main_problems

    idx = LEVEL_ORDER.index(level) if level in LEVEL_ORDER else 0
    mixed = []
    if idx + 1 < len(LEVEL_ORDER):
        next_level = LEVEL_ORDER[idx + 1]
        harder = (
            PracticeProblem.query.filter_by(level=next_level)
            .order_by(PracticeProblem.order_index.asc(), PracticeProblem.id.asc())
            .limit(max(1, int(len(main_problems) * LEVEL_MIX)))
        ).all()
        mixed.extend(harder)

    return main_problems + mixed

@practice_bp.route('/problems', methods=['GET'])
@token_required
def list_problems(current_user):
    level = request.args.get('level', '').lower() or (current_user.skill_level or 'beginner')
    if level not in LEVEL_ORDER:
        return jsonify({'error': 'Invalid level'}), 400

    tags = request.args.get('tags', '')
    problems = _problems_for_level(level, include_mix=True)

    if tags:
        tag_list = [t.strip().lower() for t in tags.split(',')]
        problems = [p for p in problems if any(t in (p.tags or []) for t in tag_list)]

    attempted_ids = {
        a.problem_id: a.status
        for a in PracticeAttempt.query.filter_by(user_id=current_user.id).all()
    }

    result = []
    for p in problems:
        summary = p.to_summary()
        summary['attempt_status'] = attempted_ids.get(p.id)
        result.append(summary)

    return jsonify(result)


@practice_bp.route('/catalog', methods=['GET'])
@token_required
def get_catalog(current_user):
    problems = PracticeProblem.query.order_by(
        PracticeProblem.level.asc(),
        PracticeProblem.section.asc(),
        PracticeProblem.order_index.asc(),
        PracticeProblem.id.asc(),
    ).all()
    attempted_ids = {
        a.problem_id: a.status
        for a in PracticeAttempt.query.filter_by(user_id=current_user.id).all()
    }
    payload = []
    for p in problems:
        item = p.to_summary()
        item['attempt_status'] = attempted_ids.get(p.id)
        payload.append(item)
    return jsonify(payload)

@practice_bp.route('/problems/<int:problem_id>', methods=['GET'])
@token_required
def get_problem(current_user, problem_id):
    problem = PracticeProblem.query.get_or_404(problem_id)

    detail = problem.to_detail()
    draft = PracticeDraft.query.filter_by(
        user_id=current_user.id, problem_id=problem_id
    ).first()
    detail['draft_code'] = draft.code if draft else problem.starter_code

    return jsonify(detail)

@practice_bp.route('/attempts', methods=['POST'])
@token_required
def create_attempt(current_user):
    data = request.get_json(silent=True) or {}

    problem_id = data.get('problem_id')
    status = data.get('status', 'started')
    last_code = data.get('last_code')
    score = data.get('score')
    time_ms = data.get('time_ms')

    if not problem_id:
        return jsonify({'error': 'problem_id is required'}), 400
    if status not in ('started', 'passed', 'failed'):
        return jsonify({'error': 'Invalid status'}), 400

    PracticeProblem.query.get_or_404(problem_id)

    attempt = PracticeAttempt(
        user_id=current_user.id,
        problem_id=problem_id,
        status=status,
        last_code=last_code,
        score=score,
        time_ms=time_ms
    )
    db.session.add(attempt)

    if status == 'passed':
        update_streak_on_submit(current_user)

    db.session.commit()
    return jsonify(attempt.to_dict()), 201

@practice_bp.route('/attempts/<int:attempt_id>', methods=['PATCH'])
@token_required
def update_attempt(current_user, attempt_id):
    attempt = PracticeAttempt.query.filter_by(id=attempt_id, user_id=current_user.id).first_or_404()
    data = request.get_json(silent=True) or {}

    for field in ('status', 'last_code', 'score', 'time_ms'):
        if field in data:
            setattr(attempt, field, data[field])

    if data.get('status') == 'passed':
        update_streak_on_submit(current_user)

    db.session.commit()
    return jsonify(attempt.to_dict())

@practice_bp.route('/attempts', methods=['GET'])
@token_required
def list_attempts(current_user):
    attempts = (
        PracticeAttempt.query
        .filter_by(user_id=current_user.id)
        .order_by(PracticeAttempt.submitted_at.desc())
        .all()
    )
    return jsonify([a.to_dict() for a in attempts])

@practice_bp.route('/drafts', methods=['GET'])
@token_required
def get_draft(current_user):
    problem_id = request.args.get('problem_id', type=int)

    if not problem_id:
        return jsonify({'error': 'problem_id is required'}), 400

    draft = PracticeDraft.query.filter_by(
        user_id=current_user.id, problem_id=problem_id
    ).first()

    if not draft:
        problem = PracticeProblem.query.get_or_404(problem_id)
        return jsonify({'problem_id': problem_id, 'code': problem.starter_code, 'updated_at': None})

    return jsonify(draft.to_dict())

@practice_bp.route('/drafts', methods=['PUT'])
@token_required
def save_draft(current_user):
    data = request.get_json(silent=True) or {}

    problem_id = data.get('problem_id')
    code = data.get('code', '')

    if not problem_id:
        return jsonify({'error': 'problem_id is required'}), 400

    PracticeProblem.query.get_or_404(problem_id)

    draft = PracticeDraft.query.filter_by(
        user_id=current_user.id, problem_id=problem_id
    ).first()

    if draft:
        draft.code = code
        draft.updated_at = db.func.now()
    else:
        draft = PracticeDraft(user_id=current_user.id, problem_id=problem_id, code=code)
        db.session.add(draft)

    db.session.commit()
    return jsonify(draft.to_dict())


@practice_bp.route('/validate', methods=['POST'])
@token_required
def validate_solution(current_user):
    data = request.get_json(silent=True) or {}
    problem_id = data.get('problem_id')
    code = data.get('code', '')

    if not problem_id:
        return jsonify({'error': 'problem_id is required'}), 400
    if not code or not isinstance(code, str):
        return jsonify({'error': 'code is required'}), 400

    problem = PracticeProblem.query.get_or_404(problem_id)
    test_cases = problem.test_cases or []
    if not isinstance(test_cases, list) or len(test_cases) == 0:
        return jsonify({'error': 'No test cases configured for this problem'}), 400

    executor = get_java_executor()
    results = []
    passed_count = 0
    for idx, test_case in enumerate(test_cases, start=1):
        case_input = str((test_case or {}).get('input', ''))
        expected_output = str((test_case or {}).get('output', '')).strip()
        run = executor.compile_and_execute(code, input_data=case_input)
        actual_output = str(run.get('output', '')).strip()
        success = bool(run.get('success')) and actual_output == expected_output
        if success:
            passed_count += 1
        results.append({
            'index': idx,
            'input': case_input,
            'expected_output': expected_output,
            'actual_output': actual_output,
            'success': success,
            'errors': run.get('errors', []),
        })

    solved = passed_count == len(test_cases)
    return jsonify({
        'problem_id': problem.id,
        'title': problem.title,
        'solved': solved,
        'passed': passed_count,
        'total': len(test_cases),
        'results': results,
    })
