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
- **Target.** Spread over SOFR of newly originated loans, in percentage points (errors in basis points). Four
  origination checks: our hand check 32 of 36 (89%), Patrick's first hand check 25 of 26 (96%; loans of his earlier
  preprocessing version), an out-of-sample check 24 of 30 (80%, 95% CI 63 to 90%), and Patrick's hand check v2 of 50
  loans drawn from the final dataset 47 of 50 (94%, 95% CI 84 to 98%); no filter was designed on the last two, so they
  are the cleanest estimates. Over all 141 distinct checked loans in the sample 90% (95% CI 84 to 94%). About one loan
  in five to one in ten may be a purchase or transfer rather than a fresh origination; it is still a loan newly priced
  into a BDC portfolio.
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
2. **Borrowers.** A parser learns each BDC's identifier format and extracts the borrower name (3.2% empty, incl. lines whose parsed name was only an industry label); a second
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
| Candidate loans (borrower x BDC x quarter, eligible line) | 213,660 | 54,450 |
| BDC filed a complete previous quarter | 197,796 | 51,384 |
| Not held by the family before (incl. spelling variants) | 13,941 | 4,054 |
| One row per borrower x family x quarter | 9,381 | 3,029 |
| No acquisition date before the quarter at any BDC of the family | 9,316 | 3,001 |
| Spread, all-in rate, PIK, hold, tenor, SOFR (stated, implied base 2.5 pp or more) | 7,909 | 2,350 |
| Not an existing loan of an unaffiliated lender | 7,255 | 1,894 |
| Tranche (one spread across the family) and near-match rules | 7,175 | 1,864 |
| Quarters from 2023Q2 | 6,979 | 1,836 |
| Core: industry and maturity known | | **1,705** |

## 4. Final sample (`data/processed/loans.csv`)
- **1,705 loans**, 2023Q2 to 2026Q2, 31 manager families. **BDC counts:** each loan has one lead BDC (the family's
  BDC with the largest position, column `cik`); the lead BDCs are 45 distinct BDCs (48 names, because some BDCs were
  renamed). Counting also the other BDCs of the family that hold the loans: 61 BDCs. Universe: 67 BDCs that state
  borrower industries.
- Train 1,122 (2023Q2 to 2025Q2), test 583 (2025Q3 164, 2025Q4 149, 2026Q1 147, 2026Q2 123). The final model with
  the one-quarter gap trains on 983 loans (to 2025Q1).
- Largest families: Apollo 19%, Goldman Sachs 11%, BlackRock 7%, Antares 7%, First Eagle 5%.
- Spread median 5.00 pp (2023 6.25, 2024 5.00; the notebook also shows test-period years as descriptives: no rule
  or threshold was set on them, and they must not guide model choices); hold median USD 10.6m; tenor median 6.2 years;
  94% first lien (6% unknown: Stellus, TCW, Onex write no lien in the line). 39% of loans are held by three or more other families in the same quarter (syndicated or club
  loans; flag `n_other_families_same_q`).
- Robustness files: `loans_all_bdc.csv` 6,979 loans (other BDCs: median spread 4.75 pp, tenor known for 15%);
  `loans_incl_refi.csv` 2,170 loans, of which 424 refinancings/add-ons and 56 with tenor 3 to 4 years (D35).

## 5. Validation
- **Precision against acquisition dates** (dated loans after all filters): 94.8% acquired in the quarter of first
  appearance (95% CI 91.4 to 96.9%, n = 268). An upper bound: a purchase also has a date in the quarter.
- **Our hand check of 50 loans** (`docs/hand_check.csv`, stratified by family, re-checked by Mathis): borrower,
  spread and principal found 50/50, maturity 49/50. In the 36 that remain in the final sample: (a) originated in the
  quarter 32 = 89% (95% CI 75 to 96%), (b) bought later 3, (c) affiliate transfer 1. Optimistic: the existing-loan
  filter was designed on these loans.
- **Patrick's independent hand check** (`docs/hand_check_patrick.csv`, 50 loans of 8 managers): 26 are in our final
  sample, (a) 25, (b) 1; our filters remove 8 of his 9 (b) loans. The three earlier checks combined, each loan once: (a)
  80 of 91 = 88% (95% CI 80 to 93%); all four checks with v2: 127 of 141 = 90% (95% CI 84 to 94%, D55).
  See D23, D41. His loans come from his earlier preprocessing version; hence v2 below.
- **Out-of-sample verification of 30 further loans** (`docs/verification_sample_30.csv`, seed 2026, stratified by
  family, excluding both hand checks, checked in EDGAR by a fresh agent): borrower, spread, maturity and principal
  correct 30/30, lien 27 (2 not printed, 1 wrong); (a) 24 of 30 = 80% (95% CI 63 to 90%), (b) 5, not new 1; drawn
  before D37/D40, 29 still in the sample, of which 23 (a) = 79%. Errors
  found: WhiteHorse joint-venture lines counted as BDC holdings (fixed, 18 loans removed, D40); a rename after a
  restructuring (Crescent "Affordable Care", limitation); Stellus, TCW and Onex lien not written in the line.
- **Patrick's hand check v2** (`docs/hand_check_patrick_v2.csv`, D55): 50 loans drawn from the final `loans.csv`
  (seed 2027, stratified by family, excluding all earlier checks), each prepared with one EDGAR report by
  `code/hand_check_v2.py` and decided by Patrick in the filing: (a) 47 of 50 = 94% (95% CI 84 to 98%; weighted by
  family 94%), (b) 3. All 20 loans of borrowers never seen at another manager are (a); the 3 (b) are among the 30
  borrowers seen before (90% (a)). The (b) loans passed the existing-loan filter (D22) because the earlier holder's
  line had no maturity in XBRL (BCPE HIPH at OHA, PRGX at Monroe) or a different borrower name and a maturity two
  weeks off (Bending Spoons US Inc. vs Operations SpA). All four checks combined, each loan once: (a) 127 of 141 =
  90% (95% CI 84 to 94%); `output/tables/hand_check_v2_shares.csv`.
- **Release checker (work order 5, fresh agent)**: row rules, cutoff, numbers, fresh-clone reproducibility, teammate
  test and hygiene passed; the newness audit found loans that were not new (spelling variants of borrowers the family
  held, an acquisition date at a sister BDC), spreads lost to a unit error, family-level spread differences and
  industry labels parsed as names; a second fresh checker found brand-prefixed names and one SARON loan. Fixed in
  two rounds (D43, D44): 1,747 to 1,705 loans; a further EDGAR check of 10 loans
  (`docs/verification_sample_10_release.csv`): (a) 7, (b) 2, not new 1 (since removed).
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
- About one loan in five to one in ten may not be a fresh origination (secondary purchase, or transfer from an affiliated private
  fund, which BDC filings cannot reveal).
- Syndicated versus direct-lending mix: 39% of loans are held by three or more other families, and the share of
  low-spread loans rises over time, so train and test may differ in composition (D25).
- Hold size is measured at the reporting date and is the lender's hold, not the facility size.
- Borrower names come from a parser; a borrower renamed after a merger can be counted twice.
- Newness (and so the t-2 market median) is decided partly with later filings' comparative columns, and the set of
  industry-reporting BDCs is chosen on all quarters; both affect sample construction only, not feature values.
- First appearance can trail the signing by up to a quarter, so the cutoff can be slightly late.
