from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from datetime import datetime, time, timedelta
import os
from models import db, Tournament, Group, Team, Match
from sqlalchemy.exc import SQLAlchemyError
import random
from collections import defaultdict

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tournament.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SHUFFLE_SEED'] = None  # For reproducible shuffling if needed

# Initialize database
db.init_app(app)

# Add custom template filters
@app.template_filter('datetime')
def format_datetime(value, format='%Y-%m-%d'):
    """Format a datetime object to a specified format"""
    if value is None:
        return ""
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            return value
    return value.strftime(format)

# Create database tables
with app.app_context():
    db.create_all()

# Context processor for templates
@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

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
        
        # Redirect to the tournament view page instead of view_groups
        return redirect(url_for('view_tournament', tournament_id=tournament.id))
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

@app.route('/tournament/<int:tournament_id>/shuffle')
def shuffle_groups(tournament_id):
    """Randomly reassign teams to groups."""
    try:
        tournament = Tournament.query.get_or_404(tournament_id)
        
        # First, collect all team data (name and ID)
        team_data = []
        for group in tournament.groups:
            for team in group.teams:
                team_data.append((team.id, team.name, group.id))
        
        # Store the original count for verification
        original_team_count = len(team_data)
        
        # Create a copy of team data for shuffling (excluding original group)
        shuffle_data = [(id, name) for id, name, _ in team_data]
        
        # Shuffle the team data
        if app.config['SHUFFLE_SEED'] is not None:
            random.seed(app.config['SHUFFLE_SEED'])
        random.shuffle(shuffle_data)
        
        # Create new teams with the same names but in different groups
        groups = list(tournament.groups)  # Convert to list to ensure stable ordering
        num_groups = len(groups)
        teams_per_group = len(shuffle_data) // num_groups
        remainder = len(shuffle_data) % num_groups
        
        # First, detach all teams from their groups to prevent cascade deletion
        # We need to create new team objects instead of moving existing ones
        # because of the cascade delete-orphan relationship
        
        # Step 1: Create new teams with the shuffled arrangement
        new_teams = []
        start_idx = 0
        
        for i, group in enumerate(groups):
            # Calculate how many teams go in this group
            group_size = teams_per_group + (1 if i < remainder else 0)
            end_idx = start_idx + group_size
            
            # Create new teams for this group
            for _, team_name in shuffle_data[start_idx:end_idx]:
                new_team = Team(name=team_name, group_id=group.id)
                new_teams.append(new_team)
                db.session.add(new_team)
            
            start_idx = end_idx
        
        # Step 2: Delete old teams after creating new ones
        for team_id, _, _ in team_data:
            old_team = Team.query.get(team_id)
            if old_team:
                db.session.delete(old_team)
        
        # Verify team count is preserved
        db.session.flush()  # Apply changes to get accurate counts
        total_teams_after = len(new_teams)
        if total_teams_after != original_team_count:
            raise ValueError(f"Team count mismatch: {original_team_count} before, {total_teams_after} after")
        
        db.session.commit()
        flash('Groups have been shuffled successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error shuffling groups: {str(e)}', 'error')
    
    return redirect(url_for('view_tournament', tournament_id=tournament_id))

def generate_round_robin_schedule(tournament_id):
    """Generate a round-robin schedule for the tournament."""
    tournament = Tournament.query.get_or_404(tournament_id)
    groups = tournament.groups
    
    # Track overall schedule across all groups
    current_date = tournament.start_date
    match_time = time(10, 0)  # Default match time
    
    for group in groups:
        teams = group.teams
        if len(teams) < 2:
            continue
            
        # Generate all possible matchups for this group
        matchups = []
        for i in range(len(teams)):
            for j in range(i + 1, len(teams)):
                matchups.append((teams[i], teams[j]))
        
        # Create matches for this group
        for home_team, away_team in matchups:
            # Create match
            match = Match(
                tournament_id=tournament.id,
                home_team_id=home_team.id,
                away_team_id=away_team.id,
                home_team_name=home_team.name,
                away_team_name=away_team.name,
                match_date=current_date,
                match_time=match_time,
                stage='group',
                group_name=group.name,  # Store group name for easier filtering
                status='scheduled'
            )
            db.session.add(match)
            
            # Move to next time slot or next day
            match_time = (datetime.combine(current_date, match_time) + 
                         timedelta(minutes=90)).time()
            
            # If we've passed 8 PM, move to next day
            if match_time.hour >= 20:
                current_date += timedelta(days=1)
                match_time = time(10, 0)
    
    db.session.commit()

