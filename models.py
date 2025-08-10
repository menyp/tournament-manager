from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship

db = SQLAlchemy()

class Tournament(db.Model):
    __tablename__ = 'tournaments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='group')  # group, knockout, completed
    
    # Relationships
    groups = relationship('Group', back_populates='tournament', cascade='all, delete-orphan')
    matches = relationship('Match', back_populates='tournament', cascade='all, delete-orphan')

class Group(db.Model):
    __tablename__ = 'groups'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id'), nullable=False)
    
    # Relationships
    tournament = relationship('Tournament', back_populates='groups')
    teams = relationship('Team', back_populates='group', cascade='all, delete-orphan')

class Team(db.Model):
    __tablename__ = 'teams'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    
    # Relationships
    group = relationship('Group', back_populates='teams')
    home_matches = relationship('Match', foreign_keys='Match.home_team_id', back_populates='home_team')
    away_matches = relationship('Match', foreign_keys='Match.away_team_id', back_populates='away_team')

class Match(db.Model):
    __tablename__ = 'matches'
    
    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id'), nullable=False)
    home_team_id = db.Column(db.Integer, db.ForeignKey('teams.id'))
    away_team_id = db.Column(db.Integer, db.ForeignKey('teams.id'))
    home_team_name = db.Column(db.String(100))
    away_team_name = db.Column(db.String(100))
    home_score = db.Column(db.Integer)
    away_score = db.Column(db.Integer)
    match_date = db.Column(db.Date, nullable=False)
    match_time = db.Column(db.Time, nullable=False)
    stage = db.Column(db.String(20), default='group')  # group, quarterfinal, semifinal, final
    status = db.Column(db.String(20), default='scheduled')  # scheduled, in_progress, completed
    group_name = db.Column(db.String(50))  # Store the group name for easier filtering
    
    # Relationships
    tournament = relationship('Tournament', back_populates='matches')
    home_team = relationship('Team', foreign_keys=[home_team_id], back_populates='home_matches')
    away_team = relationship('Team', foreign_keys=[away_team_id], back_populates='away_matches')
