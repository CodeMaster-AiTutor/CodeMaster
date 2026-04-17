from flask import Blueprint, request, jsonify
from app import db
from app.models.code_submission import CodeSubmission
from app.models.assessment import Assessment
from app.models.practice import PracticeAttempt, PracticeProblem
from app.models.learning_path import LearningPathConcept
from app.models.skill_points import SkillPointTransaction
from app.middleware.auth import token_required
from app.services.skill_points_service import award_achievement_completion
from datetime import datetime, timedelta
from sqlalchemy import func

dashboard_bp = Blueprint('dashboard', __name__)


def _allowed_levels_for_user(skill_level: str):
    normalized = (skill_level or 'beginner').strip().lower()
    if normalized == 'advanced':
        return {'beginner', 'intermediate', 'advanced', 'basic'}
    if normalized == 'intermediate':
        return {'beginner', 'intermediate', 'basic'}
    return {'beginner', 'basic'}


def _level_rank(level: str) -> int:
    normalized = (level or 'beginner').strip().lower()
    if normalized == 'advanced':
        return 3
    if normalized == 'intermediate':
        return 2
    return 1

@dashboard_bp.route('/stats', methods=['GET'])
@token_required
def get_stats(current_user):
    """Get dashboard statistics for user"""
    try:
        # Total stats
        total_submissions = CodeSubmission.query.filter_by(user_id=current_user.id).count()
        total_assessments = Assessment.query.filter_by(user_id=current_user.id).count()
        
        # Success rate
        successful_submissions = CodeSubmission.query.filter_by(
            user_id=current_user.id,
            status='success'
        ).count()
        success_rate = int((successful_submissions / total_submissions * 100)) if total_submissions > 0 else 0
        problems_solved = db.session.query(func.count(func.distinct(PracticeAttempt.problem_id))).filter(
            PracticeAttempt.user_id == current_user.id,
            PracticeAttempt.status == 'passed'
        ).scalar() or 0
        
        # Weekly goal progress (solved practice problems)
        week_start_date = datetime.utcnow().date() - timedelta(days=datetime.utcnow().date().weekday())
        week_start = datetime.combine(week_start_date, datetime.min.time())
        weekly_solved = db.session.query(func.count(func.distinct(PracticeAttempt.problem_id))).filter(
            PracticeAttempt.user_id == current_user.id,
            PracticeAttempt.status == 'passed',
            PracticeAttempt.submitted_at >= week_start
        ).scalar() or 0
        weekly_goal = 5
        weekly_progress = min(int(weekly_solved), weekly_goal)
        month_start_date = datetime.utcnow().date().replace(day=1)
        month_start = datetime.combine(month_start_date, datetime.min.time())
        monthly_solved = db.session.query(func.count(func.distinct(PracticeAttempt.problem_id))).filter(
            PracticeAttempt.user_id == current_user.id,
            PracticeAttempt.status == 'passed',
            PracticeAttempt.submitted_at >= month_start
        ).scalar() or 0
        monthly_goal = 15
        monthly_progress = min(int(monthly_solved), monthly_goal)
        
        streak = int(current_user.streak_days or 0)
        levels = ['beginner', 'intermediate', 'advanced']
        current_user_level_rank = _level_rank(current_user.skill_level)
        assessment_passed = {
            level: Assessment.query.filter(
                Assessment.user_id == current_user.id,
                Assessment.level == level,
                Assessment.completed_at.isnot(None),
                Assessment.score >= 80
            ).count() > 0
            for level in levels
        }
        practice_totals = {
            level: PracticeProblem.query.filter_by(level=level).count()
            for level in levels
        }
        practice_solved_rows = (
            db.session.query(PracticeProblem.level, func.count(func.distinct(PracticeAttempt.problem_id)))
            .join(PracticeAttempt, PracticeAttempt.problem_id == PracticeProblem.id)
            .filter(
                PracticeAttempt.user_id == current_user.id,
                PracticeAttempt.status == 'passed',
                PracticeProblem.level.in_(levels)
            )
            .group_by(PracticeProblem.level)
            .all()
        )
        practice_solved_map = {row[0]: int(row[1]) for row in practice_solved_rows}
        configured_video_totals = {
            'beginner': 8,
            'intermediate': 8,
            'advanced': 11,
        }
        actual_video_totals = {
            'beginner': LearningPathConcept.query.filter(LearningPathConcept.level.in_(['beginner', 'basic'])).count(),
            'intermediate': LearningPathConcept.query.filter_by(level='intermediate').count(),
            'advanced': LearningPathConcept.query.filter_by(level='advanced').count(),
        }
        video_totals = {
            level: max(int(actual_video_totals.get(level, 0)), int(configured_video_totals[level]))
            for level in configured_video_totals
        }
        video_earned_rows = SkillPointTransaction.query.filter(
            SkillPointTransaction.user_id == current_user.id,
            SkillPointTransaction.event_type == 'video_watched'
        ).all()
        video_completed = {'beginner': set(), 'intermediate': set(), 'advanced': set()}
        for row in video_earned_rows:
            event_data = row.event_data or {}
            level = str(event_data.get('level', '')).strip().lower()
            if level == 'basic':
                level = 'beginner'
            if level in video_completed:
                video_completed[level].add(row.event_key)
        achievements = []
        rewards_awarded = []
        for level in levels:
            level_rank = _level_rank(level)
            locked = level_rank > current_user_level_rank
            reward_points = 10 if level == 'beginner' else 20 if level == 'intermediate' else 30
            level_items = [
                {
                    'key': f'{level}_assessment_passed',
                    'name': f'{level.capitalize()} Assessment Passed',
                    'description': f'Pass the {level} assessment.',
                    'earned_base': bool(assessment_passed[level]),
                    'progress': None,
                },
                {
                    'key': f'{level}_videos_completed',
                    'name': f'All {level.capitalize()} Videos Completed',
                    'description': f'Watch all {level} learning path videos.',
                    'earned_base': (video_totals[level] > 0 and len(video_completed[level]) >= video_totals[level]),
                    'progress': {
                        'completed': len(video_completed[level]),
                        'total': int(video_totals[level]),
                    },
                },
                {
                    'key': f'{level}_problems_completed',
                    'name': f'{level.capitalize()} Problems Completed',
                    'description': f'Solve all {level} practice problems.',
                    'earned_base': (practice_totals[level] > 0 and practice_solved_map.get(level, 0) >= practice_totals[level]),
                    'progress': {
                        'completed': int(practice_solved_map.get(level, 0)),
                        'total': int(practice_totals[level]),
                    },
                },
            ]
            for item in level_items:
                earned = bool(item['earned_base']) and not locked
                if earned:
                    awarded, points = award_achievement_completion(current_user, item['key'], level, item['name'])
                    if awarded:
                        rewards_awarded.append({
                            'achievement_key': item['key'],
                            'points_awarded': points,
                        })
                achievements.append({
                    'key': item['key'],
                    'name': item['name'],
                    'description': item['description'],
                    'level': level,
                    'locked': locked,
                    'earned': earned,
                    'reward_points': reward_points,
                    'progress': item['progress'],
                })
        if rewards_awarded:
            db.session.commit()
        current_level = (current_user.skill_level or 'beginner').strip().lower()
        if current_level == 'basic':
            current_level = 'beginner'
        base_query = (
            db.session.query(
                PracticeProblem.id,
                PracticeProblem.title,
                PracticeProblem.level,
                PracticeProblem.difficulty,
                func.count(PracticeAttempt.id).label('attempt_count'),
                func.count(func.distinct(PracticeAttempt.user_id)).label('participant_count')
            )
            .outerjoin(PracticeAttempt, PracticeAttempt.problem_id == PracticeProblem.id)
            .filter(PracticeProblem.level == current_level)
            .group_by(
                PracticeProblem.id,
                PracticeProblem.title,
                PracticeProblem.level,
                PracticeProblem.difficulty
            )
        )
        difficulty_buckets = [
            ('Easy', ['easy', 'basic']),
            ('Medium', ['medium', 'intermediate']),
            ('Hard', ['hard', 'advanced']),
        ]
        trending_challenges = []
        seen_ids = set()
        for label, aliases in difficulty_buckets:
            bucket_rows = (
                base_query
                .filter(func.lower(func.coalesce(PracticeProblem.difficulty, '')).in_(aliases))
                .order_by(
                    func.count(PracticeAttempt.id).desc(),
                    PracticeProblem.order_index.asc(),
                    PracticeProblem.id.asc()
                )
                .limit(2)
                .all()
            )
            for row in bucket_rows:
                row_id = int(row.id)
                if row_id in seen_ids:
                    continue
                seen_ids.add(row_id)
                trending_challenges.append({
                    'id': row_id,
                    'title': row.title,
                    'level': row.level,
                    'difficulty': label,
                    'participants': int(row.participant_count or 0),
                    'attempts': int(row.attempt_count or 0),
                    'path': f"/practice/solve/{row.level}/{row.title}",
                })
        
        return jsonify({
            'user': {
                'id': current_user.id,
                'username': current_user.username,
                'skill_level': current_user.skill_level,
                'total_points': int(current_user.total_points or 0)
            },
            'stats': {
                'total_submissions': total_submissions,
                'successful_submissions': successful_submissions,
                'problems_solved': int(problems_solved),
                'success_rate': success_rate,
                'total_assessments': total_assessments,
                'streak': streak,
                'weekly_goal': weekly_goal,
                'weekly_progress': weekly_progress,
                'monthly_goal': monthly_goal,
                'monthly_progress': monthly_progress
            },
            'achievements': achievements,
            'achievement_rewards_awarded': rewards_awarded,
            'trending_challenges': trending_challenges
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch stats', 'message': str(e)}), 500

@dashboard_bp.route('/recent', methods=['GET'])
@token_required
def get_recent(current_user):
    """Get recent activity for dashboard"""
    try:
        limit = request.args.get('limit', 5, type=int)
        limit = max(1, min(int(limit or 5), 7))
        
        allowed_levels = _allowed_levels_for_user(current_user.skill_level)
        activities = []

        latest_attempt_ids = (
            db.session.query(func.max(PracticeAttempt.id).label('latest_id'))
            .join(PracticeProblem, PracticeProblem.id == PracticeAttempt.problem_id)
            .filter(
                PracticeAttempt.user_id == current_user.id,
                PracticeProblem.level.in_(list(allowed_levels))
            )
            .group_by(PracticeAttempt.problem_id)
            .subquery()
        )
        recent_attempts = (
            db.session.query(PracticeAttempt, PracticeProblem)
            .join(PracticeProblem, PracticeProblem.id == PracticeAttempt.problem_id)
            .filter(PracticeAttempt.id.in_(db.session.query(latest_attempt_ids.c.latest_id)))
            .order_by(PracticeAttempt.submitted_at.desc())
            .limit(max(limit * 2, 10))
            .all()
        )

        for attempt, problem in recent_attempts:
            solved = attempt.status == 'passed'
            activities.append({
                'type': 'practice_problem',
                'title': problem.title if problem else f'Problem #{attempt.problem_id}',
                'status': 'solved' if solved else 'unsolved',
                'level': problem.level if problem else None,
                'time': attempt.submitted_at.isoformat() if attempt.submitted_at else None,
                'points': (5 if (problem and problem.level == 'beginner') else 10 if (problem and problem.level == 'intermediate') else 15) if solved else 0
            })

        recent_assessments = Assessment.query\
            .filter_by(user_id=current_user.id)\
            .filter(Assessment.level.in_(list(allowed_levels)))\
            .order_by(Assessment.started_at.desc())\
            .limit(max(limit, 5))\
            .all()

        for assessment in recent_assessments:
            activities.append({
                'type': 'assessment',
                'title': f'{assessment.level.capitalize()} Assessment',
                'status': 'taken' if assessment.completed_at else 'started',
                'level': assessment.level,
                'time': (assessment.completed_at.isoformat() if assessment.completed_at else (assessment.started_at.isoformat() if assessment.started_at else None)),
                'points': (assessment.score // 10) if assessment.completed_at else 0
            })

        content_events = SkillPointTransaction.query.filter(
            SkillPointTransaction.user_id == current_user.id,
            SkillPointTransaction.event_type.in_(['video_watched', 'course_opened'])
        ).order_by(SkillPointTransaction.created_at.desc()).limit(max(limit * 3, 15)).all()

        for event in content_events:
            event_data = event.event_data or {}
            level = str(event_data.get('level', '')).lower()
            normalized_level = 'beginner' if level == 'basic' else level
            if normalized_level and normalized_level not in allowed_levels:
                continue
            if event.event_type == 'video_watched':
                video_key = str(event_data.get('video_key') or event.event_key or '').replace('video:', '')
                activities.append({
                    'type': 'video',
                    'title': video_key or 'Learning video',
                    'status': 'watched',
                    'level': normalized_level or None,
                    'time': event.created_at.isoformat() if event.created_at else None,
                    'points': max(0, int(event.points_delta or 0))
                })
            elif event.event_type == 'course_opened':
                title = str(event_data.get('course_title') or event_data.get('course_key') or event.event_key or 'Course')
                activities.append({
                    'type': 'course',
                    'title': title,
                    'status': 'opened',
                    'level': normalized_level or None,
                    'time': event.created_at.isoformat() if event.created_at else None,
                    'points': 0
                })
        
        activities.sort(key=lambda x: x['time'] if x['time'] else '', reverse=True)
        
        return jsonify({
            'activities': activities[:limit]
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch recent activity', 'message': str(e)}), 500

def _calculate_streak(user_id: int) -> int:
    """Calculate consecutive days with activity"""
    from sqlalchemy import func
    today = datetime.utcnow().date()
    streak = 0
    
    for i in range(30):
        check_date = today - timedelta(days=i)
        
        has_submission = CodeSubmission.query.filter(
            CodeSubmission.user_id == user_id,
            func.date(CodeSubmission.created_at) == check_date
        ).first() is not None
        
        has_assessment = Assessment.query.filter(
            Assessment.user_id == user_id,
            func.date(Assessment.completed_at) == check_date
        ).first() is not None
        
        if has_submission or has_assessment:
            streak += 1
        elif i > 0:
            break
    
    return streak