@app.route('/tournament/<int:tournament_id>')
def view_tournament(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    groups_data = {}
    
    # Get all matches grouped by date and group
    matches_by_date = {}
    matches_by_group = {}
    
    for match in tournament.matches:
        # Group by date
        date_str = match.match_date.strftime('%Y-%m-%d')
        if date_str not in matches_by_date:
            matches_by_date[date_str] = []
        matches_by_date[date_str].append(match)
        
        # Group by group name
        if match.stage == 'group':
            group_name = match.group_name
            if group_name not in matches_by_group:
                matches_by_group[group_name] = []
            matches_by_group[group_name].append(match)
    
    # Sort matches by date
    sorted_dates = sorted(matches_by_date.items(), key=lambda x: x[0])
    
    # Get group standings
    for group in tournament.groups:
        teams = {team.id: {'name': team.name, 'played': 0, 'wins': 0, 'draws': 0, 'losses': 0, 'goals_for': 0, 'goals_against': 0, 'points': 0} 
                for team in group.teams}
        
        # Calculate standings
        for match in tournament.matches:
            if match.stage == 'group' and match.group_name == group.name and match.home_team_id in teams and match.away_team_id in teams:
                home_team = teams[match.home_team_id]
                away_team = teams[match.away_team_id]
                
                if match.status == 'completed' and match.home_score is not None and match.away_score is not None:
                    home_team['played'] += 1
                    away_team['played'] += 1
                    
                    home_team['goals_for'] += match.home_score
                    home_team['goals_against'] += match.away_score
                    away_team['goals_for'] += match.away_score
                    away_team['goals_against'] += match.home_score
                    
                    if match.home_score > match.away_score:
                        home_team['wins'] += 1
                        home_team['points'] += 3
                        away_team['losses'] += 1
                    elif match.home_score < match.away_score:
                        away_team['wins'] += 1
                        away_team['points'] += 3
                        home_team['losses'] += 1
                    else:
                        home_team['draws'] += 1
                        away_team['draws'] += 1
                        home_team['points'] += 1
                        away_team['points'] += 1
        
        # Sort by points, then goal difference, then goals scored
        group_teams = sorted(teams.values(), 
                           key=lambda x: (-x['points'], 
                                        -(x['goals_for'] - x['goals_against']), 
                                        -x['goals_for']))
        
        groups_data[group.name] = group_teams
    
    return render_template('view_tournament.html', 
                         tournament=tournament, 
                         matches_by_date=dict(sorted_dates),
                         matches_by_group=matches_by_group,
                         groups=groups_data)

@app.route('/match/<int:match_id>/update', methods=['POST'])
def update_match(match_id):
    match = Match.query.get_or_404(match_id)
    
    try:
        home_score = int(request.form.get('home_score', ''))
        away_score = int(request.form.get('away_score', ''))
        
        match.home_score = home_score
        match.away_score = away_score
        match.status = 'completed'
        
        db.session.commit()
        flash('Match updated successfully!', 'success')
    except (ValueError, TypeError):
        flash('Invalid score format', 'error')
    
    return redirect(url_for('view_tournament', tournament_id=match.tournament_id))

@app.route('/tournament/<int:tournament_id>/advance', methods=['POST'])
def advance_tournament(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    
    if tournament.status == 'group':
        # Move to knockout stage
        tournament.status = 'knockout'
        
        # Here you would add logic to create knockout matches
        # based on group stage results
        
        db.session.commit()
        flash('Tournament advanced to knockout stage!', 'success')
    
    return redirect(url_for('view_tournament', tournament_id=tournament_id))

if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    app.run(debug=True)
