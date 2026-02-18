from app import db
from datetime import datetime

class UserSettings(db.Model):
    __tablename__ = 'user_settings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)
    theme = db.Column(db.String(20), default='dark')
    editor_theme = db.Column(db.String(30), default='vs-dark')
    font_size = db.Column(db.Integer, default=14)
    tab_size = db.Column(db.Integer, default=4)
    word_wrap = db.Column(db.Boolean, default=False)
    vim_mode = db.Column(db.Boolean, default=False)
    language = db.Column(db.String(20), default='java')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'theme': self.theme,
            'editor_theme': self.editor_theme,
            'font_size': self.font_size,
            'tab_size': self.tab_size,
            'word_wrap': self.word_wrap,
            'vim_mode': self.vim_mode,
            'language': self.language,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
