"""Logic for creating games and storing default parameters
"""
import json
import math
import time
from datetime import timedelta
from typing import List

import pandas as pd
import pandas_market_calendars as mcal
from backend.database.db import engine
from backend.database.helpers import (
    query_to_dict,
    add_row,
    unpack_enumerated_field_mappings,
)
from backend.database.models import (
    GameModes,
    Benchmarks,
    SideBetPeriods,
    OrderTypes,
    BuyOrSell,
    TimeInForce)
from backend.logic.base import (
    DEFAULT_VIRTUAL_CASH,
    get_current_game_cash_balance,
    posix_to_datetime,
    get_next_trading_day_schedule,
    get_schedule_start_and_end,
    during_trading_day
)
from backend.logic.visuals import (
    serialize_and_pack_winners_table,
    serialize_and_pack_orders_open_orders,
    serialize_and_pack_current_balances,
    compile_and_pack_player_sidebar_stats,
    make_the_field_charts
)
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

# NYSE is default trading calendar
# --------------------------------
nyse = mcal.get_calendar('NYSE')


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


class NoNegativeOrders(Exception):

    def __str__(self):
        return "You can't transact a zero or negative quantity -- did you mean to change the buy/sell option? Support for short orders coming soon."


def make_random_game_title():
    title_iterator = iter(RandomNameGenerator())
    return next(title_iterator).replace("_", " ")


# Functions for starting, joining, and funding games
# --------------------------------------------------
def add_game(creator_id, title, mode, duration, buy_in, n_rebuys, benchmark, side_bets_perc, side_bets_period,
             invitees):
    opened_at = time.time()
    invite_window = opened_at + DEFAULT_INVITE_OPEN_WINDOW
    game_id = add_row("games",
                      creator_id=creator_id,
                      title=title,
                      mode=mode,
                      duration=duration,
                      buy_in=buy_in,
                      n_rebuys=n_rebuys,
                      benchmark=benchmark,
                      side_bets_perc=side_bets_perc,
                      side_bets_period=side_bets_period,
                      invite_window=invite_window)
    invited_ids = translate_usernames_to_ids(tuple(invitees))
    user_ids = invited_ids + [creator_id]

    create_pending_game_status_entry(game_id, user_ids, opened_at)
    create_game_invites_entries(game_id, creator_id, user_ids, opened_at)


def get_open_game_invite_ids():
    """This function returns game IDs for the subset of games that are both open and past their invite window. We pass
    the resulting IDs to service_open_game to figure out whether to activate or close the game, and identify who's
    participating
    """
    with engine.connect() as conn:
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
        WHERE invite_window < %s;
        """, time.time()).fetchall()  # yep, I know about UNIX_TIMESTAMP() -- this is necessary for test mocking
    return [x[0] for x in result]


def get_active_game_ids():
    with engine.connect() as conn:
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
          WHERE gs.status = 'active'
        ) pending_game_ids
        ON
          g.id = pending_game_ids.game_id;""").fetchall()
    return [x[0] for x in result]


def translate_usernames_to_ids(usernames: tuple):
    with engine.connect() as conn:
        res = conn.execute(f"""
            SELECT id FROM users WHERE username in ({",".join(['%s'] * len(usernames))});
        """, usernames).fetchall()
    return [x[0] for x in res]


def create_pending_game_status_entry(game_id, user_ids, opened_at):
    add_row("game_status", game_id=game_id, status="pending", timestamp=opened_at, users=user_ids)


def create_game_invites_entries(game_id, creator_id, user_ids, opened_at):
    for user_id in user_ids:
        status = "invited"
        if user_id == creator_id:
            status = "joined"
        add_row("game_invites", game_id=game_id, user_id=user_id, status=status, timestamp=opened_at)


def get_invite_list_by_status(game_id, status="joined"):
    with engine.connect() as conn:
        result = conn.execute("""
            SELECT gi.user_id 
            FROM game_invites gi
            INNER JOIN
              (SELECT game_id, user_id, max(id) as max_id
                FROM game_invites
                GROUP BY game_id, user_id) grouped_gi
            ON
              gi.id = grouped_gi.max_id
            WHERE 
              gi.game_id = %s AND 
              status = %s;""", game_id, status).fetchall()
    return [x[0] for x in result]


