# Evaluation report: the main model on the test quarters (notebook 03)

Notebook: `code/03_evaluate.ipynb` (runs top to bottom, fits no model). Decision: `docs/decisions.md`, D52.
Counterpart of `docs/data_report.md` (notebook 01) and `docs/model_report.md` (notebook 02). Every number below comes
from the tables in `output/tables/`: `test_headline.csv`, `test_by_quarter.csv`, `test_bootstrap.csv`,
`test_by_family.csv`, `test_all_candidates.csv`, `test_single_fit.csv`, `test_sensitivity_robustness.csv`,
`test_robustness_bootstrap.csv`; figures in `output/figures/`: `test_by_quarter.png`, `spread_over_time.png`,
`validation_vs_test.png`, `error_distribution.png`, `robustness_gap.png` (D53).

**Status (22 Nov 2026):** notebook 03 complete; the test quarters have been evaluated once. The main model was fixed
in notebook 02 before any test prediction (D49, D51) and is not changed after this evaluation.

## 1. Task as understood
- **Evaluate** the main model (random forest on the residual target with the committed features plus
  `has_revolver` and `has_delayed_draw`) and the committed baselines on the four test quarters 2025Q3 to 2026Q2
  (583 new loans), with the committed metrics: MAE in bps (main), share within plus or minus 50 bps, overall, by test
  quarter and by manager family.
- **Protocol (D41):** each test quarter t was predicted by a model trained on loans up to t-2 filed before t
  (written by notebook 02). Notebook 03 only reads the predictions.
