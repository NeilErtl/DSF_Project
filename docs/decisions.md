# Decision log

Status: `proposed` = suggested in the feasibility study, may be changed. `taken` = implemented (by the team or the AI, with justification). `agreed` = confirmed by the team in a review session.
Consequential decisions (target, sample, split, metric, dropping observations, main model) are reviewed by the whole team (deck P3).
For every new or changed decision, add below the table: why it came up, options, pros and cons, evidence, choice, reversibility.

**Who decided.** D1 to D12 were proposed by the team (feasibility study). The binding commitments in
`docs/lecturer_feedback_and_commitments.md` are team decisions. Everything marked "AI" below was decided by the AI
in session 1 (18 Nov 2026) under the CLAUDE.md rules; items marked **consequential** need team review.
All numbers refer to the final run of `code/01_preprocess.ipynb`.

| # | Decision | Status | Reason |
|---|----------|--------|--------|
| D1 | Data source: SEC BDC Data Sets, `soi.tsv`, quarter-ends Sep 2022 to Jun 2026 (16 quarters). | taken | Verified: 2022Q3 to 2026Q2 complete; 2026Q3 has only 4 filers (dropped). Loans from 2023Q2 (D14). |
| D2 | One filing per BDC and quarter: if a quarter has several filings (amendments), keep the latest. | taken | 12 BDC-quarters affected. |
| D3 | Main sample: **industry-reporting BDCs by rule** (industry found for at least 80% of loan lines) instead of the 16 BDCs; all-BDC file for the robustness check. | taken (AI), **consequential** | 67 industry-reporting BDCs; final core sample 1,826 loans from 47 BDCs in 31 families (16-BDC rule: about 680). |
| D4 | New loan = no BDC of the same family held the borrower in any earlier quarter (current holdings, prior-period comparatives, exact name); complete previous-quarter filing; no acquisition date before the quarter; family dedupe. | taken (team rule, AI implementation), **consequential** | Binding commitment (1). Details in D4, D13, D21. |
| D5 | Funded floating-rate USD term loans over SOFR; drop revolvers, delayed-draw lines, unfunded commitments, non-USD, Prime, LIBOR, structured products, joint-venture lines. | taken | See D15, D16, D26. |
| D6 | One row per borrower x manager family x quarter; different managers stay separate. | taken | 28.6% of new loans are held by more than one BDC of the family. |
| D7 | Spread unit detected per filing (rates per filing and column); keep 1 to 15 pp; drop lines whose "spread" equals the all-in rate. | taken (AI) | See D7. |
| D8 | Tenor (maturity minus quarter start) between 4 and 8 years. | taken (AI), **consequential** | See D8. |
| D9 | 11 GICS-style sectors by keyword rules; mapping table saved. | taken (AI) | 217 raw labels in the core sample, none unmapped. |
| D10 | Market features: Moody's Baa spread (BAA10Y) and SOFR before the cutoff; median new-loan spread from quarter t-2 filings filed before the cutoff. HY OAS descriptive only. | taken (AI; t-2 rule by team) | See D10. |
| D11 | Split by time: test = 2025Q3 to 2026Q2; expanding-window CV with one-quarter gap. | taken (column `split` only) | Commitments (2), (3). Nothing is computed from test rows. |
| D12 | Baselines and metrics as in the commitments. | proposed (for notebook 02) | Unchanged by this step. |
| D13 | Borrower identification: name parsed from the identifier; "held before" by rarity-weighted word matching plus exact-name check. | taken (AI) | See D13. |
| D14 | Loan sample starts 2023Q2. | taken (AI), **consequential** | See D14. |
| D15 | Per borrower x BDC x quarter: the funded term line with the largest held principal. | taken (AI) | See D15. |
| D16 | Exclude structured products (CLO tranches, asset-backed notes). | taken (AI) | Not loans to operating companies. |
| D17 | Exclude families that mainly buy in the secondary market. | taken (AI) | Currently excludes none (see D17). |
| D18 | Manager families from explicit name rules, with an automatic overlap guard. | taken (AI) | See D18. |
| D19 | Hold size = family's total held principal at the reporting date; feature `log_principal`. | taken (AI) | See D19. |
| D20 | Flags kept as columns, never features: `seen_at_other_family_before`, `n_other_families_same_q`. | taken (AI) | Same-quarter holdings of others are not known at the cutoff. |
| D21 | Prior-period comparatives of each filing used as evidence of earlier holdings. | taken (AI) | See D21. |
| D22 | Exclude existing loans of unaffiliated lenders. | taken (AI), **consequential** | See D22. |
| D23 | Target wording: "spread of loans newly added to a BDC portfolio (mostly new originations)". | taken (AI, rule by team), **consequential** | See D23. |
| D24 | Environment: Python 3.12 venv, pandas, scikit-learn, matplotlib, requests (`requirements.txt`). | taken (AI) | Course stack, no other libraries. |
| D25 | Broadly syndicated loans kept in the sample, flagged. | taken (AI), **consequential** | See D25. |
| D26 | Principal checked against fair value; unfunded lines and joint-venture lines excluded. | taken (AI) | See D26. |
| D27 | Exclude loans with a PIK component. | taken (AI), **consequential** | See D27. |

