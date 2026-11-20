# Data report: working dataset of newly originated private credit loans

Notebook: `code/01_preprocess.ipynb` (runs top to bottom). Decisions with evidence: `docs/decisions.md`. Every number
below is in `output/tables/headline_numbers.csv` or the tables named next to it. Use of the data in notebooks 02 and
03: `docs/for_modelling.md`.

## 1. Task as understood
- **Question.** Predict the spread over SOFR of a newly originated US private credit loan held by a BDC, so that a
  deal team (or sponsor / CFO) has a market-based reference price before the term sheet is signed.
- **Unit.** One new loan = one borrower x one manager family x one quarter of first appearance. New = no BDC of the
  same family held the borrower before; loans with an acquisition date before that quarter are dropped; borrowers
  seen earlier at unaffiliated BDCs are flagged.
- **Target.** Spread over SOFR of newly originated loans, in percentage points (errors in basis points). The hand
  check finds about 86% true originations (95% CI 72 to 94%); the remaining loans are newly added to a BDC portfolio
  through purchases or transfers. An out-of-sample verification of 30 further loans by a fresh AI agent finds 80% (95% CI 63 to 90%; 79% on the
29 still in the sample), so the share is close to the 80% threshold of the commitment.
- **Cutoff.** Start of the quarter of first appearance. Market-level spread from quarter t-2 filings (checked with
  the filing date); external market data: last value before the cutoff. Never features: interest rate, fair value,
  cost, PIK, floor.
- **Split, baselines, metrics.** As committed: test = 2025Q3 to 2026Q2 (used once), expanding-window validation
  with a one-quarter gap; baselines (1) t-2 median and (2) median by sector and size class; MAE in bps, share
  within plus or minus 50 bps, MAE by test quarter and manager. No model fitting in this step.

## 2. What was done
1. **Data.** 23 SEC BDC data set zips (filings submitted Oct 2022 to Oct 2026) and 3 FRED series, downloaded by
   code. Current-period rows of `soi.tsv`, one filing per BDC and quarter (latest filed), quarters 2022Q3 to 2026Q2,
   204 registrants mapped to manager families by explicit rules.
2. **Borrowers.** A parser learns each BDC's identifier format and extracts the borrower name (1.9% empty); a second
   pass removes display names and stray letters glued to the legal name (D28).
3. **New loans.** No BDC of the same family held the borrower in any earlier quarter, checked on current holdings and
   the prior-period comparatives of every filing, with rarity-weighted name matching plus an exact-name check. The
   BDC must have filed a complete previous quarter; loans with an acquisition date before the quarter are dropped;
   one row per borrower x family x quarter.
4. **Loan line.** Per borrower the funded SOFR term line with the largest held principal (a borrower with only
   committed lines enters in its pricing quarter, flagged). Excluded: revolvers, delayed-draw and other unfunded
   lines, non-USD, Prime/LIBOR, structured products, joint-venture lines. Hold size sums the loan's tranches.
5. **Filters.** Spread 1 to 15 pp and not the all-in rate; no PIK; hold at least USD 100,000; tenor 4 to 8 years;
   not an existing loan of an unaffiliated lender; one spread across tranches; no near match at the family; quarters
   from 2023Q2; core = BDCs that state borrower industries, with industry and maturity known.
6. **Features** (known at the start of the quarter): log hold size, tenor, sector (11), lien, manager family, Baa
   spread and SOFR before the cutoff, median new-loan spread of quarter t-2 (filings filed before the cutoff).

## 3. Funnel (all BDCs / core sample; `output/tables/funnel.csv`)
| Step | All BDCs | Core |
|---|---:|---:|
| Candidate loans (borrower x BDC x quarter, eligible line) | 214,271 | 54,743 |
| BDC filed a complete previous quarter | 198,354 | 51,642 |
| Not held by the family before | 14,402 | 4,183 |
| No acquisition date before the quarter | 14,313 | 4,147 |
| One row per borrower x family x quarter | 9,706 | 3,109 |
| Spread, all-in rate, PIK, hold, tenor, SOFR filters | 8,246 | 2,411 |
| Not an existing loan of an unaffiliated lender | 7,558 | 1,951 |
| Tranche and near-match rules | 7,509 | 1,920 |
| Quarters from 2023Q2 | 7,303 | 1,891 |
| Core: industry and maturity known | | **1,747** |

## 4. Final sample (`data/processed/loans.csv`)
- **1,747 loans**, 2023Q2 to 2026Q2, 31 manager families. **BDC counts:** each loan has one lead BDC (the family's
  BDC with the largest position, column `cik`); the lead BDCs are 45 distinct BDCs (48 names, because some BDCs were
  renamed). Counting also the other BDCs of the family that hold the loans: 61 BDCs. Universe: 67 BDCs that state
  borrower industries.
