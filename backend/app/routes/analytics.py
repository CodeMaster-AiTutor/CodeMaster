from flask import Blueprint, request, jsonify
from app import db
from app.models.code_submission import CodeSubmission
from app.models.assessment import Assessment
from app.models.analytics import AnalyticsEvent
from app.models.practice import PracticeAttempt
from app.models.skill_points import SkillPointTransaction
from app.middleware.auth import token_required
from datetime import datetime, timedelta
from sqlalchemy import func, and_
from app.services.skill_points_service import apply_daily_login_streak

analytics_bp = Blueprint('analytics', __name__)


def _sum_time_spent_seconds(user_id: int) -> int:
    rows = AnalyticsEvent.query.filter_by(user_id=user_id, event_type='web_time_spent').all()
    total = 0
    for row in rows:
        payload = row.event_data or {}
        value = payload.get('seconds', 0)
        try:
            total += max(0, int(value))
        except Exception:
            total += 0
    return int(total)

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
        
        total_time_spent_seconds = _sum_time_spent_seconds(current_user.id)
        
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
        month_start_date = datetime.utcnow().date().replace(day=1)
        month_start = datetime.combine(month_start_date, datetime.min.time())
        monthly_goal = 15
        monthly_progress_count = db.session.query(func.count(func.distinct(PracticeAttempt.problem_id))).filter(
            PracticeAttempt.user_id == current_user.id,
            PracticeAttempt.status == 'passed',
            PracticeAttempt.submitted_at >= month_start
        ).scalar() or 0
        monthly_progress = min(int(monthly_progress_count), monthly_goal)
        
        return jsonify({
            'total_submissions': total_submissions,
            'successful_submissions': successful_submissions,
            'problems_solved': int(problems_solved),
            'success_rate': success_rate,
            'total_time_spent_seconds': int(total_time_spent_seconds),
            'total_assessments': total_assessments,
            'passed_assessments': passed_assessments,
            'streak': streak,
            'weekly_goal': weekly_goal,
            'weekly_progress': weekly_progress,
            'monthly_goal': monthly_goal,
            'monthly_progress': monthly_progress,
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
        source_labels = {
            'practice_problem_solved': 'Practice Problems',
            'video_watched': 'Videos Watched',
            'assessment_passed': 'Assessments',
            'achievement_bonus': 'Achievements',
            'weekly_goal_bonus': 'Weekly Goal Bonus',
            'monthly_goal_bonus': 'Monthly Goal Bonus',
            'login_streak_bonus': 'Login Streak Bonus',
            'generator_request_cost': 'Code Generation Used',
            'course_opened': 'Course Opened',
        }
        tx_rows = SkillPointTransaction.query.filter_by(user_id=current_user.id).all()
        by_source = {}
        total_earned_points = 0
        total_used_points = 0
        for tx in tx_rows:
            key = tx.event_type or 'other'
            bucket = by_source.setdefault(key, {'earned_points': 0, 'used_points': 0, 'events': 0})
            delta = int(tx.points_delta or 0)
            if delta >= 0:
                bucket['earned_points'] += delta
                total_earned_points += delta
            else:
                spent = abs(delta)
                bucket['used_points'] += spent
                total_used_points += spent
            bucket['events'] += 1
        source_order = [
            'practice_problem_solved',
            'video_watched',
            'assessment_passed',
            'achievement_bonus',
            'weekly_goal_bonus',
            'monthly_goal_bonus',
            'login_streak_bonus',
            'generator_request_cost',
            'course_opened',
        ]
        point_sources = []
        for key in source_order:
            if key not in by_source:
                continue
            item = by_source[key]
            point_sources.append({
                'event_type': key,
                'source': source_labels.get(key, key.replace('_', ' ').title()),
                'earned_points': int(item['earned_points']),
                'used_points': int(item['used_points']),
                'net_points': int(item['earned_points'] - item['used_points']),
                'events': int(item['events']),
            })
        for key, item in by_source.items():
            if key in source_order:
                continue
            point_sources.append({
                'event_type': key,
                'source': source_labels.get(key, key.replace('_', ' ').title()),
                'earned_points': int(item['earned_points']),
                'used_points': int(item['used_points']),
                'net_points': int(item['earned_points'] - item['used_points']),
                'events': int(item['events']),
            })
        point_history_rows = SkillPointTransaction.query.filter_by(user_id=current_user.id).order_by(
            SkillPointTransaction.created_at.desc(),
            SkillPointTransaction.id.desc()
        ).limit(120).all()
        point_history = []
        for row in point_history_rows:
            delta = int(row.points_delta or 0)
            point_history.append({
                'id': int(row.id),
                'event_type': row.event_type,
                'source': source_labels.get(row.event_type or '', (row.event_type or 'other').replace('_', ' ').title()),
                'points_delta': delta,
                'event_key': row.event_key,
                'time': row.created_at.isoformat() if row.created_at else None,
            })
        
        return jsonify({
            'skills': skills,
            'current_level': current_user.skill_level,
            'overall_progress': _calculate_overall_progress(current_user.id),
            'point_sources': point_sources,
            'point_history': point_history,
            'total_earned_points': int(total_earned_points),
            'total_used_points': int(total_used_points),
            'net_points': int(total_earned_points - total_used_points),
            'current_points': int(current_user.total_points or 0),
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


@analytics_bp.route('/time-spent', methods=['POST'])
@token_required
def track_time_spent(current_user):
    try:
        data = request.get_json(silent=True) or {}
        seconds = int(data.get('seconds', 0) or 0)
        if seconds <= 0:
            return jsonify({'tracked': False, 'seconds': 0}), 200
        if seconds > 300:
            seconds = 300
        db.session.add(AnalyticsEvent(
            user_id=current_user.id,
            event_type='web_time_spent',
            event_data={'seconds': seconds}
        ))
        apply_daily_login_streak(current_user, datetime.utcnow())
        db.session.commit()
        return jsonify({'tracked': True, 'seconds': seconds}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to track time spent', 'message': str(e)}), 500

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
