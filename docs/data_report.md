# Data report: working dataset of newly originated private credit loans

Notebook: `code/01_preprocess.ipynb` (runs top to bottom). Decisions with evidence: `docs/decisions.md`.

## 0. Task as understood (restated before building)
- **Question.** Predict the spread over SOFR of a newly originated US private credit loan held by a BDC, so that a
  deal team (or sponsor / CFO) has a market-based reference price before the term sheet is signed.
- **Unit.** One new loan = one borrower x one manager family x one quarter of first appearance. New = no BDC of the
  same family held the borrower before; loans with an acquisition date before that quarter are dropped; borrowers
  seen earlier at unaffiliated BDCs are flagged.
- **Target.** Spread over SOFR in percentage points (errors to be reported in basis points).
- **Cutoff.** Start of the quarter of first appearance. Market-level spread from quarter t-2 filings (checked with
  the filing date); external market data: last value before the cutoff. Never features: interest rate, fair value,
  cost, PIK, floor.
- **Split.** By time: test = 2025Q3 to 2026Q2 (used once), expanding-window validation inside training, one-quarter
  gap (a model for quarter t is trained on loans up to t-2).
- **Baselines.** (1) Median new-loan spread of the reference quarter (t-2 rule); (2) median by sector and size class
  over the previous four available quarters.
- **Metric.** MAE in bps (main), share within +/- 50 bps, MAE by test quarter and by manager.
- **Plan for this step.** Download SEC and FRED data by code; keep one current-period filing per BDC and quarter;
  parse borrower names from the free-text identifiers of all managers; identify new loans at the family level with a
  matching rule that survives rewording; build features known at the cutoff; validate (funnel, precision against
  acquisition dates, hand check of 50 loans, distributions, cutoff checks); have a fresh AI reviewer attack the result.
  No model fitting and no learned preprocessing in this step.

## 1. What was done
1. **Data.** 23 SEC BDC data set zips (filings submitted Oct 2022 to Oct 2026) and 3 FRED series, downloaded by
   code. From `soi.tsv` we keep the current-period rows, one filing per BDC and quarter (12 amendments replaced),
   quarters 2022Q3 to 2026Q2 (176 BDCs with loan lines, 107 families after mapping).
2. **Borrowers.** The borrower is written inside a free-text identifier whose format differs by manager. A parser
   learns each BDC's format (category headers, industry labels, delimiters) and extracts the name (1.6% empty;
   median quarter-to-quarter persistence 0.91).
3. **New loans.** A loan is new when no BDC of the same family held the borrower in any earlier quarter, checked
   with a matching rule that survives rewording (distinctive words of the name, weighted by rarity) on current
   holdings and on the prior-period comparatives of every filing; the BDC must have filed a complete previous
   quarter; loans with an acquisition date before the quarter are dropped; one row per borrower x family x quarter.
4. **Loan line.** Per borrower the funded SOFR term line with the largest held principal; revolvers, delayed-draw
   lines, non-USD, Prime/LIBOR and structured products are excluded.
5. **Filters.** Spread 1 to 15 pp and not equal to the all-in rate; tenor 4 to 8 years; no existing loan of an
   unaffiliated lender (same maturity held earlier, or held earlier with tenor below 5 years); quarters 2023Q2+.
6. **Features** (all known at the start of the quarter): log hold size, tenor, sector (11), lien, manager family,
   Baa spread and SOFR before the cutoff, median new-loan spread of quarter t-2 (only filings filed before the cutoff).

## 2. Funnel (all BDCs / core sample)
| Step | All BDCs | Core |
|---|---:|---:|
| Candidate loans (borrower x BDC x quarter, eligible line) | 216,611 | 56,139 |
| BDC filed a complete previous quarter | 200,596 | 52,979 |
| Not held by the family before | 15,744 | 4,452 |
| No acquisition date before the quarter | 15,640 | 4,409 |
| One row per borrower x family x quarter | 10,843 | 3,435 |
| Spread 1 to 15 pp, not the all-in rate | 10,626 | 3,418 |
| Tenor 4 to 8 years (all-BDC: or unknown) | 9,769 | 2,893 |
| SOFR stated (core) | 9,547 | 2,671 |
| Not an existing loan of an unaffiliated lender | 8,801 | 2,189 |
| Quarters from 2023Q2 | 8,578 | 2,158 |
| Core: industry and maturity known | | **1,991** |

By manager: `output/tables/funnel_by_family.csv`.

## 3. Final sample (`data/processed/loans.csv`)
- **1,991 loans**, 2023Q2 to 2026Q2, 49 BDCs in 32 manager families. Train 1,313 (2023Q2 to 2025Q2), test 678
  (2025Q3 204, 2025Q4 179, 2026Q1 157, 2026Q2 138).
