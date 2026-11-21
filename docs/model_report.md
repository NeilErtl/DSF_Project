# Model report: estimation of the spread over SOFR (notebook 02)

Notebook: `code/02_estimate.ipynb` (runs top to bottom). Decisions with evidence: `docs/decisions.md` (D45 to D51).
Counterpart of `docs/data_report.md` for notebook 01. Every number below comes from the tables in `output/tables/`:
`horse_race_validation.csv` (all candidates), `tuning_default_vs_tuned.csv`, `validation_error_yardsticks.csv` (6c),
`residual_target_checks.csv` (6f), `optional_features_validation.csv` (step 7), `model_choice.csv` and
`feature_importance_main_model.csv` (step 8).

**Status (21 Nov 2026):** notebook 02 complete (steps 0 to 10): validation race, residual-target round with its
critical check, optional features, main model chosen, test and robustness predictions written for notebook 03. No
test error has been computed in 02.

## 1. Task as understood
- **Predict** the spread over SOFR (`spread_pp`, percentage points) of a newly originated loan at the start of its
  quarter, from the features fixed in CLAUDE.md (`mh.NUM` + `mh.CAT`; the optional features of `for_modelling.md`
  as a variant); errors in basis points.
- **Validate** on four expanding-window folds with a one-quarter gap (validation quarters 2024Q3, 2024Q4, 2025Q1,
  2025Q2; 675 loans), training loans filed before the validation quarter starts. The test quarters (2025Q3 to 2026Q2)
  are not used for any choice.
- **Choose** the main model on the MAE pooled over all validation loans; per-fold MAEs show the spread (deck 16,
  rule 4: a simpler model if the gap is within the spread across the folds).
- **Hand over** to notebook 03 (owned by another team member): predictions of all candidates in one file, one row per model and
  loan (`model, fold, loan_id, quarter, family, y_true, y_pred, abs_error_bps`). Notebook 03 computes all test
  metrics and fits no model (D45).

## 2. What was done (in the order of the notebook)
1. **Baselines** (step 2, as committed): (1) median spread of new loans in quarter t-2, (2) median by sector and size
   tercile over t-5 to t-2 with fallbacks; a training-mean reference.
2. **Models** (steps 3 to 5; course models only, each in a pipeline with the shared preprocessor, fitted per fold):
   linear regression, ridge, lasso, one tree, random forest, gradient boosting, a small neural network.
3. **Tuning:** small grids on the same folds; the default setting competes with the grid (D46, D47).
4. **Horse race and diagnostics** (step 6): why trees lose with the spread as target (6b); how much these features
   can explain (6c).
5. **Second round** (6d, 6e; D47): every model trained on the deviation from the market median
   (`spread_pp - mkt_spread_t2_all`); prediction = predicted deviation + median; scored on the spread as before.
6. **Critical check of the residual target** (6f, D47): pass-through of the market level and bias per quarter.
7. **Optional features** (step 7, D48): `has_revolver`, `has_delayed_draw`, `n_family_bdcs` added to the three best
   residual models, tuned settings kept; which of them every user knows at the cutoff (7b, D51); the complete race in
   one figure (7c).
8. **Main model** (step 8, D49, D51): chosen by the owner on the validation folds before any test prediction;
   feature importance from the model refitted on all training loans.
9. **Test predictions** (step 9, D50) of every candidate, protocol D41; no test error computed.
10. **Robustness predictions** (step 10, D50) of the main model and baseline 1 on the two robustness files.

## 3. Results on the validation quarters (675 loans; MAE in bps)
| Candidate | Spread as target | Residual target | Residual + optional features |
|---|---|---|---|
| Random forest | 85.4 | 59.3 | 54.6 (with `n_family_bdcs`); **54.9** without it (main model) |
| Gradient boosting | 86.7 | 58.3 | 57.3 |
| Neural network | 126.6 | 60.8 | 68.3 |
| Ridge | 72.1 | 64.7 | |
| Lasso | 68.5 | 66.4 | |
| Tree | 89.0 | 68.6 | |
| Linear regression | 74.9 | 74.9 | |
| Baseline 1: market median t-2 | 78.6 | | |
| Baseline 2: sector x size median | 98.3 | | |
| Reference: training mean | 96.0 | | |

- With the spread as target, lasso is best (68.5) and the tree models lose to baseline 1.
- With the residual target, all models beat baseline 1 in all four folds; linear regression is identical in both
  rounds by construction (the market median is a feature).
- With the optional features, the random forest improves from 59.3 to 54.6 bps, in each of the four folds; without
  `n_family_bdcs`, which only the lender knows (7b), it reaches 54.9 (63.0% within 50 bps).
- Tuning gains larger than the fold spread only for lasso (the default alpha removes every coefficient) and for ridge
  and lasso on the residual target; elsewhere tuning polishes (deck 16).
- Figure: `output/figures/horse_race_validation.png` (all 21 candidates; colour and shape mark the round; the main
  model is marked).

## 4. Findings
- **The market level carries most of the predictable signal.** Baseline 1 beats the sector x size median by 20 bps
  because spreads fell from about 6.25 pp (2023) to 4.75 pp (2025) and a four-quarter window lags.
- **Trees cannot follow a falling market.** In every fold the market features of the validation quarter lie outside
  the training range; trees predict averages of training loans and stay too high. Training on the deviation from the
  market median removes the problem (boosting 86.7 -> 58.3, forest 85.4 -> 59.3 bps).
