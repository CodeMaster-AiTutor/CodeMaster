from app import db
from datetime import datetime
import secrets
from werkzeug.security import generate_password_hash, check_password_hash
try:
    import bcrypt
except Exception:
    bcrypt = None

class User(db.Model):
    """User model for authentication and profile"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=True)  # Nullable for OAuth users
    google_id = db.Column(db.String(255), unique=True, nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    password_updated_at = db.Column(db.DateTime)
    deletion_requested_at = db.Column(db.DateTime)
    deleted_at = db.Column(db.DateTime)
    csrf_token = db.Column(db.String(128), nullable=True)
    
    # User profile
    skill_level = db.Column(db.String(20), default='beginner')  # beginner, intermediate, advanced
    total_points = db.Column(db.Integer, default=0)
    profile_image_url = db.Column(db.Text, nullable=True)
    bio = db.Column(db.Text, nullable=True)
    streak_days = db.Column(db.Integer, default=0)
    last_active_date = db.Column(db.Date, nullable=True)
    
    # Relationships
    code_submissions = db.relationship('CodeSubmission', backref='user', lazy=True, cascade='all, delete-orphan')
    assessments = db.relationship('Assessment', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        if bcrypt:
            self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')
            return
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if password is correct"""
        if not self.password_hash:
            return False
        if bcrypt:
            return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
        return check_password_hash(self.password_hash, password)

    def ensure_csrf_token(self):
        if not self.csrf_token:
            self.csrf_token = secrets.token_urlsafe(32)
        return self.csrf_token
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'skill_level': self.skill_level,
            'total_points': self.total_points,
            'profile_image_url': self.profile_image_url,
            'bio': self.bio,
            'streak_days': self.streak_days,
            'last_active_date': self.last_active_date.isoformat() if self.last_active_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
    
    def __repr__(self):
        return f'<User {self.username}>'
