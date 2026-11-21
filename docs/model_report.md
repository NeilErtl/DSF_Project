# Model report: estimation of the spread over SOFR (notebook 02)

Notebook: `code/02_estimate.ipynb` (runs top to bottom). Decisions with evidence: `docs/decisions.md` (D45 to D48).
Every number below comes from the tables in `output/tables/`: `horse_race_validation.csv` (all candidates),
`tuning_default_vs_tuned.csv`, `validation_error_yardsticks.csv` (6c), `residual_target_checks.csv` (6f)
and `optional_features_validation.csv` (step 7). Counterpart of `docs/data_report.md` for notebook 01.

**Status (21 Nov 2026):** steps 0 to 7 done (validation race, residual-target round with its critical check,
optional features, complete race figure). Open: step 8 choice of the main model (owner), steps 9 and 10 test and robustness predictions for notebook 03.

## 1. Task as understood
- **Predict** the spread over SOFR (`spread_pp`, percentage points) of a newly originated loan at the start of its
  quarter, from the features fixed in CLAUDE.md (`mh.NUM` + `mh.CAT`, optional features of `for_modelling.md` as a
  variant); errors in basis points.
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
   (`spread_pp - mkt_spread_t2_all`); prediction = predicted deviation + median; scored on the spread as before.
6. **Critical check of the residual target (6f, D47):** pass-through of the market level and bias per quarter.
7. **Optional features (step 7, D48):** `has_revolver`, `has_delayed_draw`, `n_family_bdcs` added to the three best
   residual models, tuned settings kept; the complete race in one figure (7b).

## 3. Results on the validation quarters (675 loans; MAE in bps)
| Candidate | Spread as target | Residual target | Residual + optional features |
|---|---|---|---|
| Random forest | 85.4 | 59.3 | **54.6** |
| Gradient boosting | 86.7 | 58.3 | 57.3 |
| Neural network | 126.6 | 60.8 | 68.3 |
| Ridge | 72.1 | 64.7 | |
| Lasso | 68.5 | 66.4 | |
| Tree | 89.0 | 68.6 | |
| Linear regression | 74.9 | 74.9 | |
| Baseline 1: market median t-2 | 78.6 | | |
| Baseline 2: sector x size median | 98.3 | | |
| Reference: training mean | 96.0 | | |

- **Best:** random forest, residual target, optional features: 54.6 bps, 24 bps below baseline 1; lower than the
  forest without optional features in each of the four folds; share within 50 bps 63.1% against 58.4% for baseline
  1 (the only candidate ahead of baseline 1 on both metrics). Fold spread 7.0 bps; boosting (57.3, 58.3) and the
  residual forest without optional features (59.3) lie within it.
- All residual models beat baseline 1 in all four folds; linear regression is identical in both rounds by
  construction (the market median is a feature).
- Tuning gains larger than the fold spread only for lasso (the default alpha removes every coefficient) and for ridge
  and lasso on the residual target; elsewhere tuning polishes (deck 16).
- Figure: `output/figures/horse_race_validation.png` (all 20 candidates; colour and shape mark the round).

## 4. Findings
- **The market level carries most of the predictable signal.** Baseline 1 beats the sector x size median by 20 bps
  because spreads fell from about 6.25 pp (2023) to 4.75 pp (2025) and a four-quarter window lags.
- **Trees cannot follow a falling market.** In every fold the market features of the validation quarter lie outside
  the training range; trees predict averages of training loans and stay too high. Training on the deviation from the
  market median removes the problem (boosting 86.7 -> 58.3, forest 85.4 -> 59.3 bps).
- **Deal structure adds information.** Whether the borrower also has a revolver or delayed-draw line and how many of
  the manager's BDCs hold the loan lower the forest's error by 4.7 bps, in every fold.
- **A floor from missing borrower data.** No overfitting (lasso training 63 to 69 bps, validation 65 to 70 bps).
  Knowing the true quarter median still leaves 74 to 83 bps; a lasso fitted on the validation quarter itself reaches
  55 to 59 bps (the limit for linear models). Leverage, earnings and sponsor, which drive spreads, are not in the
  filings.
- **Where the error sits.** Spreads at or below 4 pp and above 7 pp are pulled towards the middle; 10% of loans with
  errors above 150 bps carry 31% of the lasso error.
- **Metric caveat.** 97% of spreads lie on a 25 bps grid, so a constant median hits 17.5% of loans exactly. Report
  MAE and the share within 50 bps together.

## 5. Does the residual target still answer our question? (6f, D47)
- **Yes:** the model still predicts, and is scored on, the spread over SOFR at the cutoff. The market median t-2 is a
  committed feature and the committed baseline 1 (no new information, no leakage). "Market level + loan premium"
  is how a deal team prices against comparables. Transforming the training target has a course precedent (log
  price, notebook 209).
- **Assumptions, reported as limitations:** (1) trees pass the market level through one-for-one; across the nine
  training quarters the median spread moved 0.79 pp per 1 pp of the t-2 median. (2) The premium is learned in a
  falling market, so the tree-based residual models (boosting, forest, also with the optional features) predict too
  low in every validation quarter (mean error +8 to +22 bps); baseline 1, lasso and the residual neural net err in
  both directions. A rising market would increase this bias. (3) Feature importances of
  a residual model describe the premium, not the spread level.

## 6. Checks
Fold construction (gap, filing dates) asserted; no never-feature among the features (incl. the optional ones); every
candidate predicts every validation loan once; baseline 2 recomputed by separate code for all 675 loans; predictions
within 1 to 15 pp; best ridge and lasso alpha inside their grids; tuning never ends below the default; the notebook
runs top to bottom with fixed seeds.

## 7. Decisions for team review (`docs/decisions.md`)
D45 working rules for 02/03; D46 small choices in steps 2 to 6; D47 residual target as second round
(**consequential**, model specification, with the critical assessment); D48 optional features. Pending: choice of
the main model (step 8, **consequential**).

## 8. Open risks
- **Selection optimism:** about 20 candidates were compared on the same four quarters; the best validation score is
  optimistic. The test quarters give the honest number.
- Four validation quarters only; differences below about 6 to 8 bps are within the spread across the folds.
- Tree-based residual models: inherited bias from a falling market (section 5).
- 61 validation loans belong to a manager family not seen in their training fold (pooled infrequent category).
- The early-stopping holdout of the neural net is drawn at random within the training fold (D46).
