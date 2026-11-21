"""Helpers for notebooks 02 and 03: loading the working dataset, the preprocessing pipeline, the time splits and the
committed error metrics and baselines. Notebook 01 only dry-runs the splits (no model fit; the preprocessor is fitted
once on training rows to check its shape).

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
        tr, va = train.iloc[tr_idx], train.iloc[va_idx]
        model.fit(tr[mh.NUM + mh.CAT], tr[mh.TARGET])
        errors = mh.error_frame(va, model.predict(va[mh.NUM + mh.CAT]))
        base1 = mh.error_frame(va, mh.baseline_t2(va))
        base2 = mh.error_frame(va, mh.baseline_sector_size(train, va))
        print(mh.summarize_errors(errors), mh.summarize_errors(base1), mh.summarize_errors(base2))

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


def make_preprocessor(min_frequency=5, num=None, cat=None):
    """Numeric features: median imputation and z-scores; categorical: one-hot with a dropped reference category.

    num, cat: feature lists (default NUM and CAT). Example with an optional feature and without sector:
        make_preprocessor(num=NUM + ["n_family_bdcs"], cat=["lien", "family"])
    Categories with fewer than `min_frequency` training loans are pooled as "infrequent" (small families, rare
    sectors). A category not seen in the training fold is mapped to the infrequent group if the fold has one,
    otherwise to all zeros, i.e. to the dropped reference category; check this for families that enter late.
    """
    num_pipe = Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())])
    cat_pipe = OneHotEncoder(handle_unknown="infrequent_if_exist", drop="first", min_frequency=min_frequency)
    return ColumnTransformer([("num", num_pipe, NUM if num is None else num),
                              ("cat", cat_pipe, CAT if cat is None else cat)])


def time_cv_splits(train, min_train_quarters=4, gap=1):
    """Expanding-window cross-validation over the training quarters.

    To validate on quarter t the model is trained on quarters up to t-2 (gap=1): the filings of t-1 are not yet
    public at the start of t, our cutoff. Training rows must also have been filed before the start of t (a late
    amendment can carry an older quarter, see `known_before`). The first validation quarter follows
    `min_train_quarters` training quarters. Yields (train_index, validation_index) as positions in `train`.
    """
    qs = sorted(train["quarter"].unique())
    assert all(b == a + 1 for a, b in zip(qs, qs[1:])), "quarters must be contiguous for the position-based gap"
    for i in range(min_train_quarters + gap, len(qs)):
        va_q = qs[i]
        tr_q = qs[: i - gap]
        tr_idx = np.where(train["quarter"].isin(tr_q) & known_before(train, va_q))[0]
        va_idx = np.where(train["quarter"] == va_q)[0]
        yield tr_idx, va_idx


def known_before(df, quarter):
    """True for rows whose filing (column filed_date) was submitted before the start of `quarter`, the cutoff.

    The one-quarter gap alone is not enough in rare cases: a BDC that amends a filing late (e.g. a 10-K/A filed months
    after the original) carries the amendment's filing date, so its loans count as public only from that date.
    """
    return (df["filed_date"] < quarter.start_time).to_numpy()


def final_train_test(df, respect_gap=True):
    """Train and test sets for the final evaluation on the test quarters (2025Q3 to 2026Q2), used once.

    respect_gap=True: train only on quarters up to 2025Q1, because 2025Q2 filings were not public at the start of
    2025Q3 (same one-quarter gap as in validation). respect_gap=False: all training quarters (report as a limitation).
    Note: one model is trained once, so the later test quarters (2025Q4 to 2026Q2) are predicted with a gap of 2 to
    4 quarters: conservative (no leakage), and a reason to report the MAE by test quarter. The alternative with the
    same gap for every test quarter is `test_quarter_splits` / `evaluate_per_test_quarter`.
    """
    train = df[df["split"] == "train"]
    test = df[df["split"] == "test"]
    if respect_gap:
        train = train[(train["quarter"] < train["quarter"].max()) & known_before(train, test["quarter"].min())]
    return train, test


def test_quarter_splits(df, gap=1):
    """Per-test-quarter evaluation (rolling origin): one model per test quarter.

    For each test quarter t (2025Q3 to 2026Q2) the training set is every loan of quarters up to t-2, including
    earlier test quarters once their filings are public (for t = 2026Q1 the training set ends in 2025Q3). This is
    what a deal team could do at the start of each quarter, and every test quarter gets the same one-quarter gap.
    Hyperparameters must be fixed before (on the validation folds of `time_cv_splits`); the test quarters are used
    for evaluation only, never to choose a model.
    Yields (test_quarter, train_rows, test_rows) as DataFrames.
    """
    test_qs = sorted(df.loc[df["split"] == "test", "quarter"].unique())
    for t in test_qs:
        yield t, df[(df["quarter"] <= t - (gap + 1)) & known_before(df, t)], df[df["quarter"] == t]


def evaluate_per_test_quarter(make_model, df, gap=1, features=None):
    """Fit a fresh model for each test quarter (see `test_quarter_splits`) and collect the test predictions.

    make_model: function without arguments that returns an unfitted sklearn estimator or pipeline, e.g.
        lambda: make_pipeline(make_preprocessor(), Ridge(alpha=1.0)).
    features: columns passed to the model (default NUM + CAT; must match the preprocessor in make_model).
    Training on earlier test quarters is intended here: at the start of 2026Q1 the 2025Q3 loans are public. The test
    set is still used once, for this final evaluation only.
    Returns one row per test loan (see `error_frame`); summarize with `summarize_errors`.
    """
    cols = NUM + CAT if features is None else features
    rows = []
    for t, tr, te in test_quarter_splits(df, gap):
        model = make_model()
        model.fit(tr[cols], tr[TARGET])
        rows.append(error_frame(te, model.predict(te[cols])))
    return pd.concat(rows, ignore_index=True)


def error_frame(rows, y_pred):
    """Predictions of any model or baseline on `rows` (validation fold or test set) as one frame for the metrics:
    loan_id, quarter, family, y_true, y_pred, abs_error_bps."""
    out = pd.DataFrame({"loan_id": rows["loan_id"].values, "quarter": rows["quarter"].values,
                        "family": rows["family"].values, "y_true": rows[TARGET].values, "y_pred": np.asarray(y_pred)})
    out["abs_error_bps"] = (out["y_true"] - out["y_pred"]).abs() * 100
    return out


def baseline_t2(rows):
    """Baseline 1 (committed): the median spread of new loans first seen in quarter t-2 and filed before the cutoff,
    i.e. the column `mkt_spread_t2_all`. It is computed over the new loans of all BDCs (more loans per quarter, a
    stabler median); `mkt_spread_t2_core` is the main-sample version but is missing when fewer than 20 loans."""
    return rows["mkt_spread_t2_all"].to_numpy()


def baseline_sector_size(history, rows, window=4, min_loans=5, gap=1):
    """Baseline 2 (committed): median spread by sector and size class over the previous four quarters.

    For each quarter t of `rows`, the window is exactly the quarters t-5 to t-2 (four quarters ending at t-2, the
    same one-quarter gap), using only loans of `history` filed before the cutoff (`known_before`). Size class =
    terciles of log_principal, cut on the loans of the window (recomputed for every t). A sector x size cell with
    fewer than `min_loans` loans falls back to the sector median of the window, then to baseline 1. `history` may be
    the whole dataset: only quarters up to t-2 are used, so no outcome of t or t-1 enters. Returns predictions in the
    order of `rows`.
    """
    pred = pd.Series(np.nan, index=rows.index)
    for t, part in rows.groupby("quarter"):
        last = t - (gap + 1)
        win = history[(history["quarter"] <= last) & (history["quarter"] > last - window) & known_before(history, t)]
        edges = np.quantile(win["log_principal"], [1 / 3, 2 / 3])
        cell = (win.assign(size=np.digitize(win["log_principal"], edges))
                .groupby(["sector", "size"])[TARGET].agg(["median", "count"]))
        sec = win.groupby("sector")[TARGET].agg(["median", "count"])
        for i, s, k in zip(part.index, part["sector"], np.digitize(part["log_principal"], edges)):
            if (s, k) in cell.index and cell.loc[(s, k), "count"] >= min_loans:
                pred[i] = cell.loc[(s, k), "median"]
            elif s in sec.index and sec.loc[s, "count"] >= min_loans:
                pred[i] = sec.loc[s, "median"]
            else:
                pred[i] = part.loc[i, "mkt_spread_t2_all"]
    return pred.to_numpy()


def summarize_errors(pred, by=None):
    """Committed metrics: MAE in basis points and the share of loans within plus or minus 50 bps.

    pred: output of `evaluate_per_test_quarter` (or any frame with abs_error_bps). by: None, "quarter" or "family".
    """
    f = lambda d: pd.Series({"n": len(d), "mae_bps": d["abs_error_bps"].mean(),
                             "share_within_50bps": (d["abs_error_bps"] <= 50).mean()})
    return f(pred) if by is None else pred.groupby(by).apply(f, include_groups=False)
