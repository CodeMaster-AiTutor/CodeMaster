from datetime import datetime

from app import db


class FeaturedCourse(db.Model):
    __tablename__ = "featured_courses"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(120), nullable=False, unique=True, index=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(50), nullable=True)
    kind = db.Column(db.String(30), nullable=False, default="theory")
    route_path = db.Column(db.String(255), nullable=True)
    external_url = db.Column(db.String(1024), nullable=True)
    order_index = db.Column(db.Integer, nullable=False, default=0, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "slug": self.slug,
            "title": self.title,
            "description": self.description,
            "language": self.language,
            "kind": self.kind,
            "route_path": self.route_path,
            "external_url": self.external_url,
            "order_index": self.order_index,
        }

