import sys
import os

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))  

from app import app, db
from models import Match
from sqlalchemy import text

def migrate():
    with app.app_context():
        # Add group_name column to matches table if it doesn't exist
        try:
            db.session.execute(text('ALTER TABLE matches ADD COLUMN group_name VARCHAR(50)'))
            db.session.commit()
            print("Successfully added group_name column to matches table")
        except Exception as e:
            db.session.rollback()
            if "duplicate column name" in str(e).lower():
                print("Column group_name already exists in matches table")
            else:
                print(f"Error adding group_name column: {str(e)}")
        
        # Update existing matches with group names based on teams' groups
        try:
            matches = Match.query.filter_by(stage='group').all()
            for match in matches:
                if match.home_team and match.home_team.group:
                    match.group_name = match.home_team.group.name
            
            db.session.commit()
            print(f"Updated {len(matches)} existing matches with group names")
        except Exception as e:
            db.session.rollback()
            print(f"Error updating matches with group names: {str(e)}")

if __name__ == "__main__":
    migrate()
