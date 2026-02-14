from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_sock import Sock
from app.config import config
import os
import logging
from logging.handlers import RotatingFileHandler

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()
sock = Sock()

def create_app(config_name=None):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration
    config_name = config_name or os.getenv('FLASK_ENV', 'development')
    app.config.from_object(config[config_name])

    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    try:
        os.makedirs(log_dir, exist_ok=True)
    except Exception:
        log_dir = None
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    app.logger.setLevel(getattr(logging, log_level, logging.INFO))
    if log_dir and not app.testing:
        log_path = os.path.join(log_dir, 'backend.log')
        handler = RotatingFileHandler(log_path, maxBytes=2_000_000, backupCount=3)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')
        handler.setFormatter(formatter)
        if not any(isinstance(h, RotatingFileHandler) for h in app.logger.handlers):
            app.logger.addHandler(handler)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, origins=app.config['CORS_ORIGINS'])
    sock.init_app(app)
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.generator import generator_bp
    from app.routes.explainer import explainer_bp
    from app.routes.compiler import compiler_bp
    from app.routes.assessment import assessment_bp
    from app.routes.analytics import analytics_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes import terminal_ws
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(generator_bp, url_prefix='/api/generator')
    app.register_blueprint(explainer_bp, url_prefix='/api/explainer')
    app.register_blueprint(compiler_bp, url_prefix='/api/compiler')
    app.register_blueprint(assessment_bp, url_prefix='/api/assessment')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'error': 'Internal server error'}, 500
    
    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        return {'status': 'healthy', 'service': 'CodeMaster Backend'}
    
    return app