def kick_off_game(game_id: int, user_id_list: List[int], update_time):
    """Mark a game as active and seed users' virtual cash balances
    """
    game_status_entry = query_to_dict("SELECT * FROM game_status WHERE game_id = %s", game_id)
    add_row("game_status", game_id=game_status_entry["game_id"], status="active", users=user_id_list,
            timestamp=update_time)
    for user_id in user_id_list:
        add_row("game_balances", user_id=user_id, game_id=game_id, timestamp=update_time, balance_type="virtual_cash",
                balance=DEFAULT_VIRTUAL_CASH)

    # Mark any outstanding invitations as "expired" now that the game is active
    mark_invites_expired(game_id, ["invited"], update_time)

    # initialize a blank sidebar stats entry
    compile_and_pack_player_sidebar_stats(game_id)

    # initialize a blank payouts table
    serialize_and_pack_winners_table(game_id)

    # initialize current balances and open orders
    for user_id in user_id_list:
        serialize_and_pack_current_balances(game_id, user_id)
        serialize_and_pack_orders_open_orders(game_id, user_id)

    # initialize graphics -- this is normally a very heavy function, but it's super-light when starting a game
    make_the_field_charts(game_id)


def close_game(game_id, update_time):
    game_status_entry = query_to_dict("SELECT * FROM game_status WHERE game_id = %s", game_id)
    add_row("game_status", game_id=game_status_entry["game_id"], status="expired",
            users=json.loads(game_status_entry["users"]), timestamp=update_time)
    mark_invites_expired(game_id, ["invited", "joined"], update_time)


def mark_invites_expired(game_id, status_list: List[str], update_time):
    """For a given game ID and list of statuses, this function will convert those invitations to "expired." This
    happens when games past their invite window still have pending invitations, or when games pass their invite window
    without meeting the minimum user count to kick off
    """
    if not status_list:
        return

    with engine.connect() as conn:
        result = conn.execute(f"""
            SELECT gi.user_id
            FROM game_invites gi
            INNER JOIN
              (SELECT game_id, user_id, max(id) as max_id
                FROM game_invites
                GROUP BY game_id, user_id) grouped_gi
            ON
              gi.id = grouped_gi.max_id
            WHERE
              gi.game_id = %s AND
              status IN ({','.join(['%s'] * len(status_list))});
              """, game_id, *status_list)
        ids_to_close = [x[0] for x in result]

    for user_id in ids_to_close:
        add_row("game_invites", game_id=game_id, user_id=user_id, status="expired", timestamp=update_time)


def service_open_game(game_id):
    """Important note: This function doesn't have any logic to verify that it's operating on an open game. It should
    ONLY be applied to IDs passed in from get_open_game_invite_ids
    """
    update_time = time.time()
    accepted_invite_user_ids = get_invite_list_by_status(game_id)
    if len(accepted_invite_user_ids) >= DEFAULT_N_PARTICIPANTS_TO_START:
        # If we have quorum, game is active and we can mark it as such on the game status table
        kick_off_game(game_id, accepted_invite_user_ids, update_time)
    else:
        close_game(game_id, update_time)


def start_game_if_all_invites_responded(game_id):
    accepted_invite_user_ids = get_invite_list_by_status(game_id)
    pending_invite_ids = get_invite_list_by_status(game_id, "invited")
    if len(accepted_invite_user_ids) >= DEFAULT_N_PARTICIPANTS_TO_START and len(pending_invite_ids) == 0:
        kick_off_game(game_id, accepted_invite_user_ids, time.time())


def get_game_info_for_user(user_id):
    """This big, ugly SQL query aggregates a bunch of information about a user's game invites and active games for
    display on the home page
    """
    sql = """
        SELECT 
            gs.game_id, 
            g.title,
            g.creator_id,
            creator_info.profile_pic AS creator_avatar,
            creator_info.username AS creator_username,
            gs.users,
            gs.status AS game_status,
            gi_status.status AS invite_status
        FROM game_status gs
        INNER JOIN
          (SELECT game_id, max(id) as max_id
            FROM game_status
            GROUP BY game_id) grouped_gs
            ON gs.id = grouped_gs.max_id
        INNER JOIN
          (SELECT gi.game_id, gi.status
            FROM game_invites gi
            INNER JOIN
            (SELECT game_id, user_id, max(id) as max_id
                FROM game_invites
                GROUP BY game_id, user_id) gg_invites
                ON gi.id = gg_invites.max_id
                WHERE gi.user_id = %s AND
                gi.status IN ('invited', 'joined')) gi_status
            ON gi_status.game_id = gs.game_id
        INNER JOIN
          games g on gs.game_id = g.id
        INNER JOIN
          users creator_info ON creator_info.id = g.creator_id
        WHERE gs.status IN ('active', 'pending');
    """
    with engine.connect() as conn:
        return pd.read_sql(sql, conn, params=[str(user_id)]).to_dict(orient="records")


