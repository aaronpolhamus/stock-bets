import time

from backend.config import Config
from backend.database.db import db_session
from backend.database.helpers import (
    retrieve_meta_data,
    orm_row_to_dict,
    table_updater
)
from backend.logic.games import (
    get_current_game_cash_balance,
    get_current_stock_holding,
    qc_buy_order,
    qc_sell_order,
    get_all_open_orders,
    get_order_price,
    get_order_quantity,
    SECONDS_IN_A_TRADING_DAY,
    DEFAULT_INVITE_OPEN_WINDOW
)
from backend.logic.stock_data import (
    get_symbols_table,
    fetch_iex_price
)
from backend.tasks.celery import celery, SqlAlchemyTask
from backend.tasks.redis import r
from sqlalchemy import create_engine, select


@celery.task(name="tasks.update_symbols", bind=True, default_retry_delay=10, base=SqlAlchemyTask)
def update_symbols_table(self):
    try:
        symbols_table = get_symbols_table()
        print("writing to db...")
        db_session.execute("TRUNCATE TABLE symbols;")
        with db_session.connection() as conn:
            symbols_table.to_sql("symbols", conn, if_exists="append", index=False)
            db_session.commit()
    except Exception as exc:
        raise self.retry(exc=exc)


@celery.task(name="tasks.fetch_price")
def fetch_price(symbol):
    """For now this is just a silly wrapping step that allows us to decorate the external function into our celery tasks
    inventory. Lots of room to add future nuance here around different data providers, cache look-ups, etc.
    """
    return fetch_iex_price(symbol)


@celery.task(name="tasks.cache_price")
def cache_price(symbol: str, price: float, last_updated: float):
    """We'll store the last-updated price of each monitored stock in redis. In the short-term this will save us some
    unnecessary data API call.
    """
    r.set(symbol, f"{price}_{last_updated}")


@celery.task(name="tasks.fetch_symbols")
def fetch_symbols(text):
    to_match = f"{text.upper()}%"
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    suggest_query = """
        SELECT * FROM symbols
        WHERE symbol LIKE %s OR name LIKE %s LIMIT 20;;
    """

    with engine.connect() as conn:
        symbol_suggestions = conn.execute(suggest_query, (to_match, to_match))

    return [{"symbol": entry[1], "label": f"{entry[1]} ({entry[2]})"} for entry in symbol_suggestions]


@celery.task(name="task.update_game_table", bind=True, base=SqlAlchemyTask)
def update_game_table(self, game_settings):
    opened_at = time.time()
    invite_window = opened_at + DEFAULT_INVITE_OPEN_WINDOW * 60 * 60

    with db_session.connection() as conn:
        metadata = retrieve_meta_data(conn)
        games = metadata.tables["games"]
        game_status = metadata.tables["game_status"]
        users = metadata.tables["users"]

        result = table_updater(conn, games,
                               creator_id=game_settings["creator_id"],
                               title=game_settings["title"],
                               mode=game_settings["mode"],
                               duration=game_settings["duration"],
                               buy_in=game_settings["buy_in"],
                               n_rebuys=game_settings["n_rebuys"],
                               benchmark=game_settings["benchmark"],
                               side_bets_perc=game_settings["side_bets_perc"],
                               side_bets_period=game_settings["side_bets_period"],
                               invite_window=invite_window)
        db_session.commit()

    with db_session.connection() as conn:
        # Update game status table
        game_id = result.inserted_primary_key[0]
        invitees = tuple(game_settings["invitees"])
        invitee_ids = conn.execute(select([users.c.id], users.c.username.in_(invitees))).fetchall()
        user_ids = [x[0] for x in invitee_ids]
        user_ids.append(game_settings["creator_id"])
        status_entry = {"game_id": game_id, "status": "pending", "timestamp": opened_at, "users": user_ids}
        conn.execute(game_status.insert(), status_entry)
        db_session.commit()


