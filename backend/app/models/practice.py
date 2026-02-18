from app import db
from datetime import datetime

class PracticeProblem(db.Model):
    __tablename__ = 'practice_problems'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    difficulty = db.Column(db.String(20), nullable=False, index=True)
    tags = db.Column(db.JSON, default=list)
    starter_code = db.Column(db.Text, default='')
    constraints = db.Column(db.Text, nullable=True)
    expected_output = db.Column(db.Text, nullable=True)
    test_cases = db.Column(db.JSON, default=list)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    attempts = db.relationship('PracticeAttempt', backref='problem', lazy=True, cascade='all, delete-orphan')
    drafts = db.relationship('PracticeDraft', backref='problem', lazy=True, cascade='all, delete-orphan')

    def to_summary(self):
        return {
            'id': self.id,
            'title': self.title,
            'difficulty': self.difficulty,
            'tags': self.tags or []
        }

    def to_detail(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'difficulty': self.difficulty,
            'tags': self.tags or [],
            'starter_code': self.starter_code or '',
            'constraints': self.constraints,
            'expected_output': self.expected_output,
            'test_cases': self.test_cases or []
        }

class PracticeAttempt(db.Model):
    __tablename__ = 'practice_attempts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    problem_id = db.Column(db.Integer, db.ForeignKey('practice_problems.id', ondelete='CASCADE'), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default='started')
    last_code = db.Column(db.Text, nullable=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    score = db.Column(db.Float, nullable=True)
    time_ms = db.Column(db.Integer, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'problem_id': self.problem_id,
            'problem_title': self.problem.title if self.problem else None,
            'difficulty': self.problem.difficulty if self.problem else None,
            'status': self.status,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'score': self.score,
            'time_ms': self.time_ms
        }

class PracticeDraft(db.Model):
    __tablename__ = 'practice_drafts'
    __table_args__ = (
        db.UniqueConstraint('user_id', 'problem_id', name='uq_practice_draft_user_problem'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    problem_id = db.Column(db.Integer, db.ForeignKey('practice_problems.id', ondelete='CASCADE'), nullable=False, index=True)
    code = db.Column(db.Text, default='')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'problem_id': self.problem_id,
            'code': self.code,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
