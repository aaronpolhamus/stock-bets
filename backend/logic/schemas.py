"""This file defines validators for the different derived pandas data objects that get passed around within stockbets'
business logic implementations. It has a dedicated section for each business logic module. When defining a new schema,
be sure to accompany the pandas_schema definition with a quick description of each column.

A schema is a dict where the columns are the keys and the value is a tuple that contains a list of target column types
in the first position, and a flag for whether to permit missing values in the column in the second
"""
import numpy as np
import pandas as pd


VALID_TIME_TYPES = [pd.Timedelta, np.dtype('<M8[ns]'), pd.DatetimeTZDtype]


class FailedValidation(Exception):
    def __init__(self, message="Failed schema validation"):
        super().__init__(message)


def apply_validation(df: pd.DataFrame, schema_definition: dict, strict: bool = False) -> bool:
    """I don't love pandas_schema. If we want to swap out the internals for something customized at some point we can
    do that here.
    """
    target_columns = schema_definition.keys()
    set_diff = set(target_columns) - set(df.columns)
    if len(set_diff) > 0:
        msg = f"This dataframe is missing the following target columns: [{', '.join(set_diff)}]"
        raise FailedValidation(msg)

    if strict:
        set_diff = set(df.columns) - set(target_columns)
        if len(set_diff) > 0:
            msg = f"Strict mode -- the data frame contains the following extra columns [{', '.join(set_diff)}]"
            raise FailedValidation(msg)

    for column in target_columns:
        type_targets = schema_definition[column][0]
        if not df[column].dtype in type_targets:
            # this is an awkward fail-over for checking TZ-aware pandas datetime columns, but it works
            if pd.DatetimeTZDtype in type_targets and isinstance(df[column].dtype, pd.DatetimeTZDtype):
                continue
            string_types = [str(x) for x in type_targets]
            raise FailedValidation(f"'{column}' does not have a type in {','.join(string_types)}")
        if not schema_definition and df[column].isna().sum() + df[column].isnull().sum() > 0:
            raise FailedValidation(f"'{column}' contains missing data")
    return True


# base.py
# -------
balances_and_prices_table_schema = {
    "symbol": ([pd.StringDtype], False),
    "timestamp": ([VALID_TIME_TYPES, False]),
    "balance": ([float, np.int64], False),
    "price": ([float, np.int64], False),
    "value": ([float, np.int64], False),
    "last_transaction_type": ([pd.StringDtype], True)
}

# visuals.py
# ----------

balances_chart_schema = {
    # the instrument (stocks and ETFs for now), defining the data series
    "symbol": ([pd.StringDtype], True),
    # the value of that position
    "value": ([float, np.int64], False),
    # the formatted x-axis label. trade_time_index and build_labels work together to make this
    "label": ([pd.StringDtype], True),
    # balances chart data should preserve original datetime information for sorting prior to being passed-in
    "timestamp": (VALID_TIME_TYPES, False)
}

portfolio_comps_schema = {
    # the different game participants define the data series. For single-player mode these will be index tickers
    "username": ([pd.StringDtype], True),
    # the total value of that user's holding. for indexes this will just be a normalized data series of the index value
    "value": ([float, np.int64], False),
    # the formatted x-axis label. trade_time_index and build_labels work together to make this
    "label": ([pd.StringDtype], True),
    # balances chart data should preserve original datetime information for sorting prior to being passed-in
    "timestamp": (VALID_TIME_TYPES, False)
}

order_details_schema = {
    "symbol": ([pd.StringDtype], False),
    "timestamp_fulfilled": ([float, np.int64], True),
    "quantity": ([float, np.int64], False),
    "clear_price_fulfilled": ([float, np.int64], True)
}
