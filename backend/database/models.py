"""For this iteration I'm conflating the definition of our applications database with the Flask-Migrate abstractions
to manage it. I'd like to do something cleaner, once I have a better understanding of what's going on with flake

Check out this structure:
https://stackoverflow.com/questions/56230626/why-is-sqlalchemy-database-uri-set-to-sqlite-memory-when-i-set-it-to-a-pa
"""

from aenum import Enum

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
    WINNER_TAKES_ALL = 0, "Winner takes all"
    CONSOLATION_PRIZE = 1, "Consolation prize"
    RETURN_WEIGHTED = 2, "Return-weighted"


class Benchmarks(Enum):
    RETURN_RATIO = 0, "Simple return"
    SHARPE_RATIO = 1, "Sharpe ratio-adjusted"


class Games(db.Model):
    __tablename__ = "games"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text)
    mode = db.Column(db.Enum(GameModes))
    duration = db.Column(db.Integer)  # Integer values for n trading days game is live for
    buy_in = db.Column(db.DECIMAL)
    benchmark = db.Column(db.Enum(Benchmarks))


class StatusTypes(Enum):
    PENDING = 0, "Pending"
    ACTIVE = 1, "Active"
    FINISHED = 2, "Finished"
    CANCELLED = 3, "Cancelled"


class GameStatus(db.Model):
    __tablename__ = "game_status"

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'))
    status = db.Column(db.Enum(StatusTypes))
    opened_at = db.Column(db.DateTime)  # When was the game opened
    open_until = db.Column(db.DateTime)
    started_at = db.Column(db.DateTime)
    ends_at = db.Column(db.DateTime)


class GameInvites(db.Model):
    __tablename__ = "game_invites"

    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    invitee_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    game_id = db.Column(db.Integer, db.ForeignKey("games.id"))


class TradeTypes(Enum):
    LONG = 0, "Long"  # A simple long hold
    SHORT = 1, "Short"  # A vanilla short margin trade


class Positions(db.Model):
    __tablename__ = "positions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    game_id = db.Column(db.Integer, db.ForeignKey("games.id"))
    ticker = db.Column(db.Text)  # Only American securities for now.
    trade_type = db.Column(db.Enum(TradeTypes))
    shares = db.Column(db.Integer)
    purchase_price = db.Column(db.DECIMAL)
    purchase_time = db.Column(db.DateTime)
    sale_price = db.Column(db.DECIMAL)
    sale_time = db.Column(db.DateTime)
