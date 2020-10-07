"""Canonical test cases based on real production data. As appropriate, migrate cases in from production.
"""
from freezegun import freeze_time
from numpy import nan
import pandas as pd

from backend.tasks import s3_cache
from backend.tasks.redis import rds
from backend.logic.base import posix_to_datetime
from backend.logic.visuals import (
    make_order_performance_table,
    serialize_and_pack_order_performance_assets,
    ORDER_PERF_CHART_PREFIX,
    FULFILLED_ORDER_PREFIX,
    serialize_and_pack_rankings,
    PLAYER_RANK_PREFIX,
    THREE_MONTH_RETURN_PREFIX
)
from backend.tests import (
    CanonicalSplitsCase,
    StockbetsRatingCase
)
from backend.logic.metrics import update_ratings
from backend.logic.auth import create_jwt
from backend.tests import HOST_URL


class TestSplits(CanonicalSplitsCase):
    """Stock splits introduce a lot of complexity into the order performance charting and calculating realized /
    unrealized P & L. This canonical test makes sure that we're nailing that  logic, and also does some values testing
    of the asset """

    RECORDS = [
        {'symbol': 'AAPL', 'order_id': 1149.0, 'order_label': 'AAPL/200 @ $508.74/Aug 27, 9:30', 'basis': 101748.0, 'quantity': 200.0, 'clear_price': 508.74, 'event_type': 'buy', 'fifo_balance': 200.0, 'timestamp': 1598535009.37378, 'realized_pl': 0.0, 'unrealized_pl': 0.0, 'total_pct_sold': 0.0},
        {'symbol': 'AAPL', 'order_id': nan, 'order_label': 'AAPL/200 @ $508.74/Aug 27, 9:30', 'basis': 101748.0, 'quantity': nan, 'clear_price': nan, 'event_type': 'split', 'fifo_balance': 800.0, 'timestamp': 1598880600.0, 'realized_pl': 0.0, 'unrealized_pl': 368.0, 'total_pct_sold': 0.0},
        {'symbol': 'DRIP', 'order_id': 1147.0, 'order_label': 'DRIP/18900 @ $4.97/Aug 27, 9:30', 'basis': 93933.0, 'quantity': 18900.0, 'clear_price': 4.97, 'event_type': 'buy', 'fifo_balance': 18900.0, 'timestamp': 1598535007.4765, 'realized_pl': 0.0, 'unrealized_pl': 0.0, 'total_pct_sold': 0.0},
        {'symbol': 'DRIP', 'order_id': nan, 'order_label': 'DRIP/18900 @ $4.97/Aug 27, 9:30', 'basis': 93933.0, 'quantity': nan, 'clear_price': nan, 'event_type': 'split', 'fifo_balance': 1890.0, 'timestamp': 1598621400.0, 'realized_pl': 0.0, 'unrealized_pl': -888.3000000000029, 'total_pct_sold': 0.0},
        {'symbol': 'DRIP', 'order_id': 1279.0, 'order_label': 'DRIP/18900 @ $4.97/Aug 27, 9:30', 'basis': 93933.0, 'quantity': 1000.0, 'clear_price': 53.7, 'event_type': 'sell', 'fifo_balance': 890.0, 'timestamp': 1599226211.78457, 'realized_pl': 4000.0, 'unrealized_pl': 3560.0, 'total_pct_sold': 0.5291005291005291},
        {'symbol': 'DRIP', 'order_id': 1288.0, 'order_label': 'DRIP/18900 @ $4.97/Aug 27, 9:30', 'basis': 93933.0, 'quantity': 890.0, 'clear_price': 56.23, 'event_type': 'sell', 'fifo_balance': 0.0, 'timestamp': 1599234333.77534, 'realized_pl': 5811.699999999997, 'unrealized_pl': 0.0, 'total_pct_sold': 1.0},
        {'symbol': 'LABD', 'order_id': 1146.0, 'order_label': 'LABD/41500 @ $3.47/Aug 27, 9:30', 'basis': 144005.0, 'quantity': 41500.0, 'clear_price': 3.47, 'event_type': 'buy', 'fifo_balance': 41500.0, 'timestamp': 1598535006.62553, 'realized_pl': 0.0, 'unrealized_pl': 0.0, 'total_pct_sold': 0.0},
        {'symbol': 'LABD', 'order_id': nan, 'order_label': 'LABD/41500 @ $3.47/Aug 27, 9:30', 'basis': 144005.0, 'quantity': nan, 'clear_price': nan, 'event_type': 'split', 'fifo_balance': 2075.0, 'timestamp': 1598621400.0, 'realized_pl': 0.0, 'unrealized_pl': 2822.0, 'total_pct_sold': 0.0},
        {'symbol': 'LABD', 'order_id': 1280.0, 'order_label': 'LABD/41500 @ $3.47/Aug 27, 9:30', 'basis': 144005.0, 'quantity': 1000.0, 'clear_price': 72.0, 'event_type': 'sell', 'fifo_balance': 1075.0, 'timestamp': 1599226212.75566, 'realized_pl': 2600.0, 'unrealized_pl': 2795.0, 'total_pct_sold': 0.4819277108433735},
        {'symbol': 'LABD', 'order_id': 1289.0, 'order_label': 'LABD/41500 @ $3.47/Aug 27, 9:30', 'basis': 144005.0, 'quantity': 575.0, 'clear_price': 78.4, 'event_type': 'sell', 'fifo_balance': 500.0, 'timestamp': 1599236549.59708, 'realized_pl': 5175.0, 'unrealized_pl': 4500.0, 'total_pct_sold': 0.7590361445783133},
        {'symbol': 'LABD', 'order_id': 1291.0, 'order_label': 'LABD/41500 @ $3.47/Aug 27, 9:30', 'basis': 144005.0, 'quantity': 500.0, 'clear_price': 78.27, 'event_type': 'sell', 'fifo_balance': 0.0, 'timestamp': 1599236574.9613, 'realized_pl': 4435.0, 'unrealized_pl': 0.0, 'total_pct_sold': 1.0},
        {'symbol': 'LABD', 'order_id': 1290.0, 'order_label': 'LABD/500 @ $78.63/Sep 4, 12:22', 'basis': 39314.0, 'quantity': 500.0, 'clear_price': 78.628, 'event_type': 'buy', 'fifo_balance': 500.0, 'timestamp': 1599236560.0951, 'realized_pl': 0.0, 'unrealized_pl': 0.0, 'total_pct_sold': 0.0},
        {'symbol': 'LABD', 'order_id': 1292.0, 'order_label': 'LABD/500 @ $78.63/Sep 4, 12:22', 'basis': 39314.0, 'quantity': 500.0, 'clear_price': 78.27, 'event_type': 'sell', 'fifo_balance': 0.0, 'timestamp': 1599236587.77923, 'realized_pl': -179.0, 'unrealized_pl': 0.0, 'total_pct_sold': 1.0},
        {'symbol': 'MUTE', 'order_id': 1143.0, 'order_label': 'MUTE/21100 @ $4.13/Aug 27, 9:30', 'basis': 87143.0, 'quantity': 21100.0, 'clear_price': 4.13, 'event_type': 'buy', 'fifo_balance': 21100.0, 'timestamp': 1598535001.8686, 'realized_pl': 0.0, 'unrealized_pl': 0.0, 'total_pct_sold': 0.0},
        {'symbol': 'MUTE', 'order_id': nan, 'order_label': 'MUTE/21100 @ $4.13/Aug 27, 9:30', 'basis': 87143.0, 'quantity': nan, 'clear_price': nan, 'event_type': 'split', 'fifo_balance': 2110.0, 'timestamp': 1598621400.0, 'realized_pl': 0.0, 'unrealized_pl': 2426.5, 'total_pct_sold': 0.0},
        {'symbol': 'MUTE', 'order_id': 1283.0, 'order_label': 'MUTE/21100 @ $4.13/Aug 27, 9:30', 'basis': 87143.0, 'quantity': 2110.0, 'clear_price': 43.25, 'event_type': 'sell', 'fifo_balance': 0.0, 'timestamp': 1599226216.89789, 'realized_pl': 4114.5, 'unrealized_pl': 0.0, 'total_pct_sold': 1.0},
        {'symbol': 'PASS', 'order_id': 1144.0, 'order_label': 'PASS/21100 @ $4.18/Aug 27, 9:30', 'basis': 88198.0, 'quantity': 21100.0, 'clear_price': 4.18, 'event_type': 'buy', 'fifo_balance': 21100.0, 'timestamp': 1598535003.63028, 'realized_pl': 0.0, 'unrealized_pl': 0.0, 'total_pct_sold': 0.0},
        {'symbol': 'PASS', 'order_id': nan, 'order_label': 'PASS/21100 @ $4.18/Aug 27, 9:30', 'basis': 88198.0, 'quantity': nan, 'clear_price': nan, 'event_type': 'split', 'fifo_balance': 2110.0, 'timestamp': 1598621400.0, 'realized_pl': 0.0, 'unrealized_pl': 400.90000000000873, 'total_pct_sold': 0.0},
        {'symbol': 'SOXS', 'order_id': 1148.0, 'order_label': 'SOXS/30000 @ $3.53/Aug 27, 9:30', 'basis': 105900.0, 'quantity': 30000.0, 'clear_price': 3.53, 'event_type': 'buy', 'fifo_balance': 30000.0, 'timestamp': 1598535008.46027, 'realized_pl': 0.0, 'unrealized_pl': 0.0, 'total_pct_sold': 0.0},
        {'symbol': 'SOXS', 'order_id': nan, 'order_label': 'SOXS/30000 @ $3.53/Aug 27, 9:30', 'basis': 105900.0, 'quantity': nan, 'clear_price': nan, 'event_type': 'split', 'fifo_balance': 2500.0, 'timestamp': 1598621400.0, 'realized_pl': 0.0, 'unrealized_pl': 1900.0, 'total_pct_sold': 0.0},
        {'symbol': 'TREX', 'order_id': 1151.0, 'order_label': 'TREX/800 @ $148.11/Aug 27, 9:30', 'basis': 118488.00000000001, 'quantity': 800.0, 'clear_price': 148.11, 'event_type': 'buy', 'fifo_balance': 800.0, 'timestamp': 1598535011.49184, 'realized_pl': 0.0, 'unrealized_pl': 0.0, 'total_pct_sold': 0.0},
        {'symbol': 'TREX', 'order_id': 1278.0, 'order_label': 'TREX/800 @ $148.11/Aug 27, 9:30', 'basis': 118488.00000000001, 'quantity': 400.0, 'clear_price': 141.0, 'event_type': 'sell', 'fifo_balance': 400.0, 'timestamp': 1599226210.52071, 'realized_pl': -2844.0000000000073, 'unrealized_pl': -2844.0000000000073, 'total_pct_sold': 0.5},
        {'symbol': 'TREX', 'order_id': 1285.0, 'order_label': 'TREX/800 @ $148.11/Aug 27, 9:30', 'basis': 118488.00000000001, 'quantity': 100.0, 'clear_price': 133.74, 'event_type': 'sell', 'fifo_balance': 300.0, 'timestamp': 1599232103.8257, 'realized_pl': -1437.0000000000018, 'unrealized_pl': -4311.000000000007, 'total_pct_sold': 0.625},
        {'symbol': 'TREX', 'order_id': 1287.0, 'order_label': 'TREX/800 @ $148.11/Aug 27, 9:30', 'basis': 118488.00000000001, 'quantity': 200.0, 'clear_price': 133.74, 'event_type': 'sell', 'fifo_balance': 100.0, 'timestamp': 1599232122.22291, 'realized_pl': -2874.0000000000036, 'unrealized_pl': -1437.0000000000018, 'total_pct_sold': 0.875},
        {'symbol': 'TREX', 'order_id': 1286.0, 'order_label': 'TREX/100 @ $133.74/Sep 4, 11:08', 'basis': 13374.0, 'quantity': 100.0, 'clear_price': 133.74, 'event_type': 'buy', 'fifo_balance': 100.0, 'timestamp': 1599232112.93018, 'realized_pl': 0.0, 'unrealized_pl': 0.0, 'total_pct_sold': 0.0},
        {'symbol': 'TSLA', 'order_id': 1150.0, 'order_label': 'TSLA/50 @ $2,185.05/Aug 27, 9:30', 'basis': 109252.25, 'quantity': 50.0, 'clear_price': 2185.045, 'event_type': 'buy', 'fifo_balance': 50.0, 'timestamp': 1598535010.25804, 'realized_pl': 0.0, 'unrealized_pl': 0.0, 'total_pct_sold': 0.0},
        {'symbol': 'TSLA', 'order_id': nan, 'order_label': 'TSLA/50 @ $2,185.05/Aug 27, 9:30', 'basis': 109252.25, 'quantity': nan, 'clear_price': nan, 'event_type': 'split', 'fifo_balance': 250.0, 'timestamp': 1598880600.0, 'realized_pl': 0.0, 'unrealized_pl': 1797.75, 'total_pct_sold': 0.0},
        {'symbol': 'WEBS', 'order_id': 1145.0, 'order_label': 'WEBS/21100 @ $4.13/Aug 27, 9:30', 'basis': 87143.0, 'quantity': 21100.0, 'clear_price': 4.13, 'event_type': 'buy', 'fifo_balance': 21100.0, 'timestamp': 1598535005.66577, 'realized_pl': 0.0, 'unrealized_pl': 0.0, 'total_pct_sold': 0.0},
        {'symbol': 'WEBS', 'order_id': nan, 'order_label': 'WEBS/21100 @ $4.13/Aug 27, 9:30', 'basis': 87143.0, 'quantity': nan, 'clear_price': nan, 'event_type': 'split', 'fifo_balance': 2110.0, 'timestamp': 1598621400.0, 'realized_pl': 0.0, 'unrealized_pl': 0.0, 'total_pct_sold': 0.0},
        {'symbol': 'WEBS', 'order_id': 1282.0, 'order_label': 'WEBS/21100 @ $4.13/Aug 27, 9:30', 'basis': 87143.0, 'quantity': 2110.0, 'clear_price': 43.55, 'event_type': 'sell', 'fifo_balance': 0.0, 'timestamp': 1599226214.42921, 'realized_pl': 4747.5, 'unrealized_pl': 0.0, 'total_pct_sold': 1.0}
    ]

    def test_splits(self):
        df = make_order_performance_table(self.game_id, self.user_id)
        pd.testing.assert_frame_equal(df, pd.DataFrame(self.RECORDS))
        serialize_and_pack_order_performance_assets(self.game_id, self.user_id)
        perf_table = s3_cache.unpack_s3_json(f"{self.game_id}/{self.user_id}/{FULFILLED_ORDER_PREFIX}")
        perf_chart = s3_cache.unpack_s3_json(f"{self.game_id}/{self.user_id}/{ORDER_PERF_CHART_PREFIX}")
        perf_table_df = pd.DataFrame(perf_table["data"])
        self.assertEqual(perf_table_df.shape, (22, 13))
        buy_perf_entries = [x for x in perf_table["data"] if x["event_type"] == "buy"]
        order_labels_table = set([x["order_label"] for x in buy_perf_entries])
        order_labels_chart = set([x["label"] for x in perf_chart["datasets"]])
        self.assertEqual(order_labels_chart, order_labels_table)
        for label in order_labels_table:
            table_entry = [x for x in buy_perf_entries if x["order_label"] == label][0]
            chart_entry = [x for x in perf_chart["datasets"] if x["label"] == label][0]
            self.assertEqual(table_entry["color"], chart_entry["backgroundColor"])


