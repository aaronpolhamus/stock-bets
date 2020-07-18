"""This file defines validators for the different derived pandas data objects that get passed around within stockbets'
business logic implementations. It has a dedicated section for each business logic module. When defining a new schema,
be sure to accompany the pandas_schema definition with a quick description of each column
"""
from pandas_schema import (
    Column,
    Schema
)
from pandas_schema.validation import IsDtypeValidation
import numpy as np
import pandas as pd
from pandas import StringDtype


class FailedValidation(Exception):

    def __str__(self):
        return "Failed schema validation"


def apply_validation(df: pd.DataFrame, schema_definition: Schema):
    """I don't love pandas_schema. If we want to swap out the internals for something customized at some point we can
    do that here.
    """
    errors = schema_definition.validate(df)
    if len(errors) > 0:
        raise FailedValidation
    return True


# visuals.py
# ----------

balances_chart_schema = Schema([
    # the instrument (stocks and ETFs for now), defining the data series
    Column("symbol", [IsDtypeValidation(StringDtype)]),
    # the value of that position
    Column("value", [IsDtypeValidation(np.int64)]),
    # the formatted x-axis label. trade_time_index and build_labels work together to make this
    Column("label", [IsDtypeValidation(StringDtype)])
])

portfolio_comps_schema = Schema([  # this supports "The Field" chart in the frontend
    # the different game participants define the data series. For single-player mode these will be index tickers
    Column("username", [IsDtypeValidation(StringDtype)]),
    # the total value of that user's holding. for indexes this will just be a normalized data series of the index value
    Column("value", [IsDtypeValidation(np.int64)]),
    # the formatted x-axis label. trade_time_index and build_labels work together to make this
    Column("label", [IsDtypeValidation(StringDtype)])
])

order_performance_schema = Schema([
    # a label for each individual purchase order containing quantity, time, and purchase price information
    Column("order_label", [IsDtypeValidation(StringDtype)]),
    # the return over time of each order based on the changing market price. series ends when that position is closed
    Column("return", [IsDtypeValidation(np.int64)]),
    # the formatted x-axis label. trade_time_index and build_labels work together to make this
    Column("label", [IsDtypeValidation(StringDtype)])
])
