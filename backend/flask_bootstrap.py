"""
Bootstrap script to initialize Flask app and database
Run this once to set up the database
"""
from app import create_app, db
from app.models import User, CodeSubmission, Assessment, Question, AnalyticsEvent
from sqlalchemy import inspect, text

app = create_app()

def init_db():
    """Initialize database tables"""
    with app.app_context():
        # Create all tables
        db.create_all()
        ensure_user_columns()
        ensure_user_settings_columns()
        print("✓ Database tables created successfully")
        
        admin_email = 'admin@codemaster.com'
        existing_admin = User.query.filter_by(email=admin_email).first()
        if not existing_admin:
            legacy_admin = User.query.filter_by(email='admin@CodeMaster.com').first()
            if legacy_admin:
                legacy_admin.email = admin_email
                db.session.commit()
                print("✓ Admin email normalized to lowercase (admin@codemaster.com)")
            else:
                admin = User(
                    email=admin_email,
                    username='admin',
                    skill_level='advanced',
                    total_points=0
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                print("✓ Admin user created (email: admin@codemaster.com, password: admin123)")
        
        print("\n✓ Database initialization complete!")

def ensure_user_columns():
    inspector = inspect(db.engine)
    if "users" not in inspector.get_table_names():
        return
    existing_columns = {column["name"] for column in inspector.get_columns("users")}
    column_definitions = {
        "profile_image_url": "TEXT",
        "bio": "TEXT",
        "streak_days": "INTEGER DEFAULT 0",
        "last_active_date": "DATE"
    }
    for column_name, column_type in column_definitions.items():
        if column_name in existing_columns:
            continue
        db.session.execute(text(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}"))
    db.session.commit()

def ensure_user_settings_columns():
    inspector = inspect(db.engine)
    if "user_settings" not in inspector.get_table_names():
        return
    existing_columns = {column["name"] for column in inspector.get_columns("user_settings")}
    column_definitions = {
        "editor_theme": "VARCHAR(30) DEFAULT 'vs-dark'"
    }
    for column_name, column_type in column_definitions.items():
        if column_name in existing_columns:
            continue
        db.session.execute(text(f"ALTER TABLE user_settings ADD COLUMN {column_name} {column_type}"))
    db.session.commit()

if __name__ == '__main__':
    init_db()
