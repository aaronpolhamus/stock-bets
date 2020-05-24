"""Logic for creating games and storing default parameters
"""
import math
import time

from backend.database.helpers import (
    unpack_enumerated_field_mappings,
    retrieve_meta_data,
    orm_row_to_dict,
    table_updater
)
from backend.database.models import (
    GameModes,
    Benchmarks,
    SideBetPeriods,
    OrderTypes,
    BuyOrSell,
    TimeInForce)
from funkybob import RandomNameGenerator

# Default make game settings
# --------------------------
DEFAULT_GAME_MODE = "return_weighted"
DEFAULT_GAME_DURATION = 30  # days
DEFAULT_BUYIN = 100  # dolllars
DEFAULT_REBUYS = 0  # How many rebuys are allowed
DEFAULT_BENCHMARK = "return_ratio"
DEFAULT_SIDEBET_PERCENT = 0
DEFAULT_SIDEBET_PERIOD = "weekly"
DEFAULT_INVITE_OPEN_WINDOW = 24 * 60 * 60  # Number of seconds that a game invite is open for (2 days)
DEFAULT_VIRTUAL_CASH = 1_000_000  # USD
DEFAULT_N_PARTICIPANTS_TO_START = 2  # Minimum number of participants required to have accepted an invite to start game

QUANTITY_DEFAULT = "Shares"
QUANTITY_OPTIONS = ["Shares", "USD"]

"""Quick note about implementation here: The function unpack_enumerated_field_mappings extracts the natural language
label of each integer entry for the DB and send that value: label mapping to the frontend as a dictionary (or Object) 
in javascript. We handle value-label mapping concerns on the frontend.
"""
GAME_MODES = unpack_enumerated_field_mappings(GameModes)
BENCHMARKS = unpack_enumerated_field_mappings(Benchmarks)
SIDE_BET_PERIODS = unpack_enumerated_field_mappings(SideBetPeriods)

# Default play game settings
# --------------------------
DEFAULT_BUY_SELL = "buy"
BUY_SELL_TYPES = unpack_enumerated_field_mappings(BuyOrSell)
DEFAULT_ORDER_TYPE = "market"
ORDER_TYPES = unpack_enumerated_field_mappings(OrderTypes)
DEFAULT_TIME_IN_FORCE = "day"
TIME_IN_FORCE_TYPES = unpack_enumerated_field_mappings(TimeInForce)


# Exceptions
# ----------
class InsufficientFunds(Exception):

    def __str__(self):
        return "Insufficient funds to complete this purchase"


class InsufficientHoldings(Exception):

    def __str__(self):
        return "You can't sell more of a position than you currently own"


class LimitError(Exception):

    def __str__(self):
        return "You've set your limit order below the current market price: this would effectively be a market order"


def make_random_game_title():
    title_iterator = iter(RandomNameGenerator())
    return next(title_iterator).replace("_", " ")


# Functions for starting, joining, and funding games
# --------------------------------------------------
def respond_to_invite(db_session, game_id, user_id, status):
    with db_session.connection() as conn:
        game_invites = retrieve_meta_data(conn).tables["game_invites"]
        table_updater(conn, game_invites, game_id=game_id, user_id=user_id, status=status, timestamp=time.time())

    db_session.commit()


def get_open_game_ids(conn):
    """This function returns game IDs for the subset of th game that are both open and past their invite window. We pass
    the resulting IDs to service_open_game to figure out whether to activate or close the game, and identify who's
    participating
    """
    result = conn.execute("""
    SELECT g.id
    FROM games g
    INNER JOIN
    (
      SELECT gs.game_id, gs.status
      FROM game_status gs
      INNER JOIN
      (SELECT game_id, max(id) as max_id
        FROM game_status
        GROUP BY game_id) grouped_gs
      ON
        gs.id = grouped_gs.max_id
      WHERE gs.status = 'pending'
    ) pending_game_ids
    ON
      g.id = pending_game_ids.game_id
    WHERE
        pending_game_ids.status = 'pending' AND
        invite_window < UNIX_TIMESTAMP();
    """).fetchall()
    return [x[0] for x in result]


def service_open_game(db_session, game_id):
    """Important note: This function doesn't have any logic to verify that it's operating on an open game. It should
    ONLY be applied to IDs passed in from get_open_game_ids
    """
    with db_session.connection() as conn:
        game_status = retrieve_meta_data(conn).tables["game_status"]
        row = db_session.query(game_status).filter(game_status.c.game_id == game_id)
        game_status_entry = orm_row_to_dict(row)

        game_invites = retrieve_meta_data(conn).tables["game_invites"]

        result = conn.execute("SELECT user_id FROM game_invites WHERE game_id = %s AND status = 'joined';",
                              game_id).fetchall()
        accepted_invite_user_ids = [x[0] for x in result]
        if len(accepted_invite_user_ids) >= DEFAULT_N_PARTICIPANTS_TO_START:
            # If we have quorum, game is active and we can mark it as such on the game status table
            game_status_entry["status"] = "active"
            game_status_entry["users"] = accepted_invite_user_ids
            conn.execute(game_status.insert(), game_status_entry)

            # Any users with an outstanding invite who haven't joined now have their invitations marked as "expired"

            result = conn.execute("SELECT user_id FROM game_invites WHERE game_id = %s AND status = 'invited';",
                                  game_id).fetchall()
            ids_to_close = [x[0] for x in result]
        else:
            # If we're past the invite window and we don't have quorum, close the game
            game_status_entry["status"] = "expired"
            conn.execute(game_status.insert(), game_status_entry)

            result = conn.execute(
                "SELECT user_id FROM game_invites WHERE game_id = %s AND status in ('active', 'joined');",
                game_id).fetchall()
            ids_to_close = [x[0] for x in result]

        # close any expired invites from either active or expired games
        for user_id in ids_to_close:
            table_updater(conn, game_invites, game_id=game_id, user_id=user_id, status="expired")

    db_session.commit()


