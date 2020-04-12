import enum

from backend.app import db


class Users(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.Text)
    username = db.Column(db.Text)


class GameModes(int, enum.Enum):
    WINNER_TAKES_ALL = 0
    CONSOLATION_PRIZE = 1
    WINNER_TAKES_RETURN = 2


class Benchmarks(int, enum.Enum):
    RETURN_RATIO = 0
    SHARPE_RATIO = 1


class Games(db.Model):
    __tablename__ = "games"

    id = db.Column(db.Integer, primary_key=True)
    opened_at = db.Column(db.DateTime)  # When was the game opened
    title = db.Column(db.Text)
    mode = db.Column(db.Enum(GameModes))
    duration = db.Column(db.Integer)  # Integer values for n trading days game is live for
    min_buy = db.Column(db.DECIMAL)
    max_buy = db.Column(db.DECIMAL)
    benchmark = db.Column(db.Enum(Benchmarks))


class StatusTypes(int, enum.Enum):
    PENDING = 0
    ACTIVE = 1
    FINISHED = 2
    CANCELLED = 3


class GameStatus(db.Model):
    __tablename__ = "game_status"

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'))
    status = db.Column(db.Enum(StatusTypes))
    timestamp = db.Column(db.DateTime)


class GameInvites(db.Model):
    __tablename__ = "game_invites"

    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    invitee_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    game_id = db.Column(db.Integer, db.ForeignKey("games.id"))


class TradeTypes(int, enum.Enum):
    LONG = 0  # A simple long hold
    SHORT = 1  # A vanilla short margin trade


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