- **Deal structure adds information.** Whether the borrower also has a revolver or delayed-draw line lowers the
  forest's error by 4.4 bps (59.3 -> 54.9), in every fold; the number of the manager's BDCs holding the loan adds only
  0.3 bps more and is known to the lender only (D51).
- **A floor from missing borrower data.** No overfitting (lasso training 63 to 69 bps, validation 65 to 70 bps).
  Knowing the true quarter median still leaves 74 to 83 bps; a lasso fitted on the validation quarter itself reaches
  55 to 59 bps (the limit for linear models). Leverage, earnings and sponsor, which drive spreads, are not in the
  filings.
- **Where the error sits.** Spreads at or below 4 pp and above 7 pp are pulled towards the middle; for lasso, 10% of
  loans with errors above 150 bps carry 31% of the error.
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
  low in every validation quarter (mean error +8 to +24 bps); baseline 1, lasso and the residual neural net err in
  both directions. A rising market would increase this bias. (3) Feature importances of a residual model describe
  the premium, not the spread level.

## 6. Main model (step 8, D49 and D51)
- **Random forest on the residual target with the committed features plus `has_revolver` and `has_delayed_draw`**
  (300 trees, `max_features` 0.33, `min_samples_leaf` 1, seed 42), chosen by the notebook 02 owner before any test
  prediction. Specification: `output/tables/model_choice.csv`.
- **Why:** E10 (D49) chose the random forest with the optional features (54.6 bps): lowest validation MAE, lower than
  the forest without them in each fold, ahead of baseline 1 on both metrics. E11 (D51) dropped `n_family_bdcs`, which
  the lender knows but a sponsor or CFO does not: 54.9 bps (24 below baseline 1), 63.0% within 50 bps against 58.4%
  for baseline 1; the 0.3 bps gap is far below the fold spread (7.3), and the model is valid for every named user.
  Alternatives within the fold spread: boosting (both variants), forest without optional features, residual neural
  net; none is simpler. Ridge (64.7) is further away than the fold spread.
- **Known weakness:** predicted too low in each validation quarter (+8 / +18 / +13 / +24 bps; section 5).
- **What it uses** (feature importance, deck 17, refitted on all training loans; it explains the premium over the
  market median, is predictive, not causal, and favours continuous features, so read it as a ranking): tenor 0.24,
  hold size 0.24, manager family 0.16, revolver 0.09, sector 0.08, market features 0.04 to 0.05 (the market level is
  already in the residual target), lien 0.03, delayed draw 0.02.
  Figure: `output/figures/feature_importance_main_model.png`.

## 7. Predictions handed over to notebook 03 (steps 9 and 10, D50)
| File | Content |
|---|---|
| `data/processed/predictions_validation.csv` | 21 candidates (models, baselines, reference) x 675 validation loans (`fold` 0 to 3) |
| `data/processed/predictions_test.csv` | the same 21 candidates and the main model fitted once up to 2025Q1 ("[single fit to 2025Q1]", secondary view of D41) x 583 test loans (`fold` = "test"); protocol D41: one fit per test quarter on loans up to t-2 filed before t |
| `data/processed/predictions_robustness.csv` | main model and baseline 1 on `loans_all_bdc.csv` (without sector; 2,261 test loans) and `loans_incl_refi.csv` (759), column `dataset` |

Columns as in section 1. Notebook 03 computes every test metric (MAE overall, by test quarter and by manager family,
share within 50 bps, mean error by quarter for the bias of section 5) and the syndicated-loan sensitivity (subset
`n_other_families_same_q < 3`, join on `loan_id` with `loans.csv`). The main model is fixed (D49, D51): changing it after
looking at test errors would turn the test quarters into validation data.

## 8. Checks
Fold construction (gap, filing dates) asserted; no never-feature among the features (incl. the optional ones); every
candidate predicts every validation loan once; baseline 2 recomputed by separate code for all 675 loans; predictions
within 1 to 15 pp; best ridge and lasso alpha inside their grids; tuning never ends below the default; the recorded
main-model specification reproduces its validation MAE; a full rerun of the notebook reproduces all 13,500
validation predictions; two full runs give byte-identical output files (D50); `main.ipynb` runs notebook 02 and checks its outputs; every test training set ends at t-2
and was filed before t; every candidate predicts every test and robustness loan exactly once; no test error is
printed in 02; every main-model feature is marked as known at the cutoff for every named user in `data_dictionary.csv` (D51).

## 9. Decisions for team review (`docs/decisions.md`)
D45 working rules for 02/03; D46 small choices in steps 2 to 6; D47 residual target as second round
(**consequential**, model specification, with the critical assessment); D48 optional features; D49 main model
(**consequential**); D50 test and robustness predictions; D51 main model without the lender-only feature
`n_family_bdcs` (**consequential**).

## 10. Open risks
- **Selection optimism:** about 20 model variants were compared on the same four quarters; the best validation score is
  optimistic. The test quarters give the honest number.
- Four validation quarters only; differences below about 6 to 8 bps are within the spread across the folds.
- Tree-based residual models, including the main model: inherited bias from a falling market (section 5).
- 61 validation loans belong to a manager family not seen in their training fold (pooled infrequent category).
- The early-stopping holdout of the neural net is drawn at random within the training fold (D46).
