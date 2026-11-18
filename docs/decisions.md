# Decision log

Status: `proposed` = suggested in the feasibility study, may be changed. `taken` = implemented (by the team or the AI, with justification). `agreed` = confirmed by the team in a review session.
Consequential decisions (target, sample, split, metric, dropping observations, main model) are reviewed by the whole team (deck P3).
For every new or changed decision, add below the table: why it came up, options, pros and cons, evidence, choice, reversibility.

**Who decided.** D1 to D12 were proposed by the team (feasibility study). The binding commitments in
`docs/lecturer_feedback_and_commitments.md` are team decisions. Everything marked "AI" below was decided by the AI
in session 1 (18 Nov 2026) under the CLAUDE.md rules; items marked **consequential** need team review.

| # | Decision | Status | Reason |
|---|----------|--------|--------|
| D1 | Data source: SEC BDC Data Sets, `soi.tsv`, quarter-ends Sep 2022 to Jun 2026 (16 quarters). | taken | Official, free, public domain, already structured. Verified: 2022Q3 to 2026Q2 complete; 2026Q3 has only 4 filers (dropped). Loans from 2023Q2 (D14). |
| D2 | One filing per BDC and quarter: if a quarter has several filings (amendments), keep the latest. | taken | 12 BDC-quarters affected. |
| D3 | BDC universe of the main sample: **industry-reporting BDCs by rule** (industry found for at least 80% of loan lines), instead of the 16 BDCs. All-BDC file for the robustness check. | taken (AI), **consequential** | See D3 below. 67 BDCs, 34 families; 1,991 loans instead of about 680. |
| D4 | New loan = no BDC of the same family held the borrower in any earlier quarter (current holdings and prior-period comparatives), the BDC filed a complete previous quarter, no acquisition date before the quarter; family dedupe. | taken (team rule, AI implementation), **consequential** | Binding commitment (1). Implementation details in D4, D13, D21. |
| D5 | Funded floating-rate USD term loans over SOFR; drop revolvers, delayed-draw lines, non-USD, Prime, LIBOR, structured products. | taken | Goldman Sachs writes no instrument type: largest line per borrower is used (D15). |
| D6 | One row per borrower x manager family x quarter; different managers stay separate. | taken | 27.8% of new loans are held by more than one BDC of the family. |
| D7 | Spread unit detected per filing; keep 1 to 15 pp; drop lines whose "spread" equals the all-in rate. | taken (AI) | See D7 below. |
| D8 | Tenor (maturity minus quarter start) between 4 and 8 years. | taken (AI), **consequential** | See D8 below. |
| D9 | 11 GICS-style sectors by keyword rules; mapping table saved. | taken (AI) | 239 raw labels; no loan left unmapped. |
| D10 | Market features: Moody's Baa spread (BAA10Y) and SOFR before the cutoff; median new-loan spread from quarter t-2 filings filed before the cutoff. HY OAS descriptive only. | taken (AI, t-2 rule by team) | See D10 below. |
| D11 | Split by time: test = 2025Q3 to 2026Q2; train = earlier; expanding-window CV with one-quarter gap. | taken (column `split` only) | Binding commitment (2), (3). Nothing is computed from test rows. |
| D12 | Baselines and metrics as in the commitments (median of reference quarter with t-2 rule; sector x size median; MAE in bps, share within 50 bps, MAE by quarter and manager). | proposed (for notebook 02) | Unchanged by this step. |
| D13 | Borrower identification: parse the name from the free-text identifier; "held before" = rarity-weighted word matching, not exact strings. | taken (AI) | See D13. |
| D14 | Loan sample starts 2023Q2. | taken (AI), **consequential** | See D14. |
| D15 | Per borrower x BDC x quarter: the funded term line with the largest held principal. | taken (AI) | See D15. |
| D16 | Exclude structured products (CLO tranches, asset-backed notes). | taken (AI) | Not loans to operating companies. |
| D17 | Exclude families that mainly buy in the secondary market (more than half of dated new loans acquired earlier, at least 5 dated). | taken (AI) | Currently excludes none (see D17). |
| D18 | Manager families from explicit name rules; renamed BDCs keep the family of their first matching name; CCS IX -> Crescent. | taken (AI) | See D18. |
| D19 | Hold size = family's total held principal at the reporting date; feature `log_principal`. | taken (AI, approximation stated in commitments) | See D19. |
| D20 | Flags kept as columns, never features: `seen_at_other_family_before`, `n_other_families_same_q`. | taken (AI) | Same-quarter holdings of others are not known at the cutoff. |
| D21 | Prior-period comparatives of each filing used as evidence of earlier holdings. | taken (AI) | See D21. |
| D22 | Exclude existing loans of unaffiliated lenders (same maturity held earlier, or held earlier and tenor below 5 years). | taken (AI), **consequential** | See D22. Result of the hand check. |
| D23 | Target interpretation: stays "spread of newly originated loans" (hand check 83% originations in the final sample). | taken (AI, rule by team), **consequential** | See D23. |
| D24 | Environment: Python 3.12 venv, pandas 3.1, scikit-learn 1.9, matplotlib, requests; no other libraries. | taken (AI) | Course stack; `requirements.txt`. |

