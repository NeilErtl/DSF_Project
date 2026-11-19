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
   (1.9% empty; median quarter-to-quarter persistence 0.91). A second pass removes display names glued in front of
   the legal name (repeated names, a stray capital letter from the XBRL member, Apollo/MidCap display names).
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
| Candidate loans (borrower x BDC x quarter, eligible funded line) | 215,157 | 55,200 |
| BDC filed a complete previous quarter | 199,203 | 52,072 |
| Not held by the family before | 14,399 | 4,178 |
| No acquisition date before the quarter | 14,310 | 4,142 |
| One row per borrower x family x quarter | 9,729 | 3,131 |
| Spread 1 to 15 pp, not the all-in rate, no PIK | 9,170 | 3,045 |
| Tenor 4 to 8 years (all-BDC: or unknown) | 8,464 | 2,614 |
| SOFR stated (core) | 8,285 | 2,435 |
| Not an existing loan of an unaffiliated lender | 7,591 | 1,972 |
| Quarters from 2023Q2 | 7,385 | 1,943 |
| Core: industry and maturity known | | **1,798** |

By manager: `output/tables/funnel_by_family.csv`. The new-loan rule is the big cut: portfolios turn over slowly,
so only about 7% of borrower x BDC x quarter lines are new relationships.

## 3. Final sample (`data/processed/loans.csv`)
- **1,798 loans**, 2023Q2 to 2026Q2, 46 BDCs in 31 manager families. Train 1,177 (2023Q2 to 2025Q2), test 621
  (2025Q3 177, 2025Q4 161, 2026Q1 152, 2026Q2 131).
- Largest families: Apollo 20%, Goldman Sachs 11%, BlackRock 8%, Antares 7%, First Eagle 5%.
- **Spread** median 5.00 pp (10th to 90th percentile 3.00 to 6.25). Median by year: 2023 6.25, 2024 5.00,
  2025 4.75, 2026 4.50 pp; the t-2 market median falls from 6.50 (2023Q2) to 4.50 (2026Q2).
- Hold size median USD 10.0m; tenor median 6.2 years; 94% first lien (5% unknown lien).
- 37% of loans are held by three or more other managers in the same quarter (syndicated or club loans):
  flag `n_other_families_same_q`, not a feature.
- Industry-reporting versus all other BDCs (`loans_all_bdc.csv`, 7,385 loans in total): median spread 5.00 vs
  4.75 pp, hold USD 10.0m vs 9.7m, tenor 6.2 vs 6.2 years; for other BDCs the tenor is known for only 17% of loans.

## 4. Validation
- **Precision against acquisition dates** (dated loans after all filters): 94.1% acquired in the quarter of first
  appearance for industry-reporting BDCs (95% CI 90.8 to 96.3%, n = 289), 91.2% for all BDCs; 88% to 100% in the
  four test quarters (26 to 35 dated loans each). Caveat: a date inside the quarter does not prove origination
  (secondary purchases have one too), so this is an upper bound.
- **Hand check of 50 loans** against the EDGAR filings (`docs/hand_check.csv`), stratified by manager, prepared with the AI and re-checked by hand by Mathis on 19 Nov 2026: borrower
  found 50/50, spread 50/50, maturity 49/50, principal 50/50 (the re-check found the principal printed in the
  schedule table for all 50), industry 48/50 (the other two are tagged XBRL values not printed next to the name).
  Classification: (a) originated in the quarter 35, (b) originated earlier and acquired 14, (c) transferred from an
  affiliate 1. The (b) cases led to the existing-loan filter. **Checked loans that remain in the final sample (39):
  (a) 33 = 85% (95% CI 70 to 93%), (b) 5 = 13%, (c) 1 = 3%**, computed by the notebook from the current files
  (step 15e). This is optimistic: the filter was designed on the same loans, and about half of the (a) verdicts
  rest on tenor and the absence of earlier holders rather than a printed date.
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

## 5. Changes of 19 Nov 2026 (re-check of the hand check, borrower-name fix)
- **Hand-check counting.** Matching checked loans to `loans.csv` by `loan_id` missed two loans whose id changed when
  Senior Credit Investments was mapped to Jefferies (the id hashes the family): Solis Mammography and AB Centers
  are in the sample under new ids. The notebook now matches by quarter, family, a distinctive name word and the same
  maturity or spread, so the count no longer depends on ids or name spelling. Principal corrected to 50/50.
