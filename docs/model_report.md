# Model report: estimation of the spread over SOFR (notebook 02)

Notebook: `code/02_estimate.ipynb` (runs top to bottom). Decisions with evidence: `docs/decisions.md` (D45 to D47).
Every number below comes from `output/tables/horse_race_validation.csv`, `output/tables/tuning_default_vs_tuned.csv`
or `output/tables/validation_error_yardsticks.csv`. Counterpart of `docs/data_report.md` for notebook 01.

**Status (21 Nov 2026):** steps 0 to 6 done (validation race). Open: step 7 optional features, step 8 choice of the
main model, steps 9 and 10 test and robustness predictions for notebook 03.

## 1. Task as understood
- **Predict** the spread over SOFR (`spread_pp`, percentage points) of a newly originated loan at the start of its
  quarter, from the features fixed in CLAUDE.md (`mh.NUM` + `mh.CAT`); errors in basis points.
- **Validate** on four expanding-window folds with a one-quarter gap (validation quarters 2024Q3, 2024Q4, 2025Q1,
  2025Q2; 675 loans), training loans filed before the validation quarter starts. The test quarters (2025Q3 to 2026Q2)
  are not used for any choice.
- **Choose** the main model on the MAE pooled over all validation loans; per-fold MAEs show the spread (deck 16,
  rule 4: a simpler model if the gap is within the spread across the folds).
- **Hand over** to notebook 03 (Nathan Steiner): predictions of all candidates in one file, one row per model and
  loan (`model, fold, loan_id, quarter, family, y_true, y_pred, abs_error_bps`). Notebook 03 computes all test
  metrics and fits no model (D45).

## 2. What was done
1. **Baselines** (as committed): (1) median spread of new loans in quarter t-2, (2) median by sector and size tercile
   over t-5 to t-2 with fallbacks; a training-mean reference.
2. **Models** (course models only, each in a pipeline with the shared preprocessor, fitted per fold): linear
   regression, ridge, lasso, one tree, random forest, gradient boosting, a small neural network.
3. **Tuning:** small grids on the same folds; the default setting competes with the grid (D46, D47).
4. **Diagnostics:** why trees lose with the spread as target (6b); how much these features can explain (6c).
5. **Second round (D47):** every model trained on the deviation from the market median
   (`spread_pp - mkt_spread_t2_all`), prediction = deviation + median; scored on the spread as before.

## 3. Results on the validation quarters (675 loans; MAE in bps)
| Candidate | Spread as target | Residual target | Folds beating baseline 1 (residual) |
|---|---|---|---|
| Gradient boosting | 86.7 | **58.3** | 4 of 4 |
| Random forest | 85.4 | 59.3 | 4 of 4 |
| Neural network | 126.6 | 60.8 | 4 of 4 |
| Ridge | 72.1 | 64.7 | 4 of 4 |
| Lasso | 68.5 | 66.4 | 4 of 4 |
| Tree | 89.0 | 68.6 | 4 of 4 |
| Linear regression | 74.9 | 74.9 | 3 of 4 |
| Baseline 1: market median t-2 | 78.6 | | |
| Baseline 2: sector x size median | 98.3 | | |
| Reference: training mean | 96.0 | | |

- Best: boosting on the residual target, 20 bps below baseline 1, fold spread 6.4 bps; share within 50 bps 57.6%
  against 58.4% for baseline 1. Boosting, forest and net (residual) lie within the fold spread of each other.
- Tuning gains larger than the fold spread only for lasso (default alpha removes every coefficient) and for ridge and
  lasso on the residual target; elsewhere tuning polishes (deck 16). Table: `tuning_default_vs_tuned.csv`.
- Figure: `output/figures/horse_race_validation.png`.

## 4. Findings
- **The market level carries most of the predictable signal.** Baseline 1 beats the sector x size median by 20 bps
  because spreads fell from about 6.25 pp (2023) to 4.75 pp (2025) and a four-quarter window lags.
- **Trees cannot follow a falling market.** In every fold the market features of the validation quarter lie outside
  the training range; trees predict averages of training loans and stay too high. Training on the deviation from the
  market median removes the problem (boosting 86.7 -> 58.3 bps). Linear regression is unchanged by construction.
- **A hard floor from missing borrower data.** No overfitting (lasso training 63 to 69 bps, validation 65 to 70 bps).
  Knowing the true quarter median still leaves 74 to 83 bps; a lasso fitted on the validation quarter itself reaches
  55 to 59 bps. Leverage, earnings and sponsor, which drive spreads, are not in the filings.
- **Where the error sits.** Spreads at or below 4 pp and above 7 pp are pulled towards the middle; 10% of loans with
  errors above 150 bps carry 31% of the lasso error.
- **Metric caveat.** 97% of spreads lie on a 25 bps grid, so a constant median hits 17.5% of loans exactly: baseline
  1 has the highest share within 50 bps despite a higher MAE. Report both.

## 5. Checks
Fold construction (gap, filing dates) asserted; no never-feature among the features; every candidate predicts every
validation loan once; baseline 2 recomputed by separate code for all 675 loans; predictions within 1 to 15 pp;
best ridge and lasso alpha inside their grids; the notebook runs top to bottom with fixed seeds.

## 6. Decisions for team review (`docs/decisions.md`)
D45 working rules for 02/03 (split of tasks, choice criterion, grids, optional features, environment, robustness);
D46 small choices in steps 2 to 6; D47 residual target as second round (**consequential**, model specification).
Pending: choice of the main model (step 8, **consequential**).

## 7. Open risks
- Tuned scores are slightly optimistic (best of several settings on the same four folds); the test quarters give the
  honest number.
- Four validation quarters only; differences below about 6 to 8 bps are within the spread across the folds.
- 61 validation loans belong to a manager family not seen in their training fold (pooled infrequent category).
- The early-stopping holdout of the neural net is drawn at random within the training fold (D46).
