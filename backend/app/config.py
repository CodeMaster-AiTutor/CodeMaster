import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database - Use SQLite for development (no compilation needed on Windows)
    # For production, set DATABASE_URL environment variable to PostgreSQL connection string
    DATABASE_URL = os.getenv('DATABASE_URL', '')
    if DATABASE_URL:
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        # Default to SQLite for development (works on all platforms without compilation)
        SQLALCHEMY_DATABASE_URI = 'sqlite:///CodeMaster.db'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-change-this')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600)))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(seconds=int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 86400)))
    
    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:8080,http://127.0.0.1:8080,http://localhost:5173,http://127.0.0.1:5173').split(',')
    
    # AI Service
    AI_SERVICE = os.getenv('AI_SERVICE', 'ollama')
    OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'codellama:13b')
    HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY', '')
    
    # Java Execution
    USE_DOCKER = os.getenv('USE_DOCKER', 'true').lower() == 'true'
    DOCKER_IMAGE = os.getenv('DOCKER_IMAGE', 'codemaster-java17:local')
    JAVA_TIMEOUT = int(os.getenv('JAVA_TIMEOUT', 10))
    JAVA_MEMORY_LIMIT = os.getenv('JAVA_MEMORY_LIMIT', '128m')
    JAVA_CPU_LIMIT = float(os.getenv('JAVA_CPU_LIMIT', 0.5))
    OPENJDK_VERSION = os.getenv('OPENJDK_VERSION', '17')
    JAVAC_PATH = os.getenv('JAVAC_PATH', 'javac')
    JAVA_PATH = os.getenv('JAVA_PATH', 'java')
    MAX_CODE_LENGTH = int(os.getenv('MAX_CODE_LENGTH', 20000))
    ALERT_WEBHOOK_URL = os.getenv('ALERT_WEBHOOK_URL', '')
    TERMINAL_IDLE_TIMEOUT = int(os.getenv('TERMINAL_IDLE_TIMEOUT', 300))
    TERMINAL_MAX_RUNTIME = int(os.getenv('TERMINAL_MAX_RUNTIME', 300))
    TERMINAL_OUTPUT_LIMIT = int(os.getenv('TERMINAL_OUTPUT_LIMIT', 200000))
    TERMINAL_REQUIRE_AUTH = os.getenv('TERMINAL_REQUIRE_AUTH', 'false').lower() == 'true'
    
    # Google OAuth Configuration
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', '')
    GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:5173/auth/google/callback')

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_ECHO = False

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
