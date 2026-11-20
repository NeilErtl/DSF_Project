# For modelling (notebooks 02 and 03): what you need to know

**Load.** From `code/`: `import modelling_helpers as mh; df = mh.load_data("../data/processed/loans.csv")`.
`df.quarter` is a pandas quarterly Period. All numbers below are in `output/tables/headline_numbers.csv`.

**Unit and target.** Cross-section with a date (each loan once). One row = one new loan: one borrower x one manager family x the quarter in which the family
first holds it (1,725 loans, 2023Q2 to 2026Q2, 31 families, lead BDC = 45 distinct `cik`). Target `spread_pp` = spread
over SOFR of newly originated loans, in percentage points; report errors in basis points (x 100). Three origination checks: our hand check 32 of 36 (89%), Patrick's
hand check 25 of 26 (96%), and an out-of-sample check 24 of 30 (80%, 95% CI 63 to 90%; the cleanest estimate, since
no filter was designed on it); over all 91 distinct checked loans in the sample 88% (95% CI 80 to 93%). About one
loan in five to one in ten may be a purchase or transfer rather than a fresh origination; it is still a loan newly
priced into a BDC portfolio. Use this name for the target in report and slides (D41).

**Features (allowed).** `mh.NUM` = `log_principal` (log of the family's held principal at the reporting date: an
approximation of the hold size, not the facility size), `tenor_years` (maturity minus quarter start),
`mkt_spread_t2_all` (median spread of new loans first seen in quarter t-2, filed before the cutoff), `baa_spread_prev`,
`sofr_prev` (FRED, last value before the cutoff). `mh.CAT` = `sector`, `lien`, `family`. Optional: `instrument`,
`has_revolver`, `has_delayed_draw`, `n_family_bdcs`, `mkt_spread_t2_core` (instead of `mkt_spread_t2_all`). Pass other lists with
`mh.make_preprocessor(num=..., cat=...)` and the same columns to the model. In `data_dictionary.csv`, `role`
`feature` = in NUM or CAT, `feature_optional` = may be added, `never_feature` = leakage; every other role is not a
feature (`note` gives details).

**Never features.** `interest_rate_pp`, `fair_value`, `cost`, `pik_flag`, `pik_rate_pp`, `floor_pp` (leakage, fixed by
the commitments); also not: `spread_min_family`, `spread_max_family` (other lines of the same loan),
`n_other_families_same_q`, `seen_at_other_family_before`, `no_rate_tagged`, `committed_not_funded` (flags, partly known
only after the cutoff or derived from fair value and cost), ids, dates and `split`.

**Split and folds.** `split` = train (2023Q2 to 2025Q2, 1,131 loans) or test (2025Q3 to 2026Q2, 594 loans). Do not
look at test rows until the final evaluation; never choose a model on them. To predict quarter t, train only on loans
up to t-2 (one-quarter gap: t-1 filings are not public at the start of t); the helpers also drop training rows filed
after the cutoff (late amendments).
- Validation: `mh.time_cv_splits(train)` gives 4 expanding-window folds (validate 2024Q3 to 2025Q2).
- Final evaluation, main protocol (D41): `mh.evaluate_per_test_quarter(make_model, df)` fits one model per test
  quarter t on all loans up to t-2, so the test gap equals the validation gap. Each test loan is predicted exactly
  once, by a model that never saw it; model choice happens only on the validation folds. Secondary view:
  `mh.final_train_test(df)`, one model trained up to 2025Q1 (990 loans, gap of 1 to 4 quarters).
- The helpers drop training rows filed after the cutoff: in the last validation fold 2 loans (836 instead of 838).
- Put all learned preprocessing in a pipeline: `make_pipeline(mh.make_preprocessor(), Ridge())`.

**Baselines (as committed, both with the t-2 rule; code in the helpers).** (1) `mh.baseline_t2(rows)`: the median
spread of new loans first seen in quarter t-2 and filed before the cutoff (`mkt_spread_t2_all`, over all BDCs because
the main-sample median `mkt_spread_t2_core` is missing in 96 loans). (2) `mh.baseline_sector_size(history, rows)`:
median by sector and size class over exactly the quarters t-5 to t-2 (loans filed before the cutoff); size class =
terciles of `log_principal` cut on those loans, recomputed for every t; a cell with fewer than 5 loans falls back to
the sector median of the same window, then to (1). Use the error frames of `mh.error_frame(rows, pred)` for every
model and baseline.

**Metrics.** MAE in bps (main), share of loans within plus or minus 50 bps, MAE by test quarter and by manager family,
on frames from `mh.error_frame` or `mh.evaluate_per_test_quarter`: `mh.summarize_errors(pred)`, `mh.summarize_errors(pred, "quarter")`, `mh.summarize_errors(pred, "family")`. Same folds
and metric for every model and baseline (horse race, notebook 209).

**Robustness files and flags.**
- `loans_all_bdc.csv` (7,174 loans, all BDCs): run without `sector`
  (`make_preprocessor(cat=["lien", "family"])`). Sector is missing for 64% of rows, tenor for 62% (imputed), and the
  base rate is not written for 61% (`base_rate` "UNKNOWN": most likely SOFR in this period, not verified).
- `loans_incl_refi.csv` (2,171 loans): also refinancings and add-ons of existing borrowers (`refi_of_existing_borrower`,
  402) and tenors of 3 to 4 years (`tenor_3_to_4`).
- Sensitivity without likely syndicated loans: drop `n_other_families_same_q >= 3` (662 loans, 38%; the flag uses
  same-quarter filings, so it defines a subsample, never a feature).

**Pitfalls.** (1) Apollo is 19% and Goldman Sachs 11% of loans: report MAE by family. (2) A family first seen late
maps to the infrequent group if the fold has one, otherwise to the reference category (see `make_preprocessor`).
(3) If you add `mkt_spread_t2_core`, it is missing in 96 loans; the pipeline imputes the training median. (4) Hold size is the held principal, not the deal
size. (5) `lien` is "unknown" for almost all Stellus, TCW and Onex loans (not written in the line). (6) The test
quarters are used once.
