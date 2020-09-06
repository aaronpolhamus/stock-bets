"""Canonical test cases based on real production data. As appropriate, migrate cases in from production.
"""
from backend.logic.visuals import (
    make_order_performance_table,
    serialize_and_pack_order_performance_assets
)
from backend.tests import CanonicalSplitsCase
from pandas import Timestamp
import pandas as pd


RECORDS = [
    {'symbol': 'AAPL', 'order_label': 'AAPL/200 @ $508.74/Aug 27, 9:30', 'event_type': 'buy', 'balance': 200.0,
     'basis': 101748.0, 'timestamp': Timestamp('2020-08-27 09:30:09.373780-0400', tz='America/New_York'),
     'realized_pl': 0.0, 'unrealized_pl': 0.0, 'total_pct_sold': 0.0},
    {'symbol': 'AAPL', 'order_label': 'AAPL/200 @ $508.74/Aug 27, 9:30', 'event_type': 'split', 'balance': 800.0,
     'basis': 101748.0, 'timestamp': Timestamp('2020-08-31 09:30:00-0400', tz='America/New_York'), 'realized_pl': 0.0,
     'unrealized_pl': 368.0, 'total_pct_sold': 0.0},
    {'symbol': 'DRIP', 'order_label': 'DRIP/18900 @ $4.97/Aug 27, 9:30', 'event_type': 'buy', 'balance': 18900.0,
     'basis': 93933.0, 'timestamp': Timestamp('2020-08-27 09:30:07.476500-0400', tz='America/New_York'),
     'realized_pl': 0.0, 'unrealized_pl': 0.0, 'total_pct_sold': 0.0},
    {'symbol': 'DRIP', 'order_label': 'DRIP/18900 @ $4.97/Aug 27, 9:30', 'event_type': 'split', 'balance': 1890.0,
     'basis': 93933.0, 'timestamp': Timestamp('2020-08-28 09:30:00-0400', tz='America/New_York'), 'realized_pl': 0.0,
     'unrealized_pl': -888.3000000000029, 'total_pct_sold': 0.0},
    {'symbol': 'DRIP', 'order_label': 'DRIP/18900 @ $4.97/Aug 27, 9:30', 'event_type': 'sell', 'balance': 890.0,
     'basis': 93933.0, 'timestamp': Timestamp('2020-09-04 09:30:11.784570-0400', tz='America/New_York'),
     'realized_pl': 4000.0, 'unrealized_pl': 3560.0, 'total_pct_sold': 0.5291005291005291},
    {'symbol': 'DRIP', 'order_label': 'DRIP/18900 @ $4.97/Aug 27, 9:30', 'event_type': 'sell', 'balance': 0.0,
     'basis': 93933.0, 'timestamp': Timestamp('2020-09-04 11:45:33.775340-0400', tz='America/New_York'),
     'realized_pl': 5811.699999999997, 'unrealized_pl': 0.0, 'total_pct_sold': 1.0},
    {'symbol': 'LABD', 'order_label': 'LABD/41500 @ $3.47/Aug 27, 9:30', 'event_type': 'buy', 'balance': 41500.0,
     'basis': 144005.0, 'timestamp': Timestamp('2020-08-27 09:30:06.625530-0400', tz='America/New_York'),
     'realized_pl': 0.0, 'unrealized_pl': 0.0, 'total_pct_sold': 0.0},
    {'symbol': 'LABD', 'order_label': 'LABD/41500 @ $3.47/Aug 27, 9:30', 'event_type': 'split', 'balance': 2075.0,
     'basis': 144005.0, 'timestamp': Timestamp('2020-08-28 09:30:00-0400', tz='America/New_York'), 'realized_pl': 0.0,
     'unrealized_pl': 2822.0, 'total_pct_sold': 0.0},
    {'symbol': 'LABD', 'order_label': 'LABD/41500 @ $3.47/Aug 27, 9:30', 'event_type': 'sell', 'balance': 1075.0,
     'basis': 144005.0, 'timestamp': Timestamp('2020-09-04 09:30:12.755660-0400', tz='America/New_York'),
     'realized_pl': 2600.0, 'unrealized_pl': 2795.0, 'total_pct_sold': 0.4819277108433735},
    {'symbol': 'LABD', 'order_label': 'LABD/41500 @ $3.47/Aug 27, 9:30', 'event_type': 'sell', 'balance': 500.0,
     'basis': 144005.0, 'timestamp': Timestamp('2020-09-04 12:22:29.597080-0400', tz='America/New_York'),
     'realized_pl': 5175.0, 'unrealized_pl': 4500.0, 'total_pct_sold': 0.7590361445783133},
    {'symbol': 'LABD', 'order_label': 'LABD/41500 @ $3.47/Aug 27, 9:30', 'event_type': 'sell', 'balance': 0.0,
     'basis': 144005.0, 'timestamp': Timestamp('2020-09-04 12:22:54.961300-0400', tz='America/New_York'),
     'realized_pl': 4435.0, 'unrealized_pl': 0.0, 'total_pct_sold': 1.0},
    {'symbol': 'LABD', 'order_label': 'LABD/500 @ $78.63/Sep 4, 12:22', 'event_type': 'buy', 'balance': 500.0,
     'basis': 39314.0, 'timestamp': Timestamp('2020-09-04 12:22:40.095100-0400', tz='America/New_York'),
     'realized_pl': 0.0, 'unrealized_pl': 0.0, 'total_pct_sold': 0.0},
    {'symbol': 'LABD', 'order_label': 'LABD/500 @ $78.63/Sep 4, 12:22', 'event_type': 'sell', 'balance': 0.0,
     'basis': 39314.0, 'timestamp': Timestamp('2020-09-04 12:23:07.779230-0400', tz='America/New_York'),
     'realized_pl': -179.0, 'unrealized_pl': 0.0, 'total_pct_sold': 1.0},
    {'symbol': 'MUTE', 'order_label': 'MUTE/21100 @ $4.13/Aug 27, 9:30', 'event_type': 'buy', 'balance': 21100.0,
     'basis': 87143.0, 'timestamp': Timestamp('2020-08-27 09:30:01.868600-0400', tz='America/New_York'),
     'realized_pl': 0.0, 'unrealized_pl': 0.0, 'total_pct_sold': 0.0},
    {'symbol': 'MUTE', 'order_label': 'MUTE/21100 @ $4.13/Aug 27, 9:30', 'event_type': 'split', 'balance': 2110.0,
     'basis': 87143.0, 'timestamp': Timestamp('2020-08-28 09:30:00-0400', tz='America/New_York'), 'realized_pl': 0.0,
     'unrealized_pl': 2426.5, 'total_pct_sold': 0.0},
    {'symbol': 'MUTE', 'order_label': 'MUTE/21100 @ $4.13/Aug 27, 9:30', 'event_type': 'sell', 'balance': 0.0,
     'basis': 87143.0, 'timestamp': Timestamp('2020-09-04 09:30:16.897890-0400', tz='America/New_York'),
     'realized_pl': 4114.5, 'unrealized_pl': 0.0, 'total_pct_sold': 1.0},
    {'symbol': 'PASS', 'order_label': 'PASS/21100 @ $4.18/Aug 27, 9:30', 'event_type': 'buy', 'balance': 21100.0,
     'basis': 88198.0, 'timestamp': Timestamp('2020-08-27 09:30:03.630280-0400', tz='America/New_York'),
     'realized_pl': 0.0, 'unrealized_pl': 0.0, 'total_pct_sold': 0.0},
    {'symbol': 'PASS', 'order_label': 'PASS/21100 @ $4.18/Aug 27, 9:30', 'event_type': 'split', 'balance': 2110.0,
     'basis': 88198.0, 'timestamp': Timestamp('2020-08-28 09:30:00-0400', tz='America/New_York'), 'realized_pl': 0.0,
     'unrealized_pl': 400.90000000000873, 'total_pct_sold': 0.0},
    {'symbol': 'SOXS', 'order_label': 'SOXS/30000 @ $3.53/Aug 27, 9:30', 'event_type': 'buy', 'balance': 30000.0,
     'basis': 105900.0, 'timestamp': Timestamp('2020-08-27 09:30:08.460270-0400', tz='America/New_York'),
     'realized_pl': 0.0, 'unrealized_pl': 0.0, 'total_pct_sold': 0.0},
    {'symbol': 'SOXS', 'order_label': 'SOXS/30000 @ $3.53/Aug 27, 9:30', 'event_type': 'split', 'balance': 2500.0,
     'basis': 105900.0, 'timestamp': Timestamp('2020-08-28 09:30:00-0400', tz='America/New_York'), 'realized_pl': 0.0,
     'unrealized_pl': 1900.0, 'total_pct_sold': 0.0},
    {'symbol': 'TREX', 'order_label': 'TREX/800 @ $148.11/Aug 27, 9:30', 'event_type': 'buy', 'balance': 800.0,
     'basis': 118488.00000000001, 'timestamp': Timestamp('2020-08-27 09:30:11.491840-0400', tz='America/New_York'),
     'realized_pl': 0.0, 'unrealized_pl': 0.0, 'total_pct_sold': 0.0},
    {'symbol': 'TREX', 'order_label': 'TREX/800 @ $148.11/Aug 27, 9:30', 'event_type': 'sell', 'balance': 400.0,
     'basis': 118488.00000000001, 'timestamp': Timestamp('2020-09-04 09:30:10.520710-0400', tz='America/New_York'),
     'realized_pl': -2844.0000000000073, 'unrealized_pl': -2844.0000000000073, 'total_pct_sold': 0.5},
    {'symbol': 'TREX', 'order_label': 'TREX/800 @ $148.11/Aug 27, 9:30', 'event_type': 'sell', 'balance': 300.0,
     'basis': 118488.00000000001, 'timestamp': Timestamp('2020-09-04 11:08:23.825700-0400', tz='America/New_York'),
     'realized_pl': -1437.0000000000018, 'unrealized_pl': -4311.000000000007, 'total_pct_sold': 0.625},
    {'symbol': 'TREX', 'order_label': 'TREX/800 @ $148.11/Aug 27, 9:30', 'event_type': 'sell', 'balance': 100.0,
     'basis': 118488.00000000001, 'timestamp': Timestamp('2020-09-04 11:08:42.222910-0400', tz='America/New_York'),
     'realized_pl': -2874.0000000000036, 'unrealized_pl': -1437.0000000000018, 'total_pct_sold': 0.875},
    {'symbol': 'TREX', 'order_label': 'TREX/100 @ $133.74/Sep 4, 11:08', 'event_type': 'buy', 'balance': 100.0,
     'basis': 13374.0, 'timestamp': Timestamp('2020-09-04 11:08:32.930180-0400', tz='America/New_York'),
     'realized_pl': 0.0, 'unrealized_pl': 0.0, 'total_pct_sold': 0.0},
    {'symbol': 'TSLA', 'order_label': 'TSLA/50 @ $2,185.05/Aug 27, 9:30', 'event_type': 'buy', 'balance': 50.0,
     'basis': 109252.25, 'timestamp': Timestamp('2020-08-27 09:30:10.258040-0400', tz='America/New_York'),
     'realized_pl': 0.0, 'unrealized_pl': 0.0, 'total_pct_sold': 0.0},
    {'symbol': 'TSLA', 'order_label': 'TSLA/50 @ $2,185.05/Aug 27, 9:30', 'event_type': 'split', 'balance': 250.0,
     'basis': 109252.25, 'timestamp': Timestamp('2020-08-31 09:30:00-0400', tz='America/New_York'), 'realized_pl': 0.0,
     'unrealized_pl': 1797.75, 'total_pct_sold': 0.0},
    {'symbol': 'WEBS', 'order_label': 'WEBS/21100 @ $4.13/Aug 27, 9:30', 'event_type': 'buy', 'balance': 21100.0,
     'basis': 87143.0, 'timestamp': Timestamp('2020-08-27 09:30:05.665770-0400', tz='America/New_York'),
     'realized_pl': 0.0, 'unrealized_pl': 0.0, 'total_pct_sold': 0.0},
    {'symbol': 'WEBS', 'order_label': 'WEBS/21100 @ $4.13/Aug 27, 9:30', 'event_type': 'split', 'balance': 2110.0,
     'basis': 87143.0, 'timestamp': Timestamp('2020-08-28 09:30:00-0400', tz='America/New_York'), 'realized_pl': 0.0,
     'unrealized_pl': 0.0, 'total_pct_sold': 0.0},
    {'symbol': 'WEBS', 'order_label': 'WEBS/21100 @ $4.13/Aug 27, 9:30', 'event_type': 'sell', 'balance': 0.0,
     'basis': 87143.0, 'timestamp': Timestamp('2020-09-04 09:30:14.429210-0400', tz='America/New_York'),
     'realized_pl': 4747.5, 'unrealized_pl': 0.0, 'total_pct_sold': 1.0},
]


class TestSplits(CanonicalSplitsCase):
    """Stock splits introduce a lot of complexity into the order performance charting and calculating realized /
    unrealized P & L. This canonical test makes sure that we're nailing that  logic, and also does some values testing
    of the asset """

    def test_splits(self):
        # df = make_order_performance_table(self.game_id, self.user_id)
        # pd.testing.assert_frame_equal(df, pd.DataFrame(RECORDS))
        serialize_and_pack_order_performance_assets(self.game_id, self.user_id)
        import ipdb;
        ipdb.set_trace()
        print("hi")
