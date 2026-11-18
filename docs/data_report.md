# Data report: working dataset of newly added private credit loans

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
   code. We keep the current-period rows of `soi.tsv`, one filing per BDC and quarter (12 amendments replaced),
   quarters 2022Q3 to 2026Q2 (204 registrants, mapped to manager families by explicit rules).
2. **Borrowers.** The borrower is written inside a free-text identifier whose format differs by manager. A parser
   learns each BDC's format (category headers, industry labels, delimiters, footnotes) and extracts the name
   (1.9% empty; median quarter-to-quarter persistence 0.91).
3. **New loans.** New = no BDC of the same family held the borrower in any earlier quarter. "Held" is checked on
   current holdings **and** the prior-period comparatives of every filing, with a rewording-robust rule (distinctive
   words of the name weighted by rarity) plus an exact-name check. The BDC must have filed a complete previous
   quarter; loans with an acquisition date before the quarter are dropped; one row per borrower x family x quarter.
4. **Loan line.** Per borrower the funded SOFR term line with the largest held principal. Excluded: revolvers,
   delayed-draw lines, unfunded commitments, non-USD, Prime/LIBOR, structured products, lines of a tagged joint
   venture. Principal is checked against fair value (unit errors rescaled).
5. **Filters.** Spread 1 to 15 pp and not equal to the all-in rate; no PIK; tenor 4 to 8 years; not an existing
   loan of an unaffiliated lender (same maturity held earlier, or held earlier with tenor below 5 years);
   quarters from 2023Q2.
6. **Features** (all known at the start of the quarter): log hold size, tenor, sector (11), lien, manager family,
   Baa spread and SOFR before the cutoff, median new-loan spread of quarter t-2 (filings filed before the cutoff).

## 2. Funnel (all BDCs / core sample)
| Step | All BDCs | Core |
|---|---:|---:|
| Candidate loans (borrower x BDC x quarter, eligible funded line) | 215,137 | 55,205 |
| BDC filed a complete previous quarter | 199,186 | 52,077 |
| Not held by the family before | 14,443 | 4,217 |
| No acquisition date before the quarter | 14,353 | 4,181 |
| One row per borrower x family x quarter | 9,771 | 3,170 |
| Spread 1 to 15 pp, not the all-in rate, no PIK | 9,212 | 3,083 |
| Tenor 4 to 8 years (all-BDC: or unknown) | 8,499 | 2,646 |
| SOFR stated (core) | 8,320 | 2,467 |
| Not an existing loan of an unaffiliated lender | 7,633 | 2,010 |
| Quarters from 2023Q2 | 7,427 | 1,981 |
| Core: industry and maturity known | | **1,826** |

By manager: `output/tables/funnel_by_family.csv`. The new-loan rule is the big cut: portfolios turn over slowly,
so only about 7% of borrower x BDC x quarter lines are new relationships.

## 3. Final sample (`data/processed/loans.csv`)
- **1,826 loans**, 2023Q2 to 2026Q2, 47 BDCs in 31 manager families. Train 1,197 (2023Q2 to 2025Q2), test 629
  (2025Q3 181, 2025Q4 163, 2026Q1 152, 2026Q2 133).
- Largest families: Apollo 21%, Goldman Sachs 11%, BlackRock 7%, Antares 7%, First Eagle 5%.
- **Spread** median 5.00 pp (10th to 90th percentile 3.00 to 6.25). Median by year: 2023 6.25, 2024 5.00,
  2025 4.75, 2026 4.50 pp; the t-2 market median falls from 6.50 (2023Q2) to 4.50 (2026Q2).
- Hold size median USD 10.0m; tenor median 6.2 years; 94% first lien (5% unknown lien).
- 35% of loans are held by three or more other managers in the same quarter (syndicated or club loans):
  flag `n_other_families_same_q`, not a feature.
- Industry-reporting versus all other BDCs (`loans_all_bdc.csv`, 7,427 loans in total): median spread 5.00 vs
  4.75 pp, hold USD 10.0m vs 9.7m, tenor 6.2 vs 6.2 years; for other BDCs the tenor is known for only 17% of loans.

