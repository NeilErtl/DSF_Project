"""Helpers for notebook 02 (estimation): loading the working dataset, the preprocessing pipeline and the time splits.

Adapted from Patrick Eppler's `preprocessing.py` (load_data, make_preprocessor, time_cv_splits, final_train_test) in his
independent version of the preprocessing; column names changed to our dataset (`data/processed/loans.csv`).

Usage (in code/02_estimate.ipynb):
    import modelling_helpers as mh
    df = mh.load_data("../data/processed/loans.csv")
    train = df[df.split == "train"]
    from sklearn.pipeline import make_pipeline
    from sklearn.linear_model import Ridge
    model = make_pipeline(mh.make_preprocessor(), Ridge(alpha=1.0))
    for tr_idx, va_idx in mh.time_cv_splits(train):      # expanding window by quarter, one-quarter gap
        model.fit(train.iloc[tr_idx][mh.NUM + mh.CAT], train.iloc[tr_idx][mh.TARGET])
        ...

Everything learned from data (median imputation, scaling, one-hot encoding) is inside the sklearn pipeline, so it is
fitted on the training fold only (deck 06, notebook 211).
"""
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

TARGET = "spread_pp"                      # spread over SOFR in percentage points (report errors in bps)
NUM = ["log_principal", "tenor_years", "mkt_spread_t2_all", "baa_spread_prev", "sofr_prev"]
CAT = ["sector", "lien", "family"]


def load_data(path="../data/processed/loans.csv"):
    """Read the working dataset; `quarter` becomes a pandas quarterly Period. Rows sorted by quarter and loan_id."""
    df = pd.read_csv(path, parse_dates=["quarter_start_date", "maturity_date", "filed_date"])
    df["quarter"] = pd.PeriodIndex(df["quarter_str"], freq="Q")
    return df.sort_values(["quarter", "loan_id"]).reset_index(drop=True)


def make_preprocessor(min_frequency=5):
    """Numeric features: median imputation and z-scores; categorical: one-hot with a dropped reference category.

    Categories with fewer than `min_frequency` training loans are pooled as "infrequent" (small families, rare
    sectors). A category not seen in the training fold is mapped to the infrequent group if one exists, otherwise to
    all zeros, i.e. to the dropped reference category; check this for families that enter late.
    """
    num = Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())])
    cat = OneHotEncoder(handle_unknown="infrequent_if_exist", drop="first", min_frequency=min_frequency)
    return ColumnTransformer([("num", num, NUM), ("cat", cat, CAT)])


def time_cv_splits(train, min_train_quarters=4, gap=1):
    """Expanding-window cross-validation over the training quarters.

    To validate on quarter t the model is trained on quarters up to t-2 (gap=1): the filings of t-1 are not yet
    public at the start of t, our cutoff. The first validation quarter follows `min_train_quarters` training quarters.
    Yields (train_index, validation_index) as positions in `train`.
    """
    qs = sorted(train["quarter"].unique())
    for i in range(min_train_quarters + gap, len(qs)):
        va_q = qs[i]
        tr_q = qs[: i - gap]
        tr_idx = np.where(train["quarter"].isin(tr_q))[0]
        va_idx = np.where(train["quarter"] == va_q)[0]
        yield tr_idx, va_idx


def final_train_test(df, respect_gap=True):
    """Train and test sets for the final evaluation on the test quarters (2025Q3 to 2026Q2), used once.

    respect_gap=True: train only on quarters up to 2025Q1, because 2025Q2 filings were not public at the start of
    2025Q3 (same one-quarter gap as in validation). respect_gap=False: all training quarters (report as a limitation).
    Note: one model is trained once, so the later test quarters (2025Q4 to 2026Q2) are predicted with a gap of 2 to
    4 quarters: conservative (no leakage), and a reason to report the MAE by test quarter.
    """
    train = df[df["split"] == "train"]
    if respect_gap:
        train = train[train["quarter"] < train["quarter"].max()]
    test = df[df["split"] == "test"]
    return train, test
