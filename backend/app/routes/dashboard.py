from flask import Blueprint, request, jsonify
from app import db
from app.models.code_submission import CodeSubmission
from app.models.assessment import Assessment
from app.models.practice import PracticeAttempt
from app.middleware.auth import token_required
from datetime import datetime, timedelta
from sqlalchemy import func

dashboard_bp = Blueprint('dashboard', __name__)

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
        
        streak = int(current_user.streak_days or 0)
        
        return jsonify({
            'user': {
                'id': current_user.id,
                'username': current_user.username,
                'skill_level': current_user.skill_level,
                'total_points': current_user.total_points
            },
            'stats': {
                'total_submissions': total_submissions,
                'successful_submissions': successful_submissions,
                'problems_solved': int(problems_solved),
                'success_rate': success_rate,
                'total_assessments': total_assessments,
                'streak': streak,
                'weekly_goal': weekly_goal,
                'weekly_progress': weekly_progress
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch stats', 'message': str(e)}), 500

@dashboard_bp.route('/recent', methods=['GET'])
@token_required
def get_recent(current_user):
    """Get recent activity for dashboard"""
    try:
        limit = request.args.get('limit', 5, type=int)
        
        # Get recent submissions
        recent_submissions = CodeSubmission.query\
            .filter_by(user_id=current_user.id)\
            .order_by(CodeSubmission.created_at.desc())\
            .limit(limit)\
            .all()
        
        activities = []
        for sub in recent_submissions:
            activities.append({
                'type': 'code_submission',
                'title': 'Java Code Execution',
                'status': sub.status,
                'time': sub.created_at.isoformat() if sub.created_at else None,
                'points': 5 if sub.status == 'success' else 0
            })
        
        # Get recent assessments
        recent_assessments = Assessment.query\
            .filter_by(user_id=current_user.id)\
            .filter(Assessment.completed_at.isnot(None))\
            .order_by(Assessment.completed_at.desc())\
            .limit(3)\
            .all()
        
        for assessment in recent_assessments:
            activities.append({
                'type': 'assessment',
                'title': f'{assessment.level.capitalize()} Assessment',
                'status': 'completed' if assessment.score >= 80 else 'failed',
                'time': assessment.completed_at.isoformat() if assessment.completed_at else None,
                'points': assessment.score // 10
            })
        
        # Sort by time
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
