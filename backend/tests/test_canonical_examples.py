"""Canonical test cases based on real production data. As appropriate, migrate cases in from production.
"""
from backend.logic.visuals import (
    make_order_performance_table,
    serialize_and_pack_order_performance_assets
)
from backend.tests import CanonicalSplitsCase
from numpy import nan
import pandas as pd


RECORDS = [
    {'symbol': 'AAPL', 'order_label': 'AAPL/200 @ $508.74/Aug 27, 9:30', 'basis': 101748.0, 'quantity': 200.0, 'clear_price': 508.74, 'event_type': 'buy', 'fifo_balance': 200.0, 'timestamp': 1598535009.37378, 'realized_pl': 0.0, 'unrealized_pl': 0.0, 'total_pct_sold': 0.0},
    {'symbol': 'AAPL', 'order_label': 'AAPL/200 @ $508.74/Aug 27, 9:30', 'basis': 101748.0, 'quantity': nan, 'clear_price': nan, 'event_type': 'split', 'fifo_balance': 800.0, 'timestamp': 1598880600.0, 'realized_pl': 0.0, 'unrealized_pl': 368.0, 'total_pct_sold': 0.0},
    {'symbol': 'DRIP', 'order_label': 'DRIP/18900 @ $4.97/Aug 27, 9:30', 'basis': 93933.0, 'quantity': 18900.0, 'clear_price': 4.97, 'event_type': 'buy', 'fifo_balance': 18900.0, 'timestamp': 1598535007.4765, 'realized_pl': 0.0, 'unrealized_pl': 0.0, 'total_pct_sold': 0.0},
    {'symbol': 'DRIP', 'order_label': 'DRIP/18900 @ $4.97/Aug 27, 9:30', 'basis': 93933.0, 'quantity': nan, 'clear_price': nan, 'event_type': 'split', 'fifo_balance': 1890.0, 'timestamp': 1598621400.0, 'realized_pl': 0.0, 'unrealized_pl': -888.3000000000029, 'total_pct_sold': 0.0},
    {'symbol': 'DRIP', 'order_label': 'DRIP/18900 @ $4.97/Aug 27, 9:30', 'basis': 93933.0, 'quantity': 1000.0, 'clear_price': 53.7, 'event_type': 'sell', 'fifo_balance': 890.0, 'timestamp': 1599226211.78457, 'realized_pl': 4000.0, 'unrealized_pl': 3560.0, 'total_pct_sold': 0.5291005291005291},
    {'symbol': 'DRIP', 'order_label': 'DRIP/18900 @ $4.97/Aug 27, 9:30', 'basis': 93933.0, 'quantity': 890.0, 'clear_price': 56.23, 'event_type': 'sell', 'fifo_balance': 0.0, 'timestamp': 1599234333.77534, 'realized_pl': 5811.699999999997, 'unrealized_pl': 0.0, 'total_pct_sold': 1.0},
    {'symbol': 'LABD', 'order_label': 'LABD/41500 @ $3.47/Aug 27, 9:30', 'basis': 144005.0, 'quantity': 41500.0, 'clear_price': 3.47, 'event_type': 'buy', 'fifo_balance': 41500.0, 'timestamp': 1598535006.62553, 'realized_pl': 0.0, 'unrealized_pl': 0.0, 'total_pct_sold': 0.0},
    {'symbol': 'LABD', 'order_label': 'LABD/41500 @ $3.47/Aug 27, 9:30', 'basis': 144005.0, 'quantity': nan, 'clear_price': nan, 'event_type': 'split', 'fifo_balance': 2075.0, 'timestamp': 1598621400.0, 'realized_pl': 0.0, 'unrealized_pl': 2822.0, 'total_pct_sold': 0.0},
    {'symbol': 'LABD', 'order_label': 'LABD/41500 @ $3.47/Aug 27, 9:30', 'basis': 144005.0, 'quantity': 1000.0, 'clear_price': 72.0, 'event_type': 'sell', 'fifo_balance': 1075.0, 'timestamp': 1599226212.75566, 'realized_pl': 2600.0, 'unrealized_pl': 2795.0, 'total_pct_sold': 0.4819277108433735},
    {'symbol': 'LABD', 'order_label': 'LABD/41500 @ $3.47/Aug 27, 9:30', 'basis': 144005.0, 'quantity': 575.0, 'clear_price': 78.4, 'event_type': 'sell', 'fifo_balance': 500.0, 'timestamp': 1599236549.59708, 'realized_pl': 5175.0, 'unrealized_pl': 4500.0, 'total_pct_sold': 0.7590361445783133},
    {'symbol': 'LABD', 'order_label': 'LABD/41500 @ $3.47/Aug 27, 9:30', 'basis': 144005.0, 'quantity': 500.0, 'clear_price': 78.27, 'event_type': 'sell', 'fifo_balance': 0.0, 'timestamp': 1599236574.9613, 'realized_pl': 4435.0, 'unrealized_pl': 0.0, 'total_pct_sold': 1.0},
    {'symbol': 'LABD', 'order_label': 'LABD/500 @ $78.63/Sep 4, 12:22', 'basis': 39314.0, 'quantity': 500.0, 'clear_price': 78.628, 'event_type': 'buy', 'fifo_balance': 500.0, 'timestamp': 1599236560.0951, 'realized_pl': 0.0, 'unrealized_pl': 0.0, 'total_pct_sold': 0.0},
    {'symbol': 'LABD', 'order_label': 'LABD/500 @ $78.63/Sep 4, 12:22', 'basis': 39314.0, 'quantity': 500.0, 'clear_price': 78.27, 'event_type': 'sell', 'fifo_balance': 0.0, 'timestamp': 1599236587.77923, 'realized_pl': -179.0, 'unrealized_pl': 0.0, 'total_pct_sold': 1.0},
    {'symbol': 'MUTE', 'order_label': 'MUTE/21100 @ $4.13/Aug 27, 9:30', 'basis': 87143.0, 'quantity': 21100.0, 'clear_price': 4.13, 'event_type': 'buy', 'fifo_balance': 21100.0, 'timestamp': 1598535001.8686, 'realized_pl': 0.0, 'unrealized_pl': 0.0, 'total_pct_sold': 0.0},
    {'symbol': 'MUTE', 'order_label': 'MUTE/21100 @ $4.13/Aug 27, 9:30', 'basis': 87143.0, 'quantity': nan, 'clear_price': nan, 'event_type': 'split', 'fifo_balance': 2110.0, 'timestamp': 1598621400.0, 'realized_pl': 0.0, 'unrealized_pl': 2426.5, 'total_pct_sold': 0.0},
    {'symbol': 'MUTE', 'order_label': 'MUTE/21100 @ $4.13/Aug 27, 9:30', 'basis': 87143.0, 'quantity': 2110.0, 'clear_price': 43.25, 'event_type': 'sell', 'fifo_balance': 0.0, 'timestamp': 1599226216.89789, 'realized_pl': 4114.5, 'unrealized_pl': 0.0, 'total_pct_sold': 1.0},
    {'symbol': 'PASS', 'order_label': 'PASS/21100 @ $4.18/Aug 27, 9:30', 'basis': 88198.0, 'quantity': 21100.0, 'clear_price': 4.18, 'event_type': 'buy', 'fifo_balance': 21100.0, 'timestamp': 1598535003.63028, 'realized_pl': 0.0, 'unrealized_pl': 0.0, 'total_pct_sold': 0.0},
    {'symbol': 'PASS', 'order_label': 'PASS/21100 @ $4.18/Aug 27, 9:30', 'basis': 88198.0, 'quantity': nan, 'clear_price': nan, 'event_type': 'split', 'fifo_balance': 2110.0, 'timestamp': 1598621400.0, 'realized_pl': 0.0, 'unrealized_pl': 400.90000000000873, 'total_pct_sold': 0.0},
    {'symbol': 'SOXS', 'order_label': 'SOXS/30000 @ $3.53/Aug 27, 9:30', 'basis': 105900.0, 'quantity': 30000.0, 'clear_price': 3.53, 'event_type': 'buy', 'fifo_balance': 30000.0, 'timestamp': 1598535008.46027, 'realized_pl': 0.0, 'unrealized_pl': 0.0, 'total_pct_sold': 0.0},
    {'symbol': 'SOXS', 'order_label': 'SOXS/30000 @ $3.53/Aug 27, 9:30', 'basis': 105900.0, 'quantity': nan, 'clear_price': nan, 'event_type': 'split', 'fifo_balance': 2500.0, 'timestamp': 1598621400.0, 'realized_pl': 0.0, 'unrealized_pl': 1900.0, 'total_pct_sold': 0.0},
    {'symbol': 'TREX', 'order_label': 'TREX/800 @ $148.11/Aug 27, 9:30', 'basis': 118488.00000000001, 'quantity': 800.0, 'clear_price': 148.11, 'event_type': 'buy', 'fifo_balance': 800.0, 'timestamp': 1598535011.49184, 'realized_pl': 0.0, 'unrealized_pl': 0.0, 'total_pct_sold': 0.0},
    {'symbol': 'TREX', 'order_label': 'TREX/800 @ $148.11/Aug 27, 9:30', 'basis': 118488.00000000001, 'quantity': 400.0, 'clear_price': 141.0, 'event_type': 'sell', 'fifo_balance': 400.0, 'timestamp': 1599226210.52071, 'realized_pl': -2844.0000000000073, 'unrealized_pl': -2844.0000000000073, 'total_pct_sold': 0.5},
    {'symbol': 'TREX', 'order_label': 'TREX/800 @ $148.11/Aug 27, 9:30', 'basis': 118488.00000000001, 'quantity': 100.0, 'clear_price': 133.74, 'event_type': 'sell', 'fifo_balance': 300.0, 'timestamp': 1599232103.8257, 'realized_pl': -1437.0000000000018, 'unrealized_pl': -4311.000000000007, 'total_pct_sold': 0.625},
    {'symbol': 'TREX', 'order_label': 'TREX/800 @ $148.11/Aug 27, 9:30', 'basis': 118488.00000000001, 'quantity': 200.0, 'clear_price': 133.74, 'event_type': 'sell', 'fifo_balance': 100.0, 'timestamp': 1599232122.22291, 'realized_pl': -2874.0000000000036, 'unrealized_pl': -1437.0000000000018, 'total_pct_sold': 0.875},
    {'symbol': 'TREX', 'order_label': 'TREX/100 @ $133.74/Sep 4, 11:08', 'basis': 13374.0, 'quantity': 100.0, 'clear_price': 133.74, 'event_type': 'buy', 'fifo_balance': 100.0, 'timestamp': 1599232112.93018, 'realized_pl': 0.0, 'unrealized_pl': 0.0, 'total_pct_sold': 0.0},
    {'symbol': 'TSLA', 'order_label': 'TSLA/50 @ $2,185.05/Aug 27, 9:30', 'basis': 109252.25, 'quantity': 50.0, 'clear_price': 2185.045, 'event_type': 'buy', 'fifo_balance': 50.0, 'timestamp': 1598535010.25804, 'realized_pl': 0.0, 'unrealized_pl': 0.0, 'total_pct_sold': 0.0},
    {'symbol': 'TSLA', 'order_label': 'TSLA/50 @ $2,185.05/Aug 27, 9:30', 'basis': 109252.25, 'quantity': nan, 'clear_price': nan, 'event_type': 'split', 'fifo_balance': 250.0, 'timestamp': 1598880600.0, 'realized_pl': 0.0, 'unrealized_pl': 1797.75, 'total_pct_sold': 0.0},
    {'symbol': 'WEBS', 'order_label': 'WEBS/21100 @ $4.13/Aug 27, 9:30', 'basis': 87143.0, 'quantity': 21100.0, 'clear_price': 4.13, 'event_type': 'buy', 'fifo_balance': 21100.0, 'timestamp': 1598535005.66577, 'realized_pl': 0.0, 'unrealized_pl': 0.0, 'total_pct_sold': 0.0},
    {'symbol': 'WEBS', 'order_label': 'WEBS/21100 @ $4.13/Aug 27, 9:30', 'basis': 87143.0, 'quantity': nan, 'clear_price': nan, 'event_type': 'split', 'fifo_balance': 2110.0, 'timestamp': 1598621400.0, 'realized_pl': 0.0, 'unrealized_pl': 0.0, 'total_pct_sold': 0.0},
    {'symbol': 'WEBS', 'order_label': 'WEBS/21100 @ $4.13/Aug 27, 9:30', 'basis': 87143.0, 'quantity': 2110.0, 'clear_price': 43.55, 'event_type': 'sell', 'fifo_balance': 0.0, 'timestamp': 1599226214.42921, 'realized_pl': 4747.5, 'unrealized_pl': 0.0, 'total_pct_sold': 1.0},
]


class TestSplits(CanonicalSplitsCase):
    """Stock splits introduce a lot of complexity into the order performance charting and calculating realized /
    unrealized P & L. This canonical test makes sure that we're nailing that  logic, and also does some values testing
    of the asset """

    def test_splits(self):
        df = make_order_performance_table(self.game_id, self.user_id)
        pd.testing.assert_frame_equal(df, pd.DataFrame(RECORDS))
        serialize_and_pack_order_performance_assets(self.game_id, self.user_id)