@celery.task(name="tasks.place_order", base=SqlAlchemyTask)
def place_order(order_ticket):
    """Placing an order involves several layers of conditional logic: is this is a buy or sell order? Stop, limit, or
    market? Do we either have the adequate cash on hand, or enough of a position in the stock for this order to be
    valid? Here an order_ticket from the frontend--along with the user_id tacked on during the API call--gets decoded,
    checked for validity, and booked. Market orders are fulfilled in the same step. Stop/limit orders are monitored on
    an ongoing basis by the celery schedule and book as their requirements are satisfies
    """
    # set the transaction time
    timestamp = time.time()

    # extract relevant data
    user_id = order_ticket["user_id"]
    game_id = order_ticket["game_id"]
    symbol = order_ticket["symbol"]
    order_type = order_ticket["order_type"]
    quantity_type = order_ticket["quantity_type"]
    market_price = order_ticket["market_price"]
    amount = float(order_ticket["amount"])
    buy_or_sell = order_ticket["buy_or_sell"]
    time_in_force = order_ticket["time_in_force"]

    order_price = get_order_price(order_ticket)
    order_quantity = get_order_quantity(order_ticket)

    # check transaction validity
    with db_session.connection() as conn:
        metadata = retrieve_meta_data(conn)
        cash_balance = get_current_game_cash_balance(conn, user_id, game_id)
        current_holding = get_current_stock_holding(conn, user_id, game_id, symbol)

        sign = 1 if buy_or_sell == "buy" else -1
        if buy_or_sell == "buy":
            qc_buy_order(order_type, quantity_type, order_price, market_price, amount, cash_balance)
        elif buy_or_sell == "sell":
            qc_sell_order(order_type, quantity_type, order_price, market_price, amount, current_holding)
        else:
            raise Exception(f"Invalid buy or sell option {buy_or_sell}")

        # having validated the order, now we'll go ahead and book it
        orders = metadata.tables["orders"]
        result = table_updater(conn, orders, user_id=user_id, game_id=game_id, symbol=symbol, buy_or_sell=buy_or_sell,
                               quantity=order_quantity, price=order_price, order_type=order_type,
                               time_in_force=time_in_force)
        db_session.commit()

    with db_session.connection() as conn:
        order_status = metadata.tables["order_status"]
        game_balances = metadata.table["game_balances"]
        if order_type == "market":
            status = "fulfilled"
            clear_price = order_price
            # if this is a market order, book it right away and update balances
            table_updater(conn, game_balances, user_id=user_id, game_id=game_id, timestamp=timestamp,
                          balance_type="virtual_cash", balance=cash_balance - sign * order_quantity * order_price)
            table_updater(conn, game_balances, user_id=user_id, game_id=game_id, timestamp=timestamp,
                          balance_type="virtual_stock", balance=current_holding + sign * order_quantity)
        else:
            status = "pending"
            clear_price = None
        db_session.commit()

    with db_session.connection() as conn:
        table_updater(conn, order_status, order_id=result.inserted_primary_key[0], timestamp=timestamp, status=status,
                      clear_price=clear_price)
        db_session.commit()


@celery.task(name="tasks.async_process_single_order", base=SqlAlchemyTask)
def process_single_order(order_id, expiration):

    with db_session.connection() as conn:
        timestamp = time.time()
        meta = retrieve_meta_data(conn)
        orders = meta.tables["orders"]
        order_status = meta.tables["order_status"]
        game_balances = meta["game_balances"]
        row = db_session.query(orders).filter(orders.c.id == order_id)
        order_ticket = orm_row_to_dict(row)

        order_id = order_ticket["id"]
        user_id = order_ticket["user_id"]
        game_id = order_ticket["game_id"]
        symbol = order_ticket["symbol"]
        buy_or_sell = order_ticket["buy_or_sell"]
        quantity = order_ticket["quantity"]
        order_price = order_ticket["price"]
        order_type = order_ticket["order_type"]
        time_in_force = order_ticket["time_in_force"]
        market_price = fetch_price.delay(symbol)
        while not market_price.ready():
            continue

        if time_in_force == "day":
            if time.time() - expiration > SECONDS_IN_A_TRADING_DAY:
                table_updater(conn, order_status, order_id=order_id, timestamp=timestamp, status="expired",
                              clear_price=None)
                return

        cash_balance = get_current_game_cash_balance(conn, user_id, game_id)
        current_holding = get_current_stock_holding(conn, user_id, game_id, symbol)

        sign = 1 if buy_or_sell == "buy" else -1
        execute = False
        if (buy_or_sell == "buy" and order_type == "stop") or (buy_or_sell == "sell" and order_type == "limit"):
            if market_price >= order_price:
                execute = True

        if (buy_or_sell == "sell" and order_type == "stop") or (buy_or_sell == "buy" and order_type == "limit"):
            if market_price <= order_price:
                execute = True

        if execute:
            table_updater(conn, game_balances, user_id=user_id, game_id=game_id, timestamp=timestamp,
                          balance_type="virtual_cash", balance=cash_balance - sign * quantity * order_price)
            table_updater(conn, game_balances, user_id=user_id, game_id=game_id, timestamp=timestamp,
                          balance_type="virtual_stock", balance=current_holding + sign * quantity)
            table_updater(conn, order_status, order_id=order_id, timestamp=timestamp, status="fulfilled",
                          clear_price=market_price)
        db_session.commit()
    return


@celery.task(name="tasks.process_open_orders")
def process_open_orders():
    """Scheduled to update all orders across all games throughout the trading day
    """
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    open_orders = get_all_open_orders(engine)
    for order_id, expiration in open_orders:
        process_single_order.delay(order_id, expiration, engine)