- Largest families: Apollo 19%, Goldman Sachs 10%, BlackRock 7%, Antares 6%, First Eagle 5%.
- **Spread** median 5.00 pp (10th to 90th percentile 3.25 to 6.25). Median by year: 2023 6.25, 2024 5.00,
  2025 4.75, 2026 4.50 pp; the t-2 market median falls from 6.50 (2023Q2) to 4.50 (2026Q2).
- Hold size median USD 9.8m; tenor median 6.2 years; 94% first lien (5% lien unknown); PIK in 1.7%.
- 36% of loans are held by three or more other managers in the same quarter (likely syndicated or club loans):
  flag `n_other_families_same_q`, not a feature.
- Industry-reporting versus all other BDCs (`loans_all_bdc.csv`, 8,578 loans): median spread 5.00 vs 4.75 pp, hold
  USD 9.8m vs 8.4m, tenor 6.2 vs 6.2 years. For other BDCs, tenor is known for only 17% of loans.

## 4. Validation
- **Precision against acquisition dates** (dated loans after all filters): 93.9% acquired in the quarter of first
  appearance (95% CI 90.6 to 96.1%, n = 297) for industry-reporting BDCs, 90.1% for all BDCs; 83% to 100% in the
  four test quarters (26 to 36 dated loans each). Caveat from the hand check: an acquisition date inside the quarter does not prove origination
  (secondary purchases have one too).
- **Hand check of 50 loans** against the EDGAR filings (`docs/hand_check.csv`), stratified by manager: borrower
  found 50/50, spread 50/50, maturity 49/50, principal 47/50, industry 48/50 (the rest are tagged values not
  printed next to the name). Classification: (a) originated in the quarter 35, (b) originated earlier and acquired
  14, (c) transferred from an affiliate 1. The (b) cases led to the existing-loan filter, which removed 8 of the 14
  (b) and none of the (a) loans. **In the final sample: (a) 83% (95% CI 69 to 92%), (b) 14%, (c) 2%.**
- **Units:** tagged spread equals the spread written in the text for 1,917 of 1,931 loans (rest: text typos).
- **Cutoff:** FRED values strictly before the quarter start, t-2 loans filed before the quarter start (asserted);
  t-2 median recomputed by hand for one quarter. Interest rate, fair value, cost, PIK and floor are kept only as
  descriptive columns and marked "NEVER a feature" in `data_dictionary.csv`.
- **Keys:** one row per family x quarter x borrower (asserted); stable `loan_id`.

## 5. Consequential decisions for team review (details in `docs/decisions.md`)
- **D3** main universe widened from 16 BDCs to all industry-reporting BDCs (about 680 -> 1,991 loans).
- **D8** tenor 4 to 8 years; **D14** sample from 2023Q2; **D22** existing loans of other lenders excluded.
- **D23** target wording: 83% originations in the hand check (CI includes values below 80%); we propose
  "spread of loans newly added to a BDC portfolio, mostly new originations" as the honest description.

## 6. Open risks
- About one in six loans is probably not a fresh origination (secondary purchase or transfer from an affiliated
  private fund, invisible in BDC filings).
- Broadly syndicated loans (Apollo, BlackRock, AllianceBernstein, Palmer Square) price tighter than direct-lending
  loans; the manager family absorbs part of this, `n_other_families_same_q` shows it.
- Hold size is measured at the reporting date, not at the term sheet; it is the lender's hold, not the facility.
- Borrower names come from a parser; rare parse errors can split or merge borrowers (low persistence for a few
  small BDCs, `output/tables/borrower_parse_quality.csv`).
- Market conditions: spreads fall steadily over the sample; the test period has the lowest spreads.

## 7. Recommendations for notebook 02
- Split: `split` column; inside train use expanding windows by `q_index` with a one-quarter gap (train up to t-2,
  validate on t).
- Baselines: (1) `mkt_spread_t2_all` (already the t-2 median, filed before the cutoff); (2) median by `sector` and
  size class over the previous four available quarters, computed with the same t-2 rule inside each fold.
- Features: `log_principal`, `tenor_years`, `sector`, `lien`, `family`, `baa_spread_prev`, `sofr_prev`,
  `mkt_spread_t2_all`; optional `has_revolver`, `has_delayed_draw`, `n_family_bdcs`. One-hot encoding and scaling
  inside the pipeline. Report MAE by test quarter and by family; check results without syndicated loans
  (`n_other_families_same_q >= 3`) as a sensitivity analysis; robustness on `loans_all_bdc.csv` without industry.