- **Presentation (D52, owner's choice E12):** main model, baselines and reference in front; all 21 candidates of the
  validation race shown for description only. **Uncertainty (E13):** paired bootstrap within test quarters.

## 2. Headline result (583 test loans)
| Candidate | Test MAE (bps) | Within 50 bps | Mean error (bps) | Validation MAE (bps) |
|---|---|---|---|---|
| **Main model** (random forest, residual target) | **58.1** | **55.4%** | -1.7 | 54.9 |
| Baseline 1: market median t-2 | 86.3 | 50.3% | -27.8 | 78.6 |
| Baseline 2: sector x size median | 79.9 | 53.7% | -24.0 | 98.3 |
| Reference: training mean | 92.3 | 45.1% | -57.0 | 96.0 |

Mean error = actual minus predicted spread; negative = predicted too high.

- **The model beats both baselines.** Gap to baseline 1: **-28.2 bps** (95% interval -33.3 to -23.1); to baseline
  2: -21.8 bps (-26.7 to -17.0). In all 2,000 bootstrap draws the model is better.
- **Little optimism from model selection.** The test MAE is 3.2 bps above the validation MAE, although about 20
  variants were compared on the validation quarters. Baseline 1 worsened by 7.7 bps over the same step.
- **The two baselines swap places.** On validation the sector x size median was 20 bps worse than the market median;
  on test it is 6 bps better. Both predict too high on average (spreads kept falling, and a lagged median follows
  with a delay).

## 3. By test quarter
| Quarter | Loans | Main model | Baseline 1 | Baseline 2 | Gap main - B1 | Mean error main |
|---|---|---|---|---|---|---|
| 2025Q3 | 164 | 54.3 | 82.0 | 82.0 | -27.7 | +5.6 |
| 2025Q4 | 149 | 48.1 | 68.5 | 67.5 | -20.4 | -5.9 |
| 2026Q1 | 147 | 61.9 | 97.6 | 84.6 | -35.7 | -22.1 |
| 2026Q2 | 123 | 70.6 | 100.0 | 86.5 | -29.4 | +18.2 |

- The model is better than both baselines **in every test quarter**; the gap to baseline 1 ranges from 20 to 36 bps.
- Errors rise towards 2026 for every candidate: the later the quarter, the further it lies from most training data.
- **The validation bias does not persist.** On validation the main model predicted too low in every quarter (+8 to
  +24 bps, D47). On test the sign changes: too high in 2026Q1 (-22), too low in 2026Q2 (+18). The bias was a
  feature of a falling market; on the test quarters the model errs in both directions. A rising market would still
  be a risk (`docs/model_report.md`, section 5).

## 4. By manager family
- Of the 9 families with at least 20 test loans (385 loans), the model beats baseline 1 in 7. The exceptions:
  Jefferies (42.5 against 30.4 bps) and Varagon (equal, 43.8).
- The largest errors: AllianceBernstein (57 loans, 81.6 bps, mean error -49: predicted too high) and First Eagle
  (18 loans, 104.8 bps). For AllianceBernstein, baseline 1 is even further off (149.8 bps).
- Families with fewer than 20 test loans give noisy MAEs (full table: `test_by_family.csv`).

## 5. All candidates (description only, no choice)
- The main lesson of notebook 02 holds on the test quarters: the tree models and the neural net gain 9 to 24 bps
  from the residual target (tree 95.2 -> 71.6, forest 76.0 -> 63.2, boosting 72.5 -> 62.6, net 77.3 -> 63.1). For
  the linear models the target hardly matters (ridge 66.0 against 67.6, lasso 69.5 against 68.9; linear regression
  identical by construction), because the market median is already one of their features.
- The main model is among a group of close candidates: forest with all optional features 57.3, boosting with
  optional features 57.6, main model 58.1. These differences (below 1 bps) are far within the validation fold
  spread (7.3 bps) and are not a reason to change the model (D49, D51).
- Some linear models did better on test than on validation (linear regression 64.0 against 74.9), so the gap
  between linear and tree-based residual models narrows to about 6 bps.

## 6. Secondary protocol and robustness
| Variant | Loans | Main model | Baseline 1 | Gap |
|---|---|---|---|---|
| Main sample, main protocol | 583 | 58.1 | 86.3 | -28.2 |
| Main model fitted once up to 2025Q1 (D41) | 583 | 57.2 | | |
| Without likely syndicated loans (D25) | 336 | 55.2 | 79.6 | -24.4 |
| All BDCs, without sector | 2,261 | 73.1 | 100.9 | -27.8 |
| Incl. refinancings, add-ons, tenor 3-4 years | 759 | 62.4 | 95.5 | -33.1 |

- **Refitting each quarter does not pay off here**: one fit up to 2025Q1 gives 57.2 bps (identical in 2025Q3 by
  construction, slightly better in 2025Q4 and 2026Q1, worse in 2026Q2). The difference is small; the main protocol
  stays as committed.
- **The gap to baseline 1 keeps its sign and size in every variant**, and no 95% interval touches zero
  (`test_robustness_bootstrap.csv`, figure `robustness_gap.png`): without likely syndicated loans -24.4 [-30.7,
  -18.5], all BDCs -27.8 [-30.4, -25.1], incl. refinancings -33.1 [-37.9, -28.5]. On all BDCs (no sector, tenor imputed for many
  loans) both errors are larger, but the model still gains 28 bps. The result does not hinge on the
  industry-reporting universe or on the sample definitions D25 and D35.

## 7. What this means for the user
- A deal team using the model instead of last-but-one quarter's market median would be about 28 bps closer to the
  actual spread on average, and the gain shows up in every test quarter and in most large manager families.
- **Still, one loan in two is priced outside plus or minus 50 bps** (55% within). Leverage, earnings and sponsor
  quality, which drive spreads, are not in the filings; the model is a market-based reference point, not a price.

## 8. Limitations
- **Four test quarters.** The bootstrap treats loans of one quarter as independent, although they share a market:
  the interval is too narrow if anything. The four per-quarter gaps (all negative) are the more robust evidence.
- **Target interpretation.** About 90% of checked loans are true originations (127 of 141 distinct loans over four
  checks, `docs/data_report.md`); the rest are purchases or transfers newly priced into a BDC portfolio.
- **Small families.** MAEs of families with few test loans are indications only.
- **Market direction.** The training data cover a falling market. The model passes the market level through
  one-for-one (residual target); its behaviour in a rising market is not tested.

## 9. Figures for the report and slides (step 9, D53)
| Figure | Shows | Use |
|---|---|---|
| `spread_over_time.png` | Median spread of new loans fell from 6.75 to 4.75 pp; spread minus market level t-2 stays between -0.75 and +0.25 pp | Why the models predict the residual (D47) |
| `validation_vs_test.png` | Validation and test MAE of all 21 candidates, sorted by validation MAE | Optimism of the validation numbers; no choice on test |
| `error_distribution.png` | Errors of the main model and baseline 1; 55% against 50% within 50 bps | Where the gain comes from: fewer large errors |
| `robustness_gap.png` | Gap to baseline 1 with 95% interval in four sample variants | The result does not hinge on the sample definition |
| `test_by_quarter.png` | MAE and mean error per test quarter | Gain in every quarter |

## 10. Checks
Every candidate predicts every test loan exactly once; actual spreads equal `loans.csv`; stored absolute errors
equal the recomputed ones; the validation MAE of the main model equals `model_choice.csv`; loan-weighted quarter
MAEs equal the pooled MAE; the bootstrap point estimate equals the table gap; both protocols give identical
predictions in 2025Q3; the robustness files contain test quarters only, one prediction per loan; two full runs give
identical tables; the recorded main model is unchanged at the end of the notebook.
