"""This file defines validators for the different derived pandas data objects that get passed around within stockbets'
business logic implementations. It has a dedicated section for each business logic module. When defining a new schema,
be sure to accompany the pandas_schema definition with a quick description of each column.

A schema is a dict where the columns are the keys and the value is a tuple that contains a list of target column types
in the first position, and a flag for whether to permit missing values in the column in the second
"""
import numpy as np
import pandas as pd


class FailedValidation(Exception):

    def __str__(self):
        return "Failed schema validation"


def apply_validation(df: pd.DataFrame, schema_definition: dict):
    """I don't love pandas_schema. If we want to swap out the internals for something customized at some point we can
    do that here.
    """
    target_columns = schema_definition.keys()
    set_diff = set(target_columns) - set(df.columns)
    if not len(set_diff) == 0:
        raise FailedValidation(f"This dataframe is missing the following target columns: {set_diff}")

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
    "timestamp": ([pd.Timedelta, np.dtype('<M8[ns]'), pd.DatetimeTZDtype], False)
}
portfolio_comps_schema = {
    # the different game participants define the data series. For single-player mode these will be index tickers
    "username": ([pd.StringDtype], True),
    # the total value of that user's holding. for indexes this will just be a normalized data series of the index value
    "value": ([float, np.int64], False),
    # the formatted x-axis label. trade_time_index and build_labels work together to make this
    "label": ([pd.StringDtype], True),
    # balances chart data should preserve original datetime information for sorting prior to being passed-in
    "timestamp": ([pd.Timedelta, np.dtype('<M8[ns]'), pd.DatetimeTZDtype], False)
}
order_performance_schema = {
    # a label for each individual purchase order containing quantity, time, and purchase price information
    "order_label": ([pd.StringDtype], True),
    # the return over time of each order based on the changing market price. series ends when that position is closed
    "return": ([float, np.int64], False),
    # the formatted x-axis label. trade_time_index and build_labels work together to make this
    "label": ([pd.StringDtype], True)
}