from datetime import datetime
from app import db


class SkillPointTransaction(db.Model):
    __tablename__ = "skill_point_transactions"
    __table_args__ = (
        db.UniqueConstraint("user_id", "event_type", "event_key", name="uq_skill_points_event"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = db.Column(db.String(64), nullable=False, index=True)
    event_key = db.Column(db.String(128), nullable=True, index=True)
    points_delta = db.Column(db.Integer, nullable=False)
    event_data = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "event_type": self.event_type,
            "event_key": self.event_key,
            "points_delta": self.points_delta,
            "event_data": self.event_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