# Functions for handling placing and execution of orders
# ------------------------------------------------------
def get_current_game_cash_balance(conn, user_id, game_id):
    """Get the user's current virtual cash balance for a given game. Expects a valid database connection for query
    execution to be passed in from the outside
    """

    sql_query = """
        SELECT balance
        FROM game_balances gb
        INNER JOIN
        (SELECT user_id, game_id, balance_type, max(id) as max_id
          FROM game_balances
          WHERE
            user_id = %s AND
            game_id = %s AND
            balance_type = 'virtual_cash'
          GROUP BY game_id, balance_type, user_id) grouped_gb
        ON
          gb.id = grouped_gb.max_id;    
    """
    return conn.execute(sql_query, (user_id, game_id)).fetchone()[0]


def get_current_stock_holding(conn, user_id, game_id, symbol):
    """Get the user's current virtual cash balance for a given game. Expects a valid database connection for query
    execution to be passed in from the outside
    """

    sql_query = """
        SELECT balance
        FROM game_balances gb
        INNER JOIN
        (SELECT user_id, game_id, balance_type, max(id) as max_id
          FROM game_balances
          WHERE
            user_id = %s AND
            game_id = %s AND
            symbol = %s AND
            balance_type = 'virtual_stock'
          GROUP BY game_id, balance_type, user_id) grouped_gb
        ON
          gb.id = grouped_gb.max_id;    
    """
    return conn.execute(sql_query, (user_id, game_id, symbol)).fetchone()[0]


def get_all_current_stock_holdings(conn, user_id, game_id):
    """Get the user's current virtual cash balance for a given game. Expects a valid database connection for query
    execution to be passed in from the outside
    """

    sql_query = """
        SELECT gb.symbol, balance
        FROM game_balances gb
        INNER JOIN
        (SELECT user_id, game_id, symbol, balance_type, max(id) as max_id
          FROM game_balances
          WHERE
            user_id = %s AND
            game_id = %s AND
            balance_type = 'virtual_stock'
          GROUP BY user_id, game_id, symbol, balance_type) grouped_gb
        ON
          gb.id = grouped_gb.max_id;    
    """
    result = conn.execute(sql_query, (user_id, game_id)).fetchall()
    return {stock: holding for stock, holding in result}


def stop_limit_qc(buy_or_sell, order_type, order_price, market_price):
    """The conditions that would cause us to flag a stop/limit order don't depend on whether the ticket is buy or sell,
    so we encompass that logic here
    """
    if (buy_or_sell == "buy" and order_type == "limit") or (buy_or_sell == "sell" and order_type == "stop"):
        if market_price < order_price:
            raise LimitError(
                "Your stop price is higher than the current market price: this would effectively be a market order")

    if (buy_or_sell == "buy" and order_type == "stop") or (buy_or_sell == "sell" and order_type == "limit"):
        if market_price > order_price:
            raise LimitError
    return True


def qc_sell_order(order_type, quantity_type, order_price, market_price, amount, current_holding):
    """this function checks the values provided by a sale order ticket, along with the user's current holdings, to
    make sure that the transaction. Downstream methods will process it
    """
    assert quantity_type in QUANTITY_OPTIONS
    assert order_type in ORDER_TYPES

    if quantity_type == "Shares":
        if amount > current_holding:
            raise InsufficientHoldings

    if quantity_type == "USD":
        shares_to_sell = math.ceil(amount / order_price)
        if shares_to_sell > current_holding:
            raise InsufficientHoldings(f"You'd need {shares_to_sell} in order to make ${order_price} on this order")

    stop_limit_qc("sell", order_type, order_price, market_price)
    return True


def qc_buy_order(order_type, quantity_type, order_price, market_price, amount, cash_balance):
    """ditto to above, just for buy orders"""
    assert quantity_type in QUANTITY_OPTIONS
    assert order_type in ORDER_TYPES

    if quantity_type == "Shares":
        if amount * order_price > cash_balance:
            raise InsufficientFunds

    if quantity_type == "USD":
        if amount > cash_balance:
            raise InsufficientFunds

    stop_limit_qc("buy", order_type, order_price, market_price)
    return True


def get_order_price(order_ticket):
    order_type = order_ticket["order_type"]
    if order_type == "market":
        return order_ticket["market_price"]
    if order_type in ["stop", "limit"]:
        return order_ticket["stop_limit_price"]
    raise Exception("Invalid order type for this ticket")


def get_order_quantity(order_ticket):
    quantity_type = order_ticket["quantity_type"]
    amount = float(order_ticket["amount"])
    order_price = get_order_price(order_ticket)

    if quantity_type == "USD":
        return int(amount / order_price)
    elif quantity_type == "Shares":
        return amount
    Exception("Invalid quantity type for this ticket")


def get_all_open_orders(conn):
    """Get all open orders, and the timestamp that they were placed at for when we cross-check against the time-in-force
    field. This query is written implicitly assumes that any given order will only ever have one "pending" entry.
    """
    sql_query = """
        SELECT os.order_id, os.timestamp
        FROM order_status os
        INNER JOIN
        (SELECT order_id, max(id) as max_id
          FROM order_status
          GROUP BY order_id) grouped_os
        ON
          os.id = grouped_os.max_id
        WHERE os.status = 'pending';
    """
    result = conn.execute(sql_query).fetchall()
    return {order_id: ts for order_id, ts in result}
