from app.models.user import User
from app.models.code_submission import CodeSubmission
from app.models.assessment import Assessment, Question
from app.models.analytics import AnalyticsEvent
from app.models.practice import PracticeProblem, PracticeAttempt, PracticeDraft
from app.models.settings import UserSettings
from app.models.featured_course import FeaturedCourse
from app.models.learning_path import LearningPathConcept, LearningPathSubtopic
from app.models.theory_course import TheoryCoursePage
from app.models.generator_chat import GeneratorChat, GeneratorChatMessage
from app.models.skill_points import SkillPointTransaction

__all__ = [
    'User',
    'CodeSubmission',
    'Assessment',
    'Question',
    'AnalyticsEvent',
    'PracticeProblem',
    'PracticeAttempt',
    'PracticeDraft',
    'UserSettings',
    'FeaturedCourse',
    'LearningPathConcept',
    'LearningPathSubtopic',
    'TheoryCoursePage',
    'GeneratorChat',
    'GeneratorChatMessage',
    'SkillPointTransaction',
]

# Import models for Flask-Migrate to detect them
from app import db