- Train 1,143 (2023Q2 to 2025Q2), test 604 (2025Q3 174, 2025Q4 152, 2026Q1 151, 2026Q2 127). The final model with
  the one-quarter gap trains on 1,000 loans (to 2025Q1).
- Largest families: Apollo 19%, Goldman Sachs 11%, BlackRock 7%, Antares 7%, First Eagle 5%.
- Spread median 5.00 pp (2023 6.25, 2024 5.00; the notebook also shows test-period years as descriptives: no rule
  or threshold was set on them, and they must not guide model choices); hold median USD 10.5m; tenor median 6.2 years;
  93% first lien (6% unknown: Stellus, TCW, Onex write no lien in the line). 38% of loans are held by three or more other families in the same quarter (syndicated or club
  loans; flag `n_other_families_same_q`).
- Robustness files: `loans_all_bdc.csv` 7,303 loans (other BDCs: median spread 4.75 pp, tenor known for 16%);
  `loans_incl_refi.csv` 2,185 loans, of which 390 refinancings/add-ons and 57 with tenor 3 to 4 years (D35).

## 5. Validation
- **Precision against acquisition dates** (dated loans after all filters): 94.6% acquired in the quarter of first
  appearance (95% CI 91.2 to 96.7%, n = 276). An upper bound: a purchase also has a date in the quarter.
- **Our hand check of 50 loans** (`docs/hand_check.csv`, stratified by family, re-checked by Mathis): borrower,
  spread and principal found 50/50, maturity 49/50. In the 37 that remain in the final sample: (a) originated in the
  quarter 32 = 86% (95% CI 72 to 94%), (b) bought later 4, (c) affiliate transfer 1. Optimistic: the existing-loan
  filter was designed on these loans.
- **Patrick's independent hand check** (`docs/hand_check_patrick.csv`, 50 loans of 8 managers): 27 are in our final
  sample, (a) 26, (b) 1; our filters remove 8 of his 9 (b) loans. Both checks combined, each loan once: (a) 58 of
  64 = 91% (95% CI 81 to 96%). See D23.
- **Out-of-sample verification of 30 further loans** (`docs/verification_sample_30.csv`, seed 2026, stratified by
  family, excluding both hand checks, checked in EDGAR by a fresh agent): borrower, spread, maturity and principal
  correct 30/30, lien 27 (2 not printed, 1 wrong); (a) 24 of 30 = 80% (95% CI 63 to 90%), (b) 5, not new 1; drawn
  before D37/D40, 29 still in the sample, of which 23 (a) = 79%. Errors
  found: WhiteHorse joint-venture lines counted as BDC holdings (fixed, 18 loans removed, D40); a rename after a
  restructuring (Crescent "Affordable Care", limitation); Stellus, TCW and Onex lien not written in the line.
- **Leakage and cutoff audit** by a fresh reviewer: one small real leak fixed (fair value replaced an implausible
  principal for 34 loans, D37), otherwise none; FRED and t-2 features recomputed exactly.
  Fixed also: training rows must
  also be filed before the cutoff (D38); the cutoff checks now cover every quarter. Documented: sample construction
  uses later filings (name rarity, comparatives), FRED dates are observation dates (D38).
- **Cutoff:** FRED values strictly before the quarter start and t-2 loans filed before the quarter start (asserted);
  never-feature columns marked in `data_dictionary.csv`.
- **Reviews and reproducibility:** three adversarial reviews (findings and fixes in `docs/ai_audit_trail.md`); one
  row per family x quarter x borrower (asserted); stable `loan_id`; two Restart-Run-All runs give identical files.

## 6. Consequential decisions for team review (`docs/decisions.md`)
D3 universe (industry-reporting BDCs), D4 new-loan rule, D8 tenor 4 to 8 years, D14 start 2023Q2, D17 no secondary-buyer family
excluded, D22 existing loans of other lenders dropped, D23 target wording with caveat, D25 syndicated loans kept, D28 second naming pass,
D27 PIK excluded, D31 near-match rule, D32 unfunded lines, D35 refinancings only in the variant file, D37 hold size
without fair value, D40 joint-venture schedules excluded.

## 7. Open risks
- About one in seven loans may not be a fresh origination (secondary purchase, or transfer from an affiliated private
  fund, which BDC filings cannot reveal).
- Syndicated versus direct-lending mix: 38% of loans are held by three or more other families, and the share of
  low-spread loans rises over time, so train and test may differ in composition (D25).
- Hold size is measured at the reporting date and is the lender's hold, not the facility size.
- Borrower names come from a parser; a borrower renamed after a merger can be counted twice.
- Newness (and so the t-2 market median) is decided partly with later filings' comparative columns, and the set of
  industry-reporting BDCs is chosen on all quarters; both affect sample construction only, not feature values.
- First appearance can trail the signing by up to a quarter, so the cutoff can be slightly late.