- **Borrower names.** Before the fix, 140 core names carried a repeated display name ("Regis Regis Corporation"),
  7 a stray capital letter ("VWhite Cap Buyer LLC") and 9 an industry fragment ("Services ...", "Equipment and
  Supplies ..."); after the fix 0, 1 and 0. Causes: Apollo/MidCap write a display name before the legal name
  ("Sterling Pharm Saffron Bidco Ltd", "Parexel Pheoenix Newco"), the XBRL member names of some Goldman Sachs and
  AllianceBernstein filings start with a stray letter, and a learned category prefix could cut an industry label in
  two. The printed tables of the filings show the correct names (e.g. "White Cap Buyer LLC", "Parexel Phoenix
  Newco, Inc."). Fix: industry labels removed before and after category prefixes ("and" = "&"), plus a second
  naming pass (D28).
- **Effect on the sample.** Core 1,826 -> 1,798 loans (train 1,197 -> 1,177, test 629 -> 621): 32 loans left,
  4 entered, and 253 kept their terms but got a corrected name. The 32 that left are mostly Apollo loans whose clean
  legal name now matches an earlier holding, either of the family itself (e.g. Garda World, held by Apollo since
  2023Q1; Saffron Bidco, held since 2024Q3) or of another lender with the same maturity (existing-loan filter). The
  4 that entered are BlackRock loans whose industry was glued to the name before, so no industry was found. The
  new-loan checks therefore became stricter: two hand-checked (a) loans (GardaWorld, Saffron) turned out not to be
  new for their family, and one (b) loan (White Cap) is now removed. Medians are unchanged (spread 5.00 pp, tenor
  6.2 years) and so is the precision against acquisition dates (94.1%).

## 6. Consequential decisions for team review (details in `docs/decisions.md`)
- **D3** main universe widened from 16 BDCs to all industry-reporting BDCs (about 680 -> 1,798 loans).
- **D8** tenor 4 to 8 years; **D14** sample from 2023Q2; **D22** existing loans of other lenders excluded;
  **D27** PIK loans excluded.
- **D23** target wording: the hand check gives 85% originations with a confidence interval reaching below 80%, so,
  following our commitment, we describe the target as **"the spread of loans newly added to a BDC portfolio
  (mostly new originations)"**.
- **D25** broadly syndicated loans are kept; their share rises over time (spread at most 3.5 pp: 2% of 2023 loans,
  26% of 2026 loans), so train and test differ in composition.

## 7. Open risks
- About one in seven loans is probably not a fresh origination (secondary purchase, or transfer from an affiliated
  private fund, which BDC filings cannot reveal).
- Syndicated versus direct-lending mix (D25); the manager family and the flag capture part of it.
- Hold size is measured at the reporting date and is the lender's hold, not the facility size.
- Borrower names come from a parser; rare parse errors can split or merge borrowers. A borrower renamed after a
  merger (e.g. BlackRock's "Flow Control Group", 2026Q1, and "FCG Acquisitions", 2026Q2, same maturity and spread)
  is counted twice; a rule "same maturity and spread held earlier" was tested and rejected (it mostly matched
  different borrowers).
- Newness of a loan (and so the t-2 market median) is decided partly with later filings' comparative columns, and
  the set of industry-reporting BDCs is chosen on all quarters. Both affect sample construction only.
- First appearance can trail the signing by up to a quarter (late settlement), so the cutoff can be slightly late.

## 8. Recommendations for notebook 02
- Split: `split` column; inside train expanding windows by `q_index` with a one-quarter gap (train up to t-2,
  validate on t).
- Baselines: (1) `mkt_spread_t2_all` (t-2 median, filed before the cutoff); (2) median by `sector` and size class
  over the previous four available quarters, with the same t-2 rule inside each fold.
- Features: `log_principal`, `tenor_years`, `sector`, `lien`, `family`, `baa_spread_prev`, `sofr_prev`,
  `mkt_spread_t2_all`; optional `has_revolver`, `has_delayed_draw`, `n_family_bdcs`. Encoding and scaling inside
  the pipeline. Report MAE by test quarter and by family; sensitivity without syndicated loans
  (`n_other_families_same_q >= 3`); robustness on `loans_all_bdc.csv` without industry.
