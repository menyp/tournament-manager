"""
Database initialization script for Tournament Manager.
Run this script to create a fresh database with the required schema.
"""

from app import app, db
from models import Tournament, Group, Team, Match

def init_db():
    """Initialize the database with tables and optionally sample data."""
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created successfully.")

if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Database initialization complete.")
