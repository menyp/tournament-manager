from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
import os
from models import db, Tournament, Group, Team

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tournament.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

# Create database tables
with app.app_context():
    db.create_all()

# Routes
@app.route('/')
def home():
    tournaments = Tournament.query.all()
    return render_template('index.html', tournaments=tournaments)

@app.route('/tournament/new', methods=['GET'])
def new_tournament():
    return render_template('new_tournament.html')

@app.route('/tournament/create', methods=['POST'])
def create_tournament():
    try:
        tournament = Tournament(
            name=request.form['name'],
            start_date=datetime.strptime(request.form['start_date'], '%Y-%m-%d').date(),
            end_date=datetime.strptime(request.form['end_date'], '%Y-%m-%d').date(),
            status='group'
        )
        db.session.add(tournament)
        
        # Get all teams and number of groups
        all_teams = [name.strip() for name in request.form['all_teams'].split('\n') if name.strip()]
        num_groups = int(request.form.get('num_groups', 1))
        
        if len(all_teams) < num_groups:
            flash('You need at least as many teams as groups', 'error')
            return redirect(url_for('new_tournament'))
        
        # Distribute teams evenly across groups
        teams_per_group = len(all_teams) // num_groups
        remainder = len(all_teams) % num_groups
        
        start_idx = 0
        for i in range(num_groups):
            group_name = f'Group {chr(65+i)}'
            group = Group(name=group_name, tournament=tournament)
            db.session.add(group)
            
            # Calculate how many teams go in this group
            # Add an extra team to earlier groups if teams don't divide evenly
            group_size = teams_per_group + (1 if i < remainder else 0)
            end_idx = start_idx + group_size
            
            # Get teams for this group
            group_teams = all_teams[start_idx:end_idx]
            for name in group_teams:
                team = Team(name=name, group=group)
                db.session.add(team)
            
            start_idx = end_idx
        
        db.session.commit()
        
        # Redirect to a page that shows the groups and teams
        return redirect(url_for('view_groups', tournament_id=tournament.id))
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating tournament: {str(e)}', 'error')
        return redirect(url_for('new_tournament'))

@app.route('/tournament/<int:tournament_id>/groups')
def view_groups(tournament_id):
    """View the groups and teams for a tournament."""
    tournament = Tournament.query.get_or_404(tournament_id)
    groups = tournament.groups
    
    return render_template('view_groups.html', tournament=tournament, groups=groups)

@app.route('/tournament/<int:tournament_id>')
def view_tournament(tournament_id):
    """View tournament details."""
    tournament = Tournament.query.get_or_404(tournament_id)
    return render_template('view_tournament.html', tournament=tournament)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5004)
