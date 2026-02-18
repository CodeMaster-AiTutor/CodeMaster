from app.models.user import User
from app.models.code_submission import CodeSubmission
from app.models.assessment import Assessment, Question
from app.models.analytics import AnalyticsEvent
from app.models.practice import PracticeProblem, PracticeAttempt, PracticeDraft
from app.models.settings import UserSettings

__all__ = ['User', 'CodeSubmission', 'Assessment', 'Question', 'AnalyticsEvent', 'PracticeProblem', 'PracticeAttempt', 'PracticeDraft', 'UserSettings']

# Import models for Flask-Migrate to detect them
from app import db