def respond_to_invite(game_id, user_id, status, response_time):
    add_row("game_invites", game_id=game_id, user_id=user_id, status=status, timestamp=response_time)


def get_user_invite_statuses_for_pending_game(game_id):
    sql = f"""
            SELECT creator_id, users.username, gi_status.status, users.profile_pic
            FROM game_status gs
            INNER JOIN
              (SELECT game_id, max(id) as max_id
                FROM game_status
                GROUP BY game_id) grouped_gs
                ON gs.id = grouped_gs.max_id
            INNER JOIN
              (SELECT gi.game_id, gi.user_id, gi.status
                FROM game_invites gi
                INNER JOIN
                (SELECT game_id, user_id, max(id) as max_id
                    FROM game_invites
                    GROUP BY game_id, user_id) gg_invites
                    ON gi.id = gg_invites.max_id) gi_status
                ON gi_status.game_id = gs.game_id
            INNER JOIN users ON users.id = gi_status.user_id
            INNER JOIN games g ON g.id = gs.game_id
            WHERE gs.game_id = %s;
    """
    with engine.connect() as conn:
        return pd.read_sql(sql, conn, params=[game_id]).to_dict(orient="records")


# Functions for handling placing and execution of orders
# ------------------------------------------------------
def get_current_stock_holding(user_id, game_id, symbol):
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
    with engine.connect() as conn:
        results = conn.execute(sql_query, (user_id, game_id, symbol)).fetchall()

    assert len(results) in [0, 1]
    if len(results) == 1:
        return results[0][0]
    return 0