## 4. Validation
- **Precision against acquisition dates** (dated loans after all filters): 94.1% acquired in the quarter of first
  appearance for industry-reporting BDCs (95% CI 90.8 to 96.3%, n = 289), 91.2% for all BDCs; 88% to 100% in the
  four test quarters (26 to 35 dated loans each). Caveat: a date inside the quarter does not prove origination
  (secondary purchases have one too), so this is an upper bound.
- **Hand check of 50 loans** against the EDGAR filings (`docs/hand_check.csv`), stratified by manager: borrower
  found 50/50, spread 50/50, maturity 49/50, principal 47/50, industry 48/50 (the rest are tagged values not
  printed next to the name). Classification: (a) originated in the quarter 35, (b) originated earlier and acquired
  14, (c) transferred from an affiliate 1. The (b) cases led to the existing-loan filter. **Loans of the check that
  remain in the final sample (41): (a) 83% (95% CI 69 to 92%), (b) 15%, (c) 2%.** This is optimistic: the filter
  was designed on the same loans, and about half of the (a) verdicts rest on tenor and the absence of earlier
  holders rather than a printed date.
- **Adversarial review** by a fresh AI agent: 9 findings (duplicated manager families, joint-venture lines,
  unfunded commitments, principal and rate units, numeric "borrowers", PIK, syndicated mix, hand-check optimism).
  All fixed except the syndicated mix (D25) and the limits of the hand check, which are documented. A guard now
  checks that no two families share more than half of their new loans (largest overlap after the fix: 19%).
- **Units:** tagged spread equals the spread written in the text for about 99% of loans (rest: text typos); rates
  converted per filing and per column; principal/fair value ratio between 0.5 and 2 for every core loan.
- **Cutoff:** FRED values strictly before the quarter start and t-2 loans filed before the quarter start
  (asserted; t-2 median recomputed by hand for one quarter). Interest rate, fair value, cost, PIK and floor are kept
  only as descriptive columns and marked "NEVER a feature" in `data_dictionary.csv`.
- **Keys and reproducibility:** one row per family x quarter x borrower, no borrower repeated within a family
  (asserted); stable `loan_id`; two consecutive Restart-Run-All runs give identical output files.

## 5. Consequential decisions for team review (details in `docs/decisions.md`)
- **D3** main universe widened from 16 BDCs to all industry-reporting BDCs (about 680 -> 1,826 loans).
- **D8** tenor 4 to 8 years; **D14** sample from 2023Q2; **D22** existing loans of other lenders excluded;
  **D27** PIK loans excluded.
- **D23** target wording: the hand check gives 83% originations with a confidence interval reaching below 80%, so,
  following our commitment, we describe the target as **"the spread of loans newly added to a BDC portfolio
  (mostly new originations)"**.
- **D25** broadly syndicated loans are kept; their share rises over time (spread at most 3.5 pp: 2% of 2023 loans,
  26% of 2026 loans), so train and test differ in composition.

## 6. Open risks
- About one in six loans is probably not a fresh origination (secondary purchase, or transfer from an affiliated
  private fund, which BDC filings cannot reveal).
- Syndicated versus direct-lending mix (D25); the manager family and the flag capture part of it.
- Hold size is measured at the reporting date and is the lender's hold, not the facility size.
- Borrower names come from a parser; rare parse errors can split or merge borrowers.
- Newness of a loan (and so the t-2 market median) is decided partly with later filings' comparative columns, and
  the set of industry-reporting BDCs is chosen on all quarters. Both affect sample construction only.
- First appearance can trail the signing by up to a quarter (late settlement), so the cutoff can be slightly late.

## 7. Recommendations for notebook 02
- Split: `split` column; inside train expanding windows by `q_index` with a one-quarter gap (train up to t-2,
  validate on t).
- Baselines: (1) `mkt_spread_t2_all` (t-2 median, filed before the cutoff); (2) median by `sector` and size class
  over the previous four available quarters, with the same t-2 rule inside each fold.
- Features: `log_principal`, `tenor_years`, `sector`, `lien`, `family`, `baa_spread_prev`, `sofr_prev`,
  `mkt_spread_t2_all`; optional `has_revolver`, `has_delayed_draw`, `n_family_bdcs`. Encoding and scaling inside
  the pipeline. Report MAE by test quarter and by family; sensitivity without syndicated loans
  (`n_other_families_same_q >= 3`); robustness on `loans_all_bdc.csv` without industry.
