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
    set_diff = set(schema_definition.keys()) - set(df.columns)
    if not len(set_diff) == 0:
        raise FailedValidation(f"This dataframe is missing the following target columns: {set_diff}")
    for column in df.columns:
        target = schema_definition[column][0]
        if not df[column].dtype == target:
            raise FailedValidation(f"'{column}' does not have expect dtypes {target}")
        if not schema_definition and df[column].isna().sum() + df[column].isnull().sum() > 0:
            raise FailedValidation(f"'{column}' contains missing data")
    return True


# visuals.py
# ----------

balances_chart_schema = {
    "symbol": (pd.StringDtype, True),
    "value": (np.int64, False),
    "label": (pd.StringDtype, True)
}
portfolio_comps_schema = {
    "username": (pd.StringDtype, True),
    "value": (np.int64, False),
    "label": (pd.StringDtype, True)
}
order_performance_schema = {
    "order_label": (pd.StringDtype, True),
    "return": (np.int64, False),
    "label": (pd.StringDtype, True)
}
