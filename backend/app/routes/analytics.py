from flask import Blueprint, request, jsonify
from app import db
from app.models.code_submission import CodeSubmission
from app.models.assessment import Assessment
from app.models.analytics import AnalyticsEvent
from app.models.practice import PracticeAttempt
from app.middleware.auth import token_required
from datetime import datetime, timedelta
from sqlalchemy import func, and_

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/overview', methods=['GET'])
@token_required
def get_overview(current_user):
    """Get analytics overview for dashboard"""
    try:
        # Get code submission stats
        total_submissions = CodeSubmission.query.filter_by(user_id=current_user.id).count()
        successful_submissions = CodeSubmission.query.filter_by(
            user_id=current_user.id,
            status='success'
        ).count()
        
        success_rate = int((successful_submissions / total_submissions * 100)) if total_submissions > 0 else 0
        
        # Get average execution time
        avg_time_result = db.session.query(func.avg(CodeSubmission.execution_time))\
            .filter_by(user_id=current_user.id, status='success')\
            .scalar()
        average_time = round(avg_time_result, 2) if avg_time_result else 0
        
        # Get assessment stats
        total_assessments = Assessment.query.filter_by(user_id=current_user.id).count()
        passed_assessments = Assessment.query.filter(
            and_(
                Assessment.user_id == current_user.id,
                Assessment.score >= 80
            )
        ).count()
        
        streak = int(current_user.streak_days or 0)
        problems_solved = db.session.query(func.count(func.distinct(PracticeAttempt.problem_id))).filter(
            PracticeAttempt.user_id == current_user.id,
            PracticeAttempt.status == 'passed'
        ).scalar() or 0
        week_start_date = datetime.utcnow().date() - timedelta(days=datetime.utcnow().date().weekday())
        week_start = datetime.combine(week_start_date, datetime.min.time())
        weekly_goal = 5
        weekly_progress_count = db.session.query(func.count(func.distinct(PracticeAttempt.problem_id))).filter(
            PracticeAttempt.user_id == current_user.id,
            PracticeAttempt.status == 'passed',
            PracticeAttempt.submitted_at >= week_start
        ).scalar() or 0
        weekly_progress = min(int(weekly_progress_count), weekly_goal)
        
        return jsonify({
            'total_submissions': total_submissions,
            'successful_submissions': successful_submissions,
            'problems_solved': int(problems_solved),
            'success_rate': success_rate,
            'average_time': average_time,
            'total_assessments': total_assessments,
            'passed_assessments': passed_assessments,
            'streak': streak,
            'weekly_goal': weekly_goal,
            'weekly_progress': weekly_progress,
            'skill_level': current_user.skill_level,
            'total_points': current_user.total_points
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch analytics', 'message': str(e)}), 500

@analytics_bp.route('/progress', methods=['GET'])
@token_required
def get_progress(current_user):
    """Get skill progress breakdown"""
    try:
        # Get progress by topic/category (simplified for now)
        # In production, you'd track topics more granularly
        
        progress_data = {
            'beginner': {
                'completed': 0,
                'total': 10
            },
            'intermediate': {
                'completed': 0,
                'total': 15
            },
            'advanced': {
                'completed': 0,
                'total': 10
            }
        }
        
        # Count assessments passed at each level
        assessments = Assessment.query.filter_by(user_id=current_user.id).all()
        for assessment in assessments:
            if assessment.score >= 80:
                if assessment.level in progress_data:
                    progress_data[assessment.level]['completed'] += 1
        
        # Calculate percentages
        skills = []
        for level, data in progress_data.items():
            percentage = int((data['completed'] / data['total']) * 100) if data['total'] > 0 else 0
            skills.append({
                'skill': f'{level.capitalize()} Level',
                'completed': data['completed'],
                'total': data['total'],
                'percentage': percentage
            })
        
        return jsonify({
            'skills': skills,
            'current_level': current_user.skill_level,
            'overall_progress': _calculate_overall_progress(current_user.id)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch progress', 'message': str(e)}), 500

@analytics_bp.route('/activity', methods=['GET'])
@token_required
def get_activity(current_user):
    """Get recent activity"""
    try:
        limit = request.args.get('limit', 10, type=int)
        
        # Get recent code submissions
        recent_submissions = CodeSubmission.query\
            .filter_by(user_id=current_user.id)\
            .order_by(CodeSubmission.created_at.desc())\
            .limit(limit)\
            .all()
        
        activities = []
        for submission in recent_submissions:
            activities.append({
                'type': 'code_submission',
                'title': f'Java Code Execution',
                'status': submission.status,
                'time': submission.created_at.isoformat() if submission.created_at else None,
                'points': 5 if submission.status == 'success' else 0
            })
        
        # Get recent assessments
        recent_assessments = Assessment.query\
            .filter_by(user_id=current_user.id)\
            .order_by(Assessment.completed_at.desc())\
            .limit(5)\
            .all()
        
        for assessment in recent_assessments:
            if assessment.completed_at:
                activities.append({
                    'type': 'assessment',
                    'title': f'{assessment.level.capitalize()} Assessment',
                    'status': 'completed' if assessment.score >= 80 else 'failed',
                    'time': assessment.completed_at.isoformat(),
                    'points': assessment.score // 10
                })
        
        # Sort by time (most recent first)
        activities.sort(key=lambda x: x['time'] if x['time'] else '', reverse=True)
        
        return jsonify({
            'activities': activities[:limit]
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch activity', 'message': str(e)}), 500

@analytics_bp.route('/trends', methods=['GET'])
@token_required
def get_trends(current_user):
    """Get time-based trends (weekly/monthly)"""
    try:
        period = request.args.get('period', 'week')  # week or month
        
        if period == 'week':
            start_date = datetime.utcnow() - timedelta(days=7)
        else:
            start_date = datetime.utcnow() - timedelta(days=30)
        
        # Get submissions over time period
        submissions = CodeSubmission.query.filter(
            and_(
                CodeSubmission.user_id == current_user.id,
                CodeSubmission.created_at >= start_date
            )
        ).all()
        
        # Group by date
        daily_stats = {}
        for sub in submissions:
            date_key = sub.created_at.date().isoformat()
            if date_key not in daily_stats:
                daily_stats[date_key] = {'submissions': 0, 'successful': 0}
            daily_stats[date_key]['submissions'] += 1
            if sub.status == 'success':
                daily_stats[date_key]['successful'] += 1
        
        # Convert to list
        trends = []
        for date, stats in sorted(daily_stats.items()):
            trends.append({
                'date': date,
                'submissions': stats['submissions'],
                'successful': stats['successful'],
                'success_rate': int((stats['successful'] / stats['submissions']) * 100) if stats['submissions'] > 0 else 0
            })
        
        return jsonify({
            'period': period,
            'trends': trends
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch trends', 'message': str(e)}), 500

def _calculate_streak(user_id: int) -> int:
    """Calculate consecutive days with activity"""
    # Get all submissions and assessments
    today = datetime.utcnow().date()
    streak = 0
    
    for i in range(30):  # Check last 30 days
        check_date = today - timedelta(days=i)
        
        # Check for activity on this date
        has_submission = CodeSubmission.query.filter(
            and_(
                CodeSubmission.user_id == user_id,
                func.date(CodeSubmission.created_at) == check_date
            )
        ).first() is not None
        
        has_assessment = Assessment.query.filter(
            and_(
                Assessment.user_id == user_id,
                func.date(Assessment.completed_at) == check_date
            )
        ).first() is not None
        
        if has_submission or has_assessment:
            streak += 1
        elif i > 0:  # Break if gap found (not checking today)
            break
    
    return streak

def _calculate_overall_progress(user_id: int) -> int:
    """Calculate overall progress percentage"""
    # Simplified: based on skill level and assessments
    assessments = Assessment.query.filter_by(user_id=user_id).all()
    
    if not assessments:
        return 0
    
    total_score = sum(a.score for a in assessments)
    max_possible = len(assessments) * 100
    
    return int((total_score / max_possible) * 100) if max_possible > 0 else 0
