import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict

# Initialize the db object here, it will be bound to the app in app.py
db = SQLAlchemy()

class ResumeAnalysis(db.Model):
    """
    Table to store resume analysis results.
    We use a JSONB column to store the full result dictionary for flexibility.
    """
    __tablename__ = 'resume_analyses'
    
    # We use the unique_id (UUID) as the primary key
    id = db.Column(db.String(36), primary_key=True)
    # The JSONB column stores the entire analysis result
    data = db.Column(JSONB)

def init_db(app):
    """Initialize the database with the Flask app."""
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    
    with app.app_context():
        db.create_all()

def save_analysis(result_data: dict):
    """Insert an analysis record."""
    analysis = ResumeAnalysis(id=result_data['id'], data=result_data)
    db.session.add(analysis)
    db.session.commit()
    return result_data['id']

def get_analysis(analysis_id: str) -> dict | None:
    """Fetch an analysis by its ID."""
    analysis = ResumeAnalysis.query.get(analysis_id)
    if analysis:
        return analysis.data
    return None

def update_suggestions(analysis_id: str, suggestions: list) -> bool:
    """Update the suggestions array inside the JSONB data."""
    analysis = ResumeAnalysis.query.get(analysis_id)
    if analysis:
        # SQLAlchemy doesn't always track changes inside a JSONB dict automatically
        # unless we re-assign it or use a MutableDict. Re-assignment is simpler here.
        new_data = dict(analysis.data)
        new_data['suggestions'] = suggestions
        analysis.data = new_data
        db.session.commit()
        return True
    return False
