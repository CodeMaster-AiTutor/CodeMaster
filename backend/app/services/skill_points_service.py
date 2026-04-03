from datetime import date, datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy import func
from app import db
from app.models.skill_points import SkillPointTransaction

PRACTICE_POINTS = {
    "beginner": 5,
    "intermediate": 10,
    "advanced": 15,
}

VIDEO_POINTS = {
    "beginner": 10,
    "intermediate": 15,
    "advanced": 20,
}

GENERATION_COST = 5
WEEKLY_GOAL_TARGET = 5
WEEKLY_GOAL_REWARD = 10


def _normalize_level(level: Optional[str]) -> str:
    normalized = (level or "beginner").strip().lower()
    if normalized == "basic":
        return "beginner"
    if normalized not in ("beginner", "intermediate", "advanced"):
        return "beginner"
    return normalized


def _apply_points(user, points_delta: int, event_type: str, event_key: Optional[str], event_data: Optional[dict] = None):
    user.total_points = max(0, int(user.total_points or 0) + int(points_delta))
    db.session.add(SkillPointTransaction(
        user_id=user.id,
        event_type=event_type,
        event_key=event_key,
        points_delta=int(points_delta),
        event_data=event_data or {},
    ))


def _award_one_time(user, event_type: str, event_key: str, points: int, event_data: Optional[dict] = None) -> Tuple[bool, int]:
    existing = SkillPointTransaction.query.filter_by(
        user_id=user.id,
        event_type=event_type,
        event_key=event_key,
    ).first()
    if existing:
        return False, 0
    _apply_points(user, points, event_type, event_key, event_data)
    return True, points


def apply_daily_login_streak(user, now: Optional[datetime] = None):
    now = now or datetime.utcnow()
    today = now.date()
    yesterday = today - timedelta(days=1)
    previous_active = user.last_active_date

    if previous_active == today:
        return {"streak_days": int(user.streak_days or 0), "bonus_points": 0, "updated": False}

    if previous_active == yesterday:
        user.streak_days = int(user.streak_days or 0) + 1
    elif previous_active is None:
        user.streak_days = 1
    else:
        user.streak_days = 1

    user.last_active_date = today
    bonus_points = 0
    streak_days = int(user.streak_days or 0)
    if streak_days > 0 and streak_days % 5 == 0:
        milestone = streak_days // 5
        bonus_points = 20 + ((milestone - 1) * 10)
        _apply_points(
            user,
            bonus_points,
            "login_streak_bonus",
            f"{today.isoformat()}:{streak_days}",
            {"streak_days": streak_days}
        )
    return {"streak_days": streak_days, "bonus_points": bonus_points, "updated": True}


def award_practice_problem_points(user, problem_id: int, level: str) -> Tuple[bool, int]:
    normalized = _normalize_level(level)
    points = PRACTICE_POINTS.get(normalized, PRACTICE_POINTS["beginner"])
    return _award_one_time(
        user,
        "practice_problem_solved",
        f"problem:{problem_id}",
        points,
        {"problem_id": problem_id, "level": normalized}
    )


def award_video_points(user, video_key: str, level: str) -> Tuple[bool, int]:
    normalized = _normalize_level(level)
    points = VIDEO_POINTS.get(normalized, VIDEO_POINTS["beginner"])
    return _award_one_time(
        user,
        "video_watched",
        f"video:{video_key}",
        points,
        {"video_key": video_key, "level": normalized}
    )


def get_video_points(level: str) -> int:
    return VIDEO_POINTS.get(_normalize_level(level), VIDEO_POINTS["beginner"])


def get_practice_points(level: str) -> int:
    return PRACTICE_POINTS.get(_normalize_level(level), PRACTICE_POINTS["beginner"])


def consume_generation_points(user, prompt: str) -> Tuple[bool, str, int]:
    current_points = int(user.total_points or 0)
    if current_points < GENERATION_COST:
        return False, "Insufficient skill points for code generation", current_points
    _apply_points(
        user,
        -GENERATION_COST,
        "generator_request_cost",
        None,
        {"prompt_preview": (prompt or "")[:120]}
    )
    return True, "", max(0, current_points - GENERATION_COST)


def award_weekly_goal_completion(user, now: Optional[datetime] = None) -> Tuple[bool, int, int]:
    from app.models.practice import PracticeAttempt

    now = now or datetime.utcnow()
    week_start_date = now.date() - timedelta(days=now.date().weekday())
    week_start_dt = datetime.combine(week_start_date, datetime.min.time())
    solved_count = db.session.query(func.count(func.distinct(PracticeAttempt.problem_id))).filter(
        PracticeAttempt.user_id == user.id,
        PracticeAttempt.status == 'passed',
        PracticeAttempt.submitted_at >= week_start_dt
    ).scalar() or 0

    solved_count = int(solved_count)
    if solved_count < WEEKLY_GOAL_TARGET:
        return False, 0, solved_count

    awarded, points = _award_one_time(
        user,
        "weekly_goal_bonus",
        f"week:{week_start_date.isoformat()}",
        WEEKLY_GOAL_REWARD,
        {"goal": WEEKLY_GOAL_TARGET, "solved": solved_count}
    )
    return awarded, points if awarded else 0, solved_count
