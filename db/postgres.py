import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON

# Initialize the db object
db = SQLAlchemy()

class ResumeAnalysis(db.Model):
    __tablename__ = 'resume_analyses'
    id = db.Column(db.String(36), primary_key=True)
    # Use JSONB for Postgres (Production), fallback to standard JSON for SQLite (Local)
    data = db.Column(JSON().with_variant(JSONB, "postgresql"))

def init_db(app):
    """Initialize the database with the Flask app."""
    # Default to a local SQLite file if DATABASE_URL is missing or local
    db_url = os.getenv("DATABASE_URL", "sqlite:///local_resumes.db")
    
    # Fix for Render/Heroku which might use 'postgres://' instead of 'postgresql://'
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
        
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    
    with app.app_context():
        db.create_all()

def save_analysis(result_data: dict):
    analysis = ResumeAnalysis(id=result_data['id'], data=result_data)
    db.session.add(analysis)
    db.session.commit()
    return result_data['id']

def get_analysis(analysis_id: str) -> dict | None:
    analysis = ResumeAnalysis.query.get(analysis_id)
    if analysis:
        return analysis.data
    return None

def update_suggestions(analysis_id: str, suggestions: list) -> bool:
    analysis = ResumeAnalysis.query.get(analysis_id)
    if analysis:
        new_data = dict(analysis.data)
        new_data['suggestions'] = suggestions
        analysis.data = new_data
        db.session.commit()
        return True
    return False