---

### D3. Main sample universe (consequential, AI)
- **Why.** With the binding new-loan rule the 16 BDCs of the feasibility study (7 families) yield only about 680
  loans over 13 quarters (first full run): below the course rule of thumb of about 1,000.
- **Options.** (1) Keep the 16 BDCs. (2) Main model on all BDCs without industry. (3) Widen "industry-reporting" to
  every BDC whose filings state the industry in a readable form ("Industry X" label, tagged XBRL industry field, or
  a standard Moody's/GICS industry name in the identifier), with the same 80% threshold.
- **Pros and cons.** (1) matches the project description but is small and concentrated in 7 managers. (2) is large
  (7,427 loans) but only 39% have a known tenor and 40% a stated base rate. (3) keeps industry and tenor for every
  loan, gives 1,826 loans from 31 families, and answers the lecturers' concern that 16 BDCs are not representative.
  Risk: industry found by vocabulary matching can be wrong for some lines (hand check: 48 of 50 match the filing,
  the other 2 come from the tagged XBRL field).
- **Evidence.** Medians core vs other BDCs: spread 5.00 vs 4.75 pp, hold USD 10.0m vs 9.7m, tenor 6.2 vs 6.2 years
  (`output/tables/core_vs_other_bdcs.csv`).
- **Choice.** (3). **Reversible:** yes, via `family` and `industry_reporting_bdc`.

### D4. New-loan rule (team rule; implementation by the AI)
- "Held before" looks at **any** earlier quarter (stricter than t-1; catches 1,286 borrowers that disappear for a
  quarter). The BDC's previous-quarter filing must be complete (at least half as many holdings as in t), because
  several 2022Q4 schedules in the SEC data are partial (first version: 91% of dated 2023Q1 "new" loans were acquired
  earlier). The earliest acquisition date on **any** line of the borrower is used.
- **Evidence.** Precision against acquisition dates after all filters: 94.1% (95% CI 90.8 to 96.3%, n = 289) for
  industry-reporting BDCs, 91.2% for all BDCs. Hand check: D23.

### D7. Units and validity of the spread (AI)
- 9 filers tag spreads in percent (5.25) instead of decimals (0.0525); single values of 50 or more are basis points.
  Units are detected per filing, and for interest rate, floor and PIK separately per column (some filers mix units:
  found by the reviewer).
- Tagged spread vs spread written in the text: about 99% agree; differences are text typos ("SOFR+59" for 590 bps).
- Lines whose spread differs from the all-in rate by less than 0.5 pp are fixed rates tagged as spreads (174 loans;
  hand check: WhiteHorse "Chase Products", 12% PIK). The interest rate is used only for this check.

### D8. Tenor window (consequential, AI)
- **Evidence.** Share of dated new loans acquired before the quarter by tenor: 59% (0-2y), 28% (2-3y), 25% (3-4y),
  20% (4-5y), 8% (5-6y), 12% (6-7y), 6% (7-8y). Precision on dated core loans: 92.4% (2-8), 92.5% (3-8),
  94.0% (4-8), 94.4% (5-8) (first full run). No core loan exceeds 7.5 years.
- **Choice.** 4 to 8 years. **Reversible:** `TENOR_MIN`.

### D10. Market features (AI; t-2 rule from the commitments)
- ICE BofA HY OAS is only on FRED from 20 Nov 2023, so it cannot cover 2023 loans: replaced by `BAA10Y` (full
  history); HY OAS kept as descriptive column. Values: last observation strictly before the quarter start.
- Market spread: median of new loans first seen in t-2 and filed before the start of t (from all BDCs; core version
  also provided). Loans before 2023Q2 are used for this median although they are not in the sample.

### D13. Borrower identification and matching (AI)
- **Why.** String comparison broke when managers reworded identifiers (prototype: 54% precision).
- **Choice.** Names parsed per BDC (delimiters, labels, learned category prefixes, industry vocabulary; footnote
  numbers ignored). Held before = distinctive words of the name (in at most 0.1% of identifiers, at least 3 letters),
  weighted by inverse document frequency, 80% covered by an earlier identifier of the family; plus an exact match of
  the normalized name (339 extra cases with names made of short words, e.g. "GS XX Corporation").
- **Evidence.** 1.9% empty names; median name persistence 0.91; a name is found in its own identifier in 99.5% of
  cases; no borrower repeats within a family in either output file.

### D14. Sample start 2023Q2 (consequential, AI)
- New loans can be identified from 2022Q4, but the first quarters have short history and partial filings, and the
  t-2 market spread for 2023Q1 would need 2022Q3 new loans. From 2023Q2 every loan has a t-2 market spread.

### D15. One loan line per borrower (AI)
- The funded term line with the largest held principal. Goldman Sachs labels no instruments; its largest line is in
  practice the term loan. Spread range across a family's funds above 0.25 pp: 61 of 9,771 family loans.

### D17. Secondary-buyer families (AI)
- Rule: more than half of a family's dated new loans acquired earlier (at least 5 dated). After excluding structured
  products it excludes no family; kept as a guard.

### D18. Manager families (AI)
- Keyword rules in `FAMILY_RULES`; a renamed BDC keeps the family of its first matching name. Mappings found with
  evidence: CCS IX Portfolio Holdings -> Crescent (same format, same new borrowers); Senior Credit Investments ->
  Jefferies (reviewer: 60 of 62 new loans duplicated); LGAM Private Credit -> Morgan Stanley and Commonwealth Credit
  Partners -> Comvest (found by the new overlap guard: 68% and 67% of their new loans shared). The notebook now
  asserts that no family shares more than half of its new loans with another (largest remaining: 19%).

### D19. Hold size (AI)
- Held principal at the reporting date, summed over the family's BDCs: an approximation of the lender's planned
  hold at the term sheet (not the facility size). `log_principal` is a fixed transformation.

### D21. Prior-period comparatives as evidence (AI)
- Hand check: BlackRock's 2024Q4 schedule in the SEC data lacks LifePoint Health, but the next filing's
  comparative shows it. 258,913 comparative rows are added to the holdings evidence (not to candidate loans).

### D22. Exclude existing loans of other lenders (consequential, AI)
- **Why.** Hand check: 14 of 50 loans were originated earlier and bought later, mostly syndicated loans held by
  other BDCs earlier with the same maturity date (Truck Hero, Focus Financial, Alliance Laundry).
- **Rule.** Drop if an unaffiliated BDC held the borrower in an earlier quarter with the same maturity (within 7
  days: 502 family loans), or held it earlier and the tenor is below 5 years (185).
- **Evidence.** In the hand-check sample the rule removes 8 of the 14 (b) loans and none of the (a) loans.
  Caveat: designed on the same sample, so its effect is measured optimistically.

### D23. Target wording (consequential; rule by the team)
- Hand check (50 loans, drawn before D22): (a) 35, (b) 14, (c) 1. In the 41 loans that remain in the final sample:
  (a) 34 = 83% (95% CI 69 to 92%), (b) 6, (c) 1. Optimistic (D22 designed on these loans; about half of the (a)
  verdicts rest on tenor and absence of earlier holders).
- The commitment says: below about 80%, the target becomes "spread of loans newly added to a BDC portfolio". The
  point estimate is just above 80%, the interval is not. **Choice:** use the conservative wording "spread of loans
  newly added to a BDC portfolio (mostly new originations)" in report and slides. The data are unchanged.

### D25. Broadly syndicated loans (consequential, AI; open for the team)
- **Why.** Reviewer: the sample mixes direct-lending and broadly syndicated loans; the share of loans with a spread
  of at most 3.5 pp rises from 2% (2023) to 14% (2024), 16% (2025) and 26% (2026).
- **Options.** Filter by `n_other_families_same_q >= 3` (35% of loans), by a spread floor (selection on the target:
  rejected), or keep and flag.
- **Choice.** Keep and flag: club deals of three or more direct lenders look the same in the data, so the filter
  would also remove genuine private credit loans. Notebook 02 should report results with and without these loans.

### D26. Principal, unfunded lines and joint-venture lines (AI; reviewer findings)
- Lines with fair value and cost both zero are unfunded commitments (excluded). Principal/fair value near 1,000 or
  1/1,000 is a unit error (rescaled: 932 lines); other ratios outside 0.5 to 2 use fair value as size (partly drawn
  or distressed). PennantPark tags its joint venture's schedule ("Related Party PSSL/PSLF"): these lines are the JV's
  loans, excluded as candidates but kept as holdings evidence.

### D27. Exclude PIK loans (consequential, AI)
- Some filers include the PIK part in the tagged spread and others do not, so the target is not comparable; PIK
  loans are mostly restructured or stressed credits. 355 family loans removed (all BDCs); PIK stays descriptive only.
