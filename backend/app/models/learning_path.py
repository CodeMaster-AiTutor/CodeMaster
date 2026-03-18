from datetime import datetime

from app import db


class LearningPathConcept(db.Model):
    __tablename__ = "learning_path_concepts"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(160), nullable=False, unique=True, index=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    level = db.Column(db.String(20), nullable=False, index=True)
    tutorial_url = db.Column(db.String(1024), nullable=True)
    order_index = db.Column(db.Integer, nullable=False, default=0, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    subtopics = db.relationship(
        "LearningPathSubtopic",
        backref="concept",
        lazy=True,
        cascade="all, delete-orphan",
        order_by="LearningPathSubtopic.order_index.asc()",
    )

    def to_summary(self):
        return {
            "id": self.id,
            "slug": self.slug,
            "title": self.title,
            "description": self.description,
            "level": self.level,
            "tutorial_url": self.tutorial_url,
            "order_index": self.order_index,
            "subtopics": [s.title for s in (self.subtopics or [])],
        }

    def to_detail(self):
        return self.to_summary()


class LearningPathSubtopic(db.Model):
    __tablename__ = "learning_path_subtopics"

    id = db.Column(db.Integer, primary_key=True)
    concept_id = db.Column(
        db.Integer, db.ForeignKey("learning_path_concepts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title = db.Column(db.String(255), nullable=False)
    order_index = db.Column(db.Integer, nullable=False, default=0, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

