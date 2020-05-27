"""Logic for rendering visual asset data and returning to frontend
"""
import pandas as pd
from sqlalchemy.orm.scoping import scoped_session
from typing import List


def get_all_game_users(db_sesssion: scoped_session, game_id: int) -> List[int]:
    pass


def get_user_balance_history(db_session: scoped_session, game_id: int, user_id: str) -> pd.DataFrame:
    """Extracts a running record of a user's balances through time.
    """
    pass


def append_price_data_to_balances(db_session: scoped_session, user_balance_history: pd.DataFrame) -> pd.DataFrame:
    pass


def build_portfolio_comps(db_session: scoped_session, game_id) -> pd.DataFrame:
    pass
