"""For this iteration I'm conflating the definition of our applications database with the Flask-Migrate abstractions
to manage it. I'd like to do something cleaner, once I have a better understanding of what's going on with flake

Check out this structure:
https://stackoverflow.com/questions/56230626/why-is-sqlalchemy-database-uri-set-to-sqlite-memory-when-i-set-it-to-a-pa
"""

from enum import Enum

from backend.database.db import db


class Users(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    email = db.Column(db.Text)
    profile_pic = db.Column(db.Text)
    username = db.Column(db.Text)
    created_at = db.Column(db.DATETIME)


class GameModes(Enum):
    return_weighted = "Return-weighted"
    consolation_prize = "Consolation prize"
    winner_takes_all = "Winner takes all"


class Benchmarks(Enum):
    return_ratio = "Simple return"
    sharpe_ratio = "Sharpe ratio-adjusted"


class SideBetPeriods(Enum):
    weekly = "Weekly"
    monthly = "Monthly"


class Games(db.Model):
    __tablename__ = "games"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text)
    mode = db.Column(db.Enum(GameModes))
    duration = db.Column(db.Integer)
    buy_in = db.Column(db.Float)
    n_rebuys = db.Column(db.Integer)
    benchmark = db.Column(db.Enum(Benchmarks))
    side_bets_perc = db.Column(db.Float)  # Will a we split off a weekly side pot?
    side_bets_period = db.Column(db.Enum(SideBetPeriods))


class StatusTypes(Enum):
    pending = "Pending"
    active = "Active"
    finished = "Finished"
    cancelled = "Cancelled"


class GameStatus(db.Model):
    __tablename__ = "game_status"

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'))
    status = db.Column(db.Enum(StatusTypes))
    updated_at = db.Column(db.DateTime)  # When was the game opened


class GameInvites(db.Model):
    __tablename__ = "game_invites"

    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    invitee_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    game_id = db.Column(db.Integer, db.ForeignKey("games.id"))
    opened_at = db.Column(db.DateTime)  # When was the game opened
    open_until = db.Column(db.DateTime)  # When the game closes


class TradeTypes(Enum):

    long = "Long"  # A simple long hold
    short = "Short"  # A vanilla short margin trade


class Positions(db.Model):
    __tablename__ = "positions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    game_id = db.Column(db.Integer, db.ForeignKey("games.id"))
    ticker = db.Column(db.Text)  # Only American securities for now.
    trade_type = db.Column(db.Enum(TradeTypes))
    shares = db.Column(db.Integer)
    purchase_price = db.Column(db.Float)
    purchase_time = db.Column(db.DateTime)
    sale_price = db.Column(db.Float)
    sale_time = db.Column(db.DateTime)
