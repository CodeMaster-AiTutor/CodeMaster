from datetime import datetime
from app import db


class GeneratorChat(db.Model):
    __tablename__ = "generator_chats"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False, default="New Generation Chat")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, index=True)

    messages = db.relationship(
        "GeneratorChatMessage",
        backref="chat",
        lazy=True,
        cascade="all, delete-orphan",
        order_by="GeneratorChatMessage.created_at.asc()",
    )

    def to_summary(self):
        return {
            "id": self.id,
            "title": self.title,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "message_count": len(self.messages),
        }

    def to_dict(self):
        return {
            **self.to_summary(),
            "messages": [m.to_dict() for m in self.messages],
        }


class GeneratorChatMessage(db.Model):
    __tablename__ = "generator_chat_messages"

    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey("generator_chats.id", ondelete="CASCADE"), nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False, default="")
    code = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "chat_id": self.chat_id,
            "role": self.role,
            "content": self.content,
            "code": self.code,
            "timestamp": self.created_at.isoformat() if self.created_at else None,
        }