class TestStockbetsRanking(StockbetsRatingCase):
    """Test stockbets ratings updates following a decent-sized multiplayer game"""

    maxDiff = None

    RECORDS = [
        {'id': 1, 'user_id': 1.0, 'index_symbol': None, 'game_id': None, 'rating': 1000.0, 'update_type': 'sign_up', 'timestamp': 1591402922.88987, 'basis': 0.0, 'n_games': 0, 'total_return': 0.0},
        {'id': 10, 'user_id': 10.0, 'index_symbol': None, 'game_id': None, 'rating': 1000.0, 'update_type': 'sign_up', 'timestamp': 1592102702.01045, 'basis': 0.0, 'n_games': 0, 'total_return': 0.0},
        {'id': 28, 'user_id': 28.0, 'index_symbol': None, 'game_id': None, 'rating': 1000.0, 'update_type': 'sign_up', 'timestamp': 1592515077.34491, 'basis': 0.0, 'n_games': 0, 'total_return': 0.0},
        {'id': 29, 'user_id': 29.0, 'index_symbol': None, 'game_id': None, 'rating': 1000.0, 'update_type': 'sign_up', 'timestamp': 1592516128.51439, 'basis': 0.0, 'n_games': 0, 'total_return': 0.0},
        {'id': 86, 'user_id': 44.0, 'index_symbol': None, 'game_id': None, 'rating': 1000.0, 'update_type': 'sign_up', 'timestamp': 1595394720.4184, 'basis': 0.0, 'n_games': 0, 'total_return': 0.0},
        {'id': 87, 'user_id': 45.0, 'index_symbol': None, 'game_id': None, 'rating': 1000.0, 'update_type': 'sign_up', 'timestamp': 1595423428.28603, 'basis': 0.0, 'n_games': 0, 'total_return': 0.0},
        {'id': 110, 'user_id': 55.0, 'index_symbol': None, 'game_id': None, 'rating': 1000.0, 'update_type': 'sign_up', 'timestamp': 1595958906.4312, 'basis': 0.0, 'n_games': 0, 'total_return': 0.0},
        {'id': 111, 'user_id': nan, 'index_symbol': '^IXIC', 'game_id': None, 'rating': 1000.0, 'update_type': 'sign_up', 'timestamp': -99.0, 'basis': 0.0, 'n_games': 0, 'total_return': 0.0},
        {'id': 112, 'user_id': nan, 'index_symbol': '^GSPC', 'game_id': None, 'rating': 1000.0, 'update_type': 'sign_up', 'timestamp': -99.0, 'basis': 0.0, 'n_games': 0, 'total_return': 0.0},
        {'id': 113, 'user_id': nan, 'index_symbol': '^DJI', 'game_id': None, 'rating': 1000.0, 'update_type': 'sign_up', 'timestamp': -99.0, 'basis': 0.0, 'n_games': 0, 'total_return': 0.0},
        {'id': 114, 'user_id': 1.0, 'index_symbol': None, 'game_id': '47', 'rating': 1144.0, 'update_type': 'game_end', 'timestamp': 1599854400.0, 'basis': 1000000.0, 'n_games': 1, 'total_return': 0.0762641150000003},
        {'id': 115, 'user_id': 10.0, 'index_symbol': None, 'game_id': '47', 'rating': 920.0, 'update_type': 'game_end', 'timestamp': 1599854400.0, 'basis': 1000000.0, 'n_games': 1, 'total_return': -0.0165752899999999},
        {'id': 116, 'user_id': 28.0, 'index_symbol': None, 'game_id': '47', 'rating': 952.0, 'update_type': 'game_end', 'timestamp': 1599854400.0, 'basis': 1000000.0, 'n_games': 1, 'total_return': 0.0},
        {'id': 117, 'user_id': 29.0, 'index_symbol': None, 'game_id': '47', 'rating': 856.0, 'update_type': 'game_end', 'timestamp': 1599854400.0, 'basis': 1000000.0, 'n_games': 1, 'total_return': -0.095518835},
        {'id': 118, 'user_id': 44.0, 'index_symbol': None, 'game_id': '47', 'rating': 888.0, 'update_type': 'game_end', 'timestamp': 1599854400.0, 'basis': 1000000.0, 'n_games': 1, 'total_return': -0.0240974450000001},
        {'id': 119, 'user_id': 45.0, 'index_symbol': None, 'game_id': '47', 'rating': 1016.0, 'update_type': 'game_end', 'timestamp': 1599854400.0, 'basis': 1000000.0, 'n_games': 1, 'total_return': 0.01191425},
        {'id': 120, 'user_id': 55.0, 'index_symbol': None, 'game_id': '47', 'rating': 984.0, 'update_type': 'game_end', 'timestamp': 1599854400.0, 'basis': 1000000.0, 'n_games': 1, 'total_return': 9.66199999998807e-05},
        {'id': 121, 'user_id': nan, 'index_symbol': '^DJI', 'game_id': '47', 'rating': 1112.0, 'update_type': 'game_end', 'timestamp': 1599854400.0, 'basis': 1000000.0, 'n_games': 1, 'total_return': 0.0403694553583551},
        {'id': 122, 'user_id': nan, 'index_symbol': '^GSPC', 'game_id': '47', 'rating': 1080.0, 'update_type': 'game_end', 'timestamp': 1599854400.0, 'basis': 1000000.0, 'n_games': 1, 'total_return': 0.0313045035144639},
        {'id': 123, 'user_id': nan, 'index_symbol': '^IXIC', 'game_id': '47', 'rating': 1048.0, 'update_type': 'game_end', 'timestamp': 1599854400.0, 'basis': 1000000.0, 'n_games': 1, 'total_return': 0.030142483456657}
    ]

    LEADERBOARD = [
        {'username': 'aaron', 'user_id': 1.0, 'rating': 1144, 'profile_pic': 'https://s3.amazonaws.com/stockbets-public/profile_pics/c0f0bc6489851026b29b0e1e0e60ece21daf93632347a44f600dc5ce', 'n_games': 1, 'three_month_return': 0.0762641150000003},
        {'username': 'Dow Jones', 'user_id': None, 'rating': 1112, 'profile_pic': 'https://stockbets-public.s3.amazonaws.com/profile_pics/8bd8ec5f6126dbceabe5aae0b255b50dcdf09b3128cea8f53e8eb091', 'n_games': 1, 'three_month_return': 0.0403694553583551},
        {'username': 'S&P 500', 'user_id': None, 'rating': 1080, 'profile_pic': 'https://stockbets-public.s3.amazonaws.com/profile_pics/fe2862aca264a58ef2f8fb2d22fa8d4dd112fd06bb3e8bf2bb8bddb6', 'n_games': 1, 'three_month_return': 0.0313045035144639},
        {'username': 'NASDAQ', 'user_id': None, 'rating': 1048, 'profile_pic': 'https://stockbets-public.s3.amazonaws.com/profile_pics/044c7859dc114c52135ad159fcb7b817ad04b5a3c44c788672796b9d', 'n_games': 1, 'three_month_return': 0.030142483456657},
        {'username': 'arjd2', 'user_id': 45.0, 'rating': 1016, 'profile_pic': 'https://s3.amazonaws.com/stockbets-public/profile_pics/aefac8aa916dccabbf7b444e5a38436d517437f37c3a981f51f68c47', 'n_games': 1, 'three_month_return': 0.01191425},
        {'username': 'Ando', 'user_id': 55.0, 'rating': 984, 'profile_pic': 'https://s3.amazonaws.com/stockbets-public/profile_pics/8b7546390be79ba37a3f31d07caac05fcb0f6deb98f7ff34bb75cd74', 'n_games': 1, 'three_month_return': 9.66199999998807e-05},
        {'username': 'Memo', 'user_id': 28.0, 'rating': 952, 'profile_pic': 'https://s3.amazonaws.com/stockbets-public/profile_pics/1251754a5111216d995e8c9408fd5699a8f73a2117cd2c52143ffd38', 'n_games': 1, 'three_month_return': 0.0},
        {'username': 'Erik the Stock Fish', 'user_id': 10.0, 'rating': 920, 'profile_pic': 'https://s3.amazonaws.com/stockbets-public/profile_pics/50ff504bc91aecd2c942758b8adc6c9616ab0ce0951f019ab44571f0', 'n_games': 1, 'three_month_return': -0.0165752899999999},
        {'username': 'Matobarato', 'user_id': 44.0, 'rating': 888, 'profile_pic': 'https://s3.amazonaws.com/stockbets-public/profile_pics/2321842dbba174eeaf8f75cd2b5798dda2d2be9f321ce5b98533cd48', 'n_games': 1, 'three_month_return': -0.0240974450000001},
        {'username': 'Jeanvaljean56', 'user_id': 29.0, 'rating': 856, 'profile_pic': 'https://s3.amazonaws.com/stockbets-public/profile_pics/4f6199cd963305ef8cb6154956ff875dec86bff210d963b1dccc3263', 'n_games': 1, 'three_month_return': -0.095518835}
    ]

    @freeze_time(posix_to_datetime(1601950823.7715478))
    def test_stockbets_ranking(self):
        update_ratings(self.game_id)
        with self.engine.connect() as conn:
            df = pd.read_sql("SELECT * FROM stockbets_rating", conn)
        pd.testing.assert_frame_equal(df, pd.DataFrame(self.RECORDS))

        # make the public rankings JSON
        serialize_and_pack_rankings()

        session_token = create_jwt("me@example.com", 1, "aaron")
        res = self.requests_session.post(f"{HOST_URL}/public_leaderboard", cookies={"session_token": session_token},
                                         verify=False)
        self.assertEqual(res.json(), self.LEADERBOARD)
        res = self.requests_session.post(f"{HOST_URL}/home", cookies={"session_token": session_token}, verify=False)
        test_user_rank = float(rds.get(f"{PLAYER_RANK_PREFIX}_1"))
        test_user_return = float(rds.get(f"{THREE_MONTH_RETURN_PREFIX}_1"))
        self.assertEqual(res.json()["rating"], test_user_rank)
        self.assertEqual(test_user_rank, 1144.0)
        self.assertEqual(res.json()["three_month_return"], test_user_return)
        self.assertEqual(test_user_return, 0.0762641150000003)
