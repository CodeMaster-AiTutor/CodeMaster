from datetime import datetime

from app import db


class TheoryCoursePage(db.Model):
    __tablename__ = "theory_course_pages"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(160), nullable=False, unique=True, index=True)
    title = db.Column(db.String(255), nullable=False)
    level = db.Column(db.String(20), nullable=False, index=True)
    html_path = db.Column(db.String(255), nullable=False)
    order_index = db.Column(db.Integer, nullable=False, default=0, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "slug": self.slug,
            "title": self.title,
            "level": self.level,
            "html_path": self.html_path,
            "order_index": self.order_index,
        }