---

### D3. BDC universe of the main sample (consequential, AI)
- **Why it came up.** With the binding new-loan rule (family level, any earlier quarter, acquisition dates) the 16
  BDCs of the feasibility study (7 families) yield only about 680 loans over 13 quarters (first full run), below the
  course rule of thumb of about 1,000 and too few for a test set of four quarters.
- **Options.** (1) Keep the 16 BDCs. (2) Main model on all BDCs without industry. (3) Widen "industry-reporting" to
  every BDC whose filings state the industry in a form we can read (label "Industry X", tagged XBRL industry field,
  or a standard Moody's/GICS industry name in the identifier), with the same 80% threshold.
- **Pros and cons.** (1) matches the project description but is small and concentrated (Goldman Sachs about 40%).
  (2) is large (8,578 loans) but loses industry and, for many large managers, maturity and the base rate (only 20%
  of other BDCs' loans have a known tenor). (3) keeps industry and tenor for every loan, gives 1,991 loans from 34
  families, and answers the lecturers' concern that 16 BDCs are not representative. Risk: industry found by
  vocabulary matching can be wrong for some lines (checked: 48 of 50 hand-checked industries match the filing, the
  other 2 come from the tagged XBRL field and are not printed).
- **Evidence.** Core size 678 (16-BDC rule) versus 1,991 (rule 3); median spread, size and tenor of core loans and
  of all other BDCs are almost identical (4.75 pp, USD 8.0m, 6.1 years; `output/tables/core_vs_other_bdcs.csv`).
- **Choice.** (3). The all-BDC file remains for the committed robustness check.
- **Reversible?** Yes: `industry_reporting_bdc` and `family` columns allow restricting to the original 7 families.

### D4. New-loan rule (team rule; implementation by the AI)
- Commitment (1) fixes the rule. Implementation choices: "held before" looks at **any** earlier quarter, not only
  t-1 (stricter; catches borrowers that disappear for a quarter, 968 cases); the BDC's previous-quarter filing must
  be complete (at least half as many holdings as in t), because several 2022Q4 schedules in the SEC data are partial
  (first version: 91% of dated 2023Q1 "new" loans were acquired earlier); the earliest acquisition date on **any**
  line of the borrower is used.
- **Evidence.** Precision against acquisition dates (dated loans after all filters): 93.7% for industry-reporting
  BDCs (95% CI 90.6 to 96.1%, n = 297), 90.1% for all BDCs; hand check in D23.

### D7. Spread units and validity (AI)
- Unit per filing: 9 filers report percent (5.25) instead of decimals (0.0525); single values of 50 or more are basis
  points. Per-filing detection avoids misreading a genuine 0.75 pp spread of a percent filer.
- Tagged spread versus spread written in the text: 1,917 of 1,931 loans agree; the 14 differences are typos in the
  text (e.g. "SOFR+59" for 590 bps); the tagged value is used.
- New filter: lines whose spread differs from the all-in interest rate by less than 0.5 pp are fixed-rate (e.g.
  "12% PIK") tagged as spread (172 loans; found in the hand check, WhiteHorse "Chase Products"). The interest rate
  is used only for this check. Reversible: one line in step 11.

### D8. Tenor window (consequential, AI)
- **Options.** 2 to 8 years (proposal), 3 to 8, 4 to 8, 5 to 8.
- **Evidence.** Share of dated new loans acquired before the quarter by tenor: 59% (0-2y), 28% (2-3y), 25% (3-4y),
  20% (4-5y), 8% (5-6y), 12% (6-7y), 6% (7-8y). Precision on dated core loans: 92.4% (2-8), 92.5% (3-8),
  94.0% (4-8), 94.4% (5-8). No core loan has a tenor above 7.5 years, so the upper bound does not bind.
- **Choice.** 4 to 8 years: clear precision gain over 2 or 3 years; 5 years would cut many genuine 5-year loans.
- **Reversible?** Yes (`TENOR_MIN`), at the cost of a rerun.

### D10. Market features (AI; t-2 rule from the commitments)
- ICE BofA HY OAS (`BAMLH0A0HYM2`) is only available on FRED from 20 Nov 2023 (licensing), so it cannot cover
  2023 loans. Replaced by Moody's Baa minus 10y Treasury (`BAA10Y`, full history); HY OAS kept as a descriptive column.
- Values are the last daily observation strictly before the quarter start (asserted in step 13).
- The market-level spread uses new loans first seen in t-2 whose filing was submitted before the start of t (60
  loans excluded across quarters), computed from all BDCs (n per quarter 125 to 1,018) and from the core sample.
  Pre-2023Q2 new loans are used for this median although they are not in the sample.

### D13. Borrower identification and matching (AI)
- **Why.** The prototype's string comparison broke when managers reworded identifiers (54% precision).
- **Options.** Exact normalized names; fuzzy string similarity (extra library); rarity-weighted word matching.
- **Choice.** Names are parsed per BDC (delimiters, labels, learned category prefixes, industry vocabulary). A
  borrower counts as held before when its distinctive words (found in at most 0.1% of identifiers), weighted by
  inverse document frequency, are 80% covered by an earlier identifier of the family. Simple to explain, no extra
  library.
- **Evidence.** 1.6% empty names; median quarter-to-quarter name persistence 0.91; the name is found in its own
  identifier in 99.5% of cases; only 147 of 13,497 "held before" decisions in the core families rely on the
  weighted matching rather than an exact name match, and a sample of them were correct.
- **Reversible?** Threshold and word-share are parameters of `HoldingsIndex`.

### D14. Sample start 2023Q2 (consequential, AI)
- New loans can be identified from 2022Q4 (needs 2022Q3 holdings). The first quarters have short holdings history
  and many partial filings, and the t-2 market spread for 2023Q1 would need 2022Q3 new loans, which cannot be
  identified. From 2023Q2 every loan has a t-2 market spread (2022Q4: 243 new loans). Cost: about 45 core loans.

### D15. One loan line per borrower (AI)
- A borrower has several lines (term loan, delayed-draw, revolver, add-ons). We keep the funded term line with the
  largest held principal; revolvers and delayed-draw lines are excluded where they are labelled. Goldman Sachs does
  not label instruments; its largest line is in practice the term loan, and unitranche tranches share one spread.
  Spread range across a family's funds above 0.25 pp occurs for 144 of 10,843 family loans (different tranches).

### D17. Secondary-buyer families (AI)
- Palmer Square had 89% of dated "new" loans acquired earlier in an early version; after excluding structured
  products (D16) its remaining dated loans are too few, so the rule currently excludes no family. Kept as a guard
  and documented; the flag `n_other_families_same_q` identifies syndicated loans for notebook 02.

### D18. Manager families (AI)
- Keyword rules in `FAMILY_RULES` (e.g. Phillip Street and West Bay are Goldman Sachs; SCP Private Credit Income is
  SLR; Portman Ridge and Logan Ridge are BC Partners; Antares checked before Ares). A renamed BDC keeps the family of
  its first matching name (Goldman Sachs Private Middle Market Credit LLC, later "Silver Capital Holdings").
  CCS IX Portfolio Holdings is mapped to Crescent: identical identifier format and the same new borrower in the same
  quarter (Java Buyer) in the hand check. Mapping table: `data/processed/bdc_family_mapping.csv`.

### D19. Hold size (AI)
- Principal is held principal at the reporting date (end of quarter t), an approximation of the planned hold at
  the term sheet (draws and repayments within one quarter). We sum it over the family's BDCs (`principal_family`)
  because the family's allocation is the lender's hold; `log_principal` is a fixed transformation.

### D21. Prior-period comparatives as evidence (AI)
- **Why.** Hand check: BlackRock's 2024Q4 schedule in the SEC data lacks LifePoint Health, but the next filing's
  2024-12-31 comparative shows it was held, so the loan looked new.
- **Choice.** Add 258,913 comparative rows to the holdings evidence (not to the candidate loans). New-by-holdings
  candidates fell from 16,084 to 15,744. Used only for sample construction.

### D22. Exclude existing loans of other lenders (consequential, AI)
- **Why.** The hand check (D23) found 14 of 50 loans that were originated earlier and bought later, mostly broadly
  syndicated loans (Truck Hero, Focus Financial, Alliance Laundry: other BDCs held them earlier with the same maturity
  date). An acquisition date inside the quarter does not prove origination (UPC Financing: bought in 2024, loan from
  2021).
- **Options.** Keep and reinterpret the target (commitment rule); exclude by the rule below; exclude all syndicated
  loans (no reliable marker).
- **Rule.** Drop a loan if an unaffiliated BDC held the borrower in an earlier quarter with the same maturity date
  (within 7 days) or held the borrower earlier and the remaining tenor is below 5 years.
- **Evidence.** In the hand-check sample the rule removes 8 of the 14 (b) loans and none of the 35 (a) loans.
  Effect on the data: 544 + 202 family loans across all BDCs; core sample 2,434 -> 1,991.
- **Reversible?** Yes, one filter in step 11; the inputs are kept as columns.

### D23. Target interpretation after the hand check (consequential; rule by the team, application by the AI)
- Hand check of 50 loans (stratified by manager, drawn before D22): (a) 35, (b) 14, (c) 1, i.e. 70% originations.
  In the 42 loans that remain after D22: (a) 35, (b) 6, (c) 1 = 83% (95% CI about 69 to 92%).
- Commitment: if fewer than about 80% are originations, the target becomes "spread of loans newly added to a BDC
  portfolio". The point estimate after D22 is above 80% but the confidence interval includes values below 80%.
- **Choice.** Keep the name "spread of newly originated loans" for the final dataset, and state in the report that
  about one in six loans is likely an acquired or transferred loan (CI 8 to 31%), so results must be read as "loans
  newly added to the portfolio, mostly originations". The team should confirm this wording.