def get_all_current_stock_holdings(user_id, game_id):
    """Get the user's current balances for display in the front end
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
    with engine.connect() as conn:
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


def get_order_price(order_type, market_price, stop_limit_price):
    if order_type == "market":
        return market_price
    if order_type in ["stop", "limit"]:
        if stop_limit_price is None:
            raise Exception("Order type is stop/limit but the stop/limit price is None")
        return stop_limit_price
    raise Exception("Invalid order type for this ticket")


def get_order_quantity(order_price, amount, quantity_type):
    if quantity_type == "USD":
        return int(amount / order_price)
    elif quantity_type == "Shares":
        return amount
    raise Exception("Invalid quantity type for this ticket")


def get_all_open_orders():
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
    with engine.connect() as conn:
        result = conn.execute(sql_query).fetchall()
    return {order_id: ts for order_id, ts in result}


def update_balances(user_id, game_id, order_status_id, timestamp, buy_or_sell, cash_balance, current_holding,
                    order_price, order_quantity, symbol):
    """This function books an order and updates a user's cash balance at the same time.
    """
    sign = 1 if buy_or_sell == "buy" else -1
    add_row("game_balances", user_id=user_id, game_id=game_id, order_status_id=order_status_id, timestamp=timestamp,
            balance_type="virtual_cash", balance=cash_balance - sign * order_quantity * order_price)
    add_row("game_balances", user_id=user_id, game_id=game_id, order_status_id=order_status_id, timestamp=timestamp,
            balance_type="virtual_stock", balance=current_holding + sign * order_quantity, symbol=symbol)


def place_order(user_id, game_id, symbol, buy_or_sell, cash_balance, current_holding, order_type, quantity_type,
                market_price, amount, time_in_force, stop_limit_price=None):
    timestamp = time.time()
    order_price = get_order_price(order_type, market_price, stop_limit_price)
    order_quantity = get_order_quantity(order_price, amount, quantity_type)
    if order_quantity <= 0:
        raise NoNegativeOrders

    if buy_or_sell == "buy":
        qc_buy_order(order_type, quantity_type, order_price, market_price, amount, cash_balance)
    elif buy_or_sell == "sell":
        qc_sell_order(order_type, quantity_type, order_price, market_price, amount, current_holding)
    else:
        raise Exception(f"Invalid buy or sell option {buy_or_sell}")

    # having validated the order, now we'll go ahead and book it
    order_id = add_row("orders", user_id=user_id, game_id=game_id, symbol=symbol, buy_or_sell=buy_or_sell,
                       quantity=order_quantity, price=order_price, order_type=order_type, time_in_force=time_in_force)

    add_row("order_status", order_id=order_id, timestamp=timestamp, status="pending", clear_price=None)

    # If this is a market order and we're inside a trading day we'll execute this order at the current price
    if order_type == "market" and during_trading_day():
        os_id = add_row("order_status", order_id=order_id, timestamp=timestamp, status="fulfilled",
                        clear_price=order_price)
        update_balances(user_id, game_id, os_id, timestamp, buy_or_sell, cash_balance, current_holding, order_price,
                        order_quantity, symbol)


def get_order_ticket(order_id):
    return query_to_dict("SELECT * FROM orders WHERE id = %s", order_id)


def process_order(game_id, user_id, symbol, order_id, buy_or_sell, order_type, order_price, market_price,
                  quantity, timestamp):
    # Only process active outstanding orders during trading day
    cash_balance = get_current_game_cash_balance(user_id, game_id)
    current_holding = get_current_stock_holding(user_id, game_id, symbol)
    if during_trading_day() and execute_order(buy_or_sell, order_type, market_price, order_price, cash_balance,
                                              current_holding, quantity):
        order_status_id = add_row("order_status", order_id=order_id, timestamp=timestamp, status="fulfilled",
                                  clear_price=market_price)
        update_balances(user_id, game_id, order_status_id, timestamp, buy_or_sell, cash_balance, current_holding,
                        market_price, quantity, symbol)


def get_order_expiration_status(order_id):
    """Before processing an order, we'll use logic to determine whether that order is still active. This function
    return True if an order is expired, or false otherwise.
    """
    with engine.connect() as conn:
        time_in_force = conn.execute("SELECT time_in_force FROM orders WHERE id = %s;", order_id).fetchone()[0]
        if time_in_force == "until_cancelled":
            return False

    # posix_to_datetime
    current_time = time.time()
    with engine.connect() as conn:
        time_placed = conn.execute("""SELECT timestamp 
                                      FROM order_status 
                                      WHERE order_id = %s 
                                      ORDER BY id LIMIT 0, 1;""", order_id).fetchone()[0]

    time_placed_nyc = posix_to_datetime(time_placed)

    schedule = nyse.schedule(time_placed_nyc, time_placed_nyc)
    if schedule.empty:
        next_day_schedule = get_next_trading_day_schedule(time_placed_nyc)
        _, cutoff_time = get_schedule_start_and_end(next_day_schedule)
    else:
        if time_placed_nyc.hour >= 16:
            next_day_schedule = get_next_trading_day_schedule(time_placed_nyc + timedelta(days=1))
            _, cutoff_time = get_schedule_start_and_end(next_day_schedule)
        else:
            _, cutoff_time = get_schedule_start_and_end(schedule)

    if current_time > cutoff_time:
        return True
    return False


def execute_order(buy_or_sell, order_type, market_price, order_price, cash_balance, current_holding, quantity):
    """Function to flag an order for execution based on order type, price, and market price
    """
    assert order_type in ["stop", "limit", "market"]
    assert buy_or_sell in ["buy", "sell"]

    if buy_or_sell == "sell":
        if quantity > current_holding:
            return False

        if order_type == "market":
            return True

        if order_type == "limit":
            if market_price >= order_price:
                return True
            return False

        if market_price <= order_price:
            return True

        return False

    if cash_balance > quantity * market_price:
        if order_type == "market":
            return True

        if order_type == "limit":
            if market_price <= order_price:
                return True
            return False

        if market_price >= order_price:
            return True

    return False

# Functions for serving information about games
# ---------------------------------------------


def get_user_invite_status_for_game(game_id: int, user_id: int):
    with engine.connect() as conn:
        status = conn.execute("""
            SELECT gi.status
            FROM game_invites gi
            INNER JOIN
            (SELECT game_id, user_id, max(id) as max_id
              FROM game_invites
              GROUP BY game_id, user_id) grouped_gi
            ON
              gi.id = grouped_gi.max_id
            WHERE gi.game_id = %s AND gi.user_id = %s;
        """, game_id, user_id).fetchone()[0]
    return status
