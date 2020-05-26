import time

from backend.config import Config
from backend.database.db import db_session
from backend.database.helpers import (
    retrieve_meta_data,
    table_updater
)
from backend.logic.games import (
    get_current_game_cash_balance,
    get_current_stock_holding,
    get_all_open_orders,
    place_order,
    get_order_ticket,
    process_order,
    get_order_expiration_status,
    get_open_game_ids,
    service_open_game,
    translate_usernames_to_ids,
    create_pending_game_status_entry,
    create_game_invites_entries,
    DEFAULT_INVITE_OPEN_WINDOW
)
from backend.logic.stock_data import (
    get_symbols_table,
    fetch_iex_price
)
from backend.tasks.celery import celery, SqlAlchemyTask
from backend.tasks.redis import rds
from sqlalchemy import create_engine, select


@celery.task(name="async_update_symbols_table", bind=True, default_retry_delay=10, base=SqlAlchemyTask)
def async_update_symbols_table(self):
    try:
        symbols_table = get_symbols_table()
        print("writing to db...")
        with db_session.connection() as conn:
            conn.execute("TRUNCATE TABLE symbols;")
            db_session.remove()

        with db_session.connection() as conn:
            symbols_table.to_sql("symbols", conn, if_exists="append", index=False)
            db_session.commit()
    except Exception as exc:
        raise self.retry(exc=exc)


@celery.task(name="async_fetch_price", bind=True)
def async_fetch_price(self, symbol):
    """For now this is just a silly wrapping step that allows us to decorate the external function into our celery tasks
    inventory. Lots of room to add future nuance here around different data providers, cache look-ups, etc.
    """
    price, timestamp = fetch_iex_price(symbol)
    return price, timestamp


@celery.task(name="async_cache_price", bind=True)
def async_cache_price(self, symbol: str, price: float, last_updated: float):
    """We'll store the last-updated price of each monitored stock in redis. In the short-term this will save us some
    unnecessary data API call.
    """
    rds.set(symbol, f"{price}_{last_updated}")


@celery.task(name="async_suggest_symbols", base=SqlAlchemyTask)
def async_suggest_symbols(text):
    to_match = f"{text.upper()}%"
    suggest_query = """
        SELECT * FROM symbols
        WHERE symbol LIKE %s OR name LIKE %s LIMIT 20;
    """

    with db_session.connection() as conn:
        symbol_suggestions = conn.execute(suggest_query, (to_match, to_match))
        db_session.remove()

    return [{"symbol": entry[1], "label": f"{entry[1]} ({entry[2]})"} for entry in symbol_suggestions]


@celery.task(name="async_add_game", bind=True, base=SqlAlchemyTask)
def async_add_game(self, game_settings):
    opened_at = time.time()
    invite_window = opened_at + DEFAULT_INVITE_OPEN_WINDOW

    metadata = retrieve_meta_data(db_session.connection())
    games = metadata.tables["games"]
    creator_id = game_settings["creator_id"]
    result = table_updater(db_session, games,
                           creator_id=creator_id,
                           title=game_settings["title"],
                           mode=game_settings["mode"],
                           duration=game_settings["duration"],
                           buy_in=game_settings["buy_in"],
                           n_rebuys=game_settings["n_rebuys"],
                           benchmark=game_settings["benchmark"],
                           side_bets_perc=game_settings["side_bets_perc"],
                           side_bets_period=game_settings["side_bets_period"],
                           invite_window=invite_window)
    game_id = result.inserted_primary_key[0]
    invited_ids = translate_usernames_to_ids(db_session, tuple(game_settings["invitees"]))
    user_ids = invited_ids + [creator_id]

    create_pending_game_status_entry(db_session, game_id, user_ids, opened_at)
    create_game_invites_entries(db_session, game_id, creator_id, user_ids, opened_at)


@celery.task(name="async_respond_to_invite", bind=True, base=SqlAlchemyTask)
def async_respond_to_invite(self, game_id, user_id, status):
    assert status in ["joined", "declined"]

    response_time = time.time()
    metadata = retrieve_meta_data(db_session.connection())
    game_invites = metadata.tables["game_invites"]
    table_updater(db_session, game_invites,
                  game_id=game_id,
                  user_id=user_id,
                  status=status,
                  timestamp=response_time)


@celery.task(name="async_service_open_games", bind=True, base=SqlAlchemyTask)
def async_service_open_games(self):
    open_game_ids = get_open_game_ids(db_session)
    for game_id in open_game_ids:
        async_service_one_open_game.delay(game_id)


@celery.task(name="async_service_one_open_game", bind=True, base=SqlAlchemyTask)
def async_service_one_open_game(self, game_id):
    service_open_game(db_session, game_id)


@celery.task(name="async_place_order", base=SqlAlchemyTask)
def async_place_order(order_ticket):
    """Placing an order involves several layers of conditional logic: is this is a buy or sell order? Stop, limit, or
    market? Do we either have the adequate cash on hand, or enough of a position in the stock for this order to be
    valid? Here an order_ticket from the frontend--along with the user_id tacked on during the API call--gets decoded,
    checked for validity, and booked. Market orders are fulfilled in the same step. Stop/limit orders are monitored on
    an ongoing basis by the celery schedule and book as their requirements are satisfies
    """
    # extract relevant data
    user_id = order_ticket["user_id"]
    game_id = order_ticket["game_id"]
    symbol = order_ticket["symbol"]
    stop_limit_price = order_ticket.get("stop_limit_price")

    cash_balance = get_current_game_cash_balance(db_session, user_id, game_id)
    current_holding = get_current_stock_holding(db_session, user_id, game_id, symbol)

    place_order(db_session, user_id, game_id, symbol, order_ticket["buy_or_sell"], cash_balance, current_holding,
                order_ticket["order_type"], order_ticket["quantity_type"], order_ticket["market_price"],
                float(order_ticket["amount"]), order_ticket["time_in_force"], stop_limit_price)


@celery.task(name="async_process_single_order", base=SqlAlchemyTask)
def async_process_single_order(order_id):
    timestamp = time.time()
    if get_order_expiration_status(db_session, order_id):
        order_status = retrieve_meta_data(db_session.connection()).tables["order_status"]
        table_updater(db_session, order_status, order_id=order_id, timestamp=timestamp, status="expired",
                      clear_price=None)
        return

    order_ticket = get_order_ticket(db_session, order_id)
    symbol = order_ticket["symbol"]
    res = async_fetch_price.delay(symbol)
    while not res.ready():
        continue

    market_price, _ = res.results
    process_order(db_session, order_ticket["game_id"], order_ticket["user_id"], symbol, order_id,
                  order_ticket["buy_or_sell"], order_ticket["order_type"], order_ticket["price"], market_price,
                  order_ticket["quantity"], timestamp)


@celery.task(name="async_process_all_open_orders", bind=True)
def async_process_all_open_orders(self):
    """Scheduled to update all orders across all games throughout the trading day
    """
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    open_orders = get_all_open_orders(db_session)
    for order_id, expiration in open_orders:
        async_process_single_order.delay(order_id, expiration, engine)


@celery.task(name="async_invite_friend", bind=True, base=SqlAlchemyTask)
def async_invite_friend(self, requester_id, invited_id):
    friends = retrieve_meta_data(db_session.connection()).tables["friends"]
    table_updater(db_session, friends, requester_id=requester_id, invited_id=invited_id, status="invited",
                  timestamp=time.time())


@celery.task(name="async_respond_to_friend_invite", bind=True, base=SqlAlchemyTask)
def async_respond_to_friend_invite(self, requester_id, invited_id, response):
    friends = retrieve_meta_data(db_session.connection()).tables["friends"]
    table_updater(db_session, friends, requester_id=requester_id, invited_id=invited_id, status=response,
                  timestamp=time.time())


@celery.task(name="async_get_friend_ids", bind=True, base=SqlAlchemyTask)
def async_get_friend_ids(self, user_id):
    with db_session.connection() as conn:
        invited_friends = conn.execute("""
            SELECT requester_id
            FROM friends 
            WHERE invited_id = %s;
        """, user_id).fetchall()

        requested_friends = conn.execute("""
            SELECT invited_id
            FROM friends
            WHERE requester_id = %s;
        """, user_id).fetchall()
        db_session.remove()

    return [x[0] for x in invited_friends + requested_friends]


@celery.task(name="async_get_friend_names", bind=True, base=SqlAlchemyTask)
def async_get_friend_names(self, user_id):
    friend_ids = async_get_friend_ids.apply(user_id)
    users = retrieve_meta_data(db_session.connetion()).tables["users"]
    invitee_ids = db_session.execute(select([users.c.username], users.c.id.in_(friend_ids))).fetchall()
    return invitee_ids


@celery.task(name="async_suggest_friends", bind=True, base=SqlAlchemyTask)
def async_suggest_friends(self, user_id, text):
    with db_session.connect() as conn:
        friend_ids = async_get_friend_ids.apply(user_id)

        suggest_query = """
            SELECT id, username FROM users
            WHERE username LIKE %s
            LIMIT 20;
        """
        friend_invite_suggestions = conn.execute(suggest_query, text)

        return [x[1] for x in friend_invite_suggestions if x[0] not in friend_ids]
