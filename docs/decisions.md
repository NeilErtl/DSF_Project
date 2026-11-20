# Decision log

Status: `proposed` = suggested in the feasibility study, may be changed. `taken` = implemented (by the team or the AI, with justification). `agreed` = confirmed by the team in a review session.
Consequential decisions (target, sample, split, metric, dropping observations, main model) are reviewed by the whole team (deck P3).
For every new or changed decision, add below the table: why it came up, options, pros and cons, evidence, choice, reversibility.

**Who decided.** D1 to D12 were proposed by the team (feasibility study). The binding commitments in
`docs/lecturer_feedback_and_commitments.md` are team decisions. Everything marked "AI" below was decided by the AI
in session 1 (18 Nov 2026) under the CLAUDE.md rules; items marked **consequential** need team review.
Numbers refer to the final run of `code/01_preprocess.ipynb`, except where an entry gives an older number
"at the time" (history).

## Current definitions in force
| Id | Definition (one line) | Status |
|---|---|---|
| D1, D2 | SEC BDC Data Sets `soi.tsv`, one filing per BDC and quarter (latest filed) | taken |
| D3 | Main universe: BDCs that state borrower industries (67 BDCs; 45 lead BDCs in the sample, 31 families) | recommended, to be confirmed by team |
| D4 | New loan: no BDC of the same family held the borrower before; no acquisition date before the quarter | taken (team rule) |
| D5, D15, D32, D34 | One funded SOFR term line per borrower; hold size sums the loan's tranches; unfunded lines excluded | taken |
| D6 | Unit: one borrower x one manager family x one quarter of first appearance | taken (team rule) |
| D7, D27, D33 | Spread 1 to 15 pp, not the all-in rate; no PIK; hold at least USD 100,000 | taken |
| D8 | Tenor 4 to 8 years (3 to 4 years only in `loans_incl_refi.csv`) | recommended, to be confirmed by team |
| D10 | Market features: Baa spread and SOFR before the cutoff, t-2 new-loan median filed before the cutoff | taken |
| D11, D38 | Split by time, test 2025Q3 to 2026Q2; one-quarter gap; training rows filed before the cutoff | taken |
| D12, D41 | Baselines and metrics as committed; main test protocol: one model per test quarter | taken, to be confirmed by team |
| D14 | Loans from 2023Q2 | taken |
| D17 | No secondary-buyer family excluded (rule excludes none) | taken |
| D22 | Existing loans of unaffiliated lenders dropped | recommended, to be confirmed by team |
| D23, D41 | Target: spread over SOFR of newly originated loans, with the three origination checks | taken, to be confirmed by team |
| D25 | Syndicated loans kept, flag `n_other_families_same_q`, sensitivity check | recommended, to be confirmed by team |
| D26, D40 | Joint-venture schedule lines excluded (PennantPark, WhiteHorse, Monroe) | taken |
| D28, D42 | Borrower names: parser with second naming pass; display names cleaned (matching unaffected) | taken |
| D30, D31 | Tranches with one spread; no near match at the family | taken |
| D35 | Refinancings and add-ons only in `loans_incl_refi.csv` | recommended, to be confirmed by team |
| D37 | Hold size never takes the fair value | taken |
| D39, D42 | Headline numbers from the notebook; rounding of processed files; fixed role vocabulary in the dictionary | taken |

## Decision log (history and evidence)

| # | Decision | Status | Reason |
|---|----------|--------|--------|
| D1 | Data source: SEC BDC Data Sets, `soi.tsv`, quarter-ends Sep 2022 to Jun 2026 (16 quarters). | taken | Verified: 2022Q3 to 2026Q2 complete; 2026Q3 has only 4 filers (dropped). Loans from 2023Q2 (D14). |
| D2 | One filing per BDC and quarter: if a quarter has several filings (amendments), keep the latest. | taken | 12 BDC-quarters affected. |
| D3 | Main sample: **industry-reporting BDCs by rule** (industry found for at least 80% of loan lines) instead of the 16 BDCs; all-BDC file for the robustness check. | taken (AI), **consequential** | 67 industry-reporting BDCs; final core sample 1,747 loans, lead BDCs 45 in 31 families (D39; 16-BDC rule: about 680). |
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
| D17 | Exclude families that mainly buy in the secondary market (rule extended in revision 2). | taken (AI), **consequential** | Excludes none; Palmer Square kept (see D17). |
| D18 | Manager families from explicit name rules, with an automatic overlap guard. | taken (AI) | See D18. |
| D19 | Hold size = family's total held principal at the reporting date; feature `log_principal`. | taken (AI) | See D19. |
| D20 | Flags kept as columns, never features: `seen_at_other_family_before`, `n_other_families_same_q`. | taken (AI) | Same-quarter holdings of others are not known at the cutoff. |
| D21 | Prior-period comparatives of each filing used as evidence of earlier holdings. | taken (AI) | See D21. |
| D22 | Exclude existing loans of unaffiliated lenders. | taken (AI), **consequential** | See D22. |
| D23 | Target wording: "spread over SOFR of newly originated loans", with the hand-check caveat wherever the target is described (changed in work order 3). | taken (team, work order 3), **consequential** | See D23. |
| D24 | Environment: Python 3.12 venv, pandas, scikit-learn, matplotlib, requests (`requirements.txt`). | taken (AI) | Course stack, no other libraries. |
| D25 | Broadly syndicated loans kept in the sample, flagged. | taken (AI), **consequential** | See D25. |
| D26 | Principal checked against fair value; unfunded lines and joint-venture lines excluded. | taken (AI) | See D26. |
| D27 | Exclude loans with a PIK component. | taken (AI), **consequential** | See D27. |
| D28 | Second naming pass: remove display names, stray letters and industry fragments glued to borrower names. | taken (AI, after team re-check), **consequential** (sample) | See D28. Core 1,826 -> 1,798 (at that time). |
| D29 | Hand-check loans are matched to the final sample by quarter, family, name word and loan terms, not by `loan_id`; principal 50/50. | taken (after team re-check) | See D29. |
| D30 | Tranches of one loan (same maturity) with different spreads are dropped (Patrick's rule). | taken (AI, revision 2; judgment call) | See D30. 14 core loans. |
| D31 | Near-match rule: same first distinctive name word and maturity within 60 days at the family = not new (Patrick's rule). | taken (AI, revision 2), **consequential** | See D31. 19 core loans. |
| D32 | Unfunded lines: no positive fair value and no positive cost; a borrower with only committed lines is kept in its pricing quarter; rate-less lines kept and flagged. | taken (AI, revision 2), **consequential** | See D32 (EDGAR check of 14 loans). |
| D33 | Principal units: filing-level thousands rule and a USD 100,000 floor (Patrick's rules). | taken (AI, revision 2) | See D33. |
| D34 | Hold size sums all tranches of the loan (same maturity); base rate counts as SOFR if any family fund states it. | taken (AI, revision 2) | See D34. |
| D35 | Main sample stays "new borrower"; variant `loans_incl_refi.csv` with refinancings/add-ons and tenor 3 to 4 years, flagged. | taken (AI, revision 2), **consequential** | See D35. |
| D36 | `code/modelling_helpers.py` for notebook 02, adapted from Patrick's `preprocessing.py`. | taken (AI, revision 2) | See D36. |
| D37 | Hold size never takes the fair value: a line whose principal is off fair value (ratio outside 0.5 to 2, not a unit error) keeps its tagged principal, flagged. | taken (AI, work order 3, leakage audit), **consequential** (feature) | See D37. |
| D38 | Time splits also require the filing date before the cutoff; per-test-quarter evaluation and the committed metrics added to `modelling_helpers.py`. | taken (AI, work order 3) | See D38. |
| D39 | Headline numbers written by the notebook (`output/tables/headline_numbers.csv`); "BDCs" means lead BDCs (distinct `cik`). | taken (AI, work order 3) | See D39. |
| D40 | Lines of WhiteHorse's and Monroe's joint-venture schedules excluded (no net-assets percentage tagged); verification findings documented. | taken (AI, work order 3, out-of-sample verification), **consequential** (sample) | See D40. |
| D41 | Target wording with all three origination checks; main test protocol one model per test quarter; the five sample definitions kept. | taken (preprocessing owner, work order 5), to be confirmed by team, **consequential** | See D41. |
| D42 | Release polish: rounding of processed files, cleaned display names, fixed role vocabulary in the data dictionary. | taken (AI, work order 5) | See D42. |

---

### D3. Main sample universe (consequential, AI)
- **Why.** With the binding new-loan rule the 16 BDCs of the feasibility study (7 families) yield only about 680
  loans over 13 quarters (first full run): below the course rule of thumb of about 1,000.
- **Options.** (1) Keep the 16 BDCs. (2) Main model on all BDCs without industry. (3) Widen "industry-reporting" to
  every BDC whose filings state the industry in a readable form ("Industry X" label, tagged XBRL industry field, or
  a standard Moody's/GICS industry name in the identifier), with the same 80% threshold.
- **Pros and cons.** (1) matches the project description but is small and concentrated in 7 managers. (2) is large
  (7,385 loans) but only 38% have a known tenor and 40% a stated base rate. (3) keeps industry and tenor for every
  loan, gave 1,798 loans from 31 families (1,747 after work order 3), and answers the lecturers' concern that 16 BDCs are not representative.
  Risk: industry found by vocabulary matching can be wrong for some lines (hand check: 48 of 50 match the filing,
  the other 2 come from the tagged XBRL field).
- **Evidence.** Medians core vs other BDCs: spread 5.00 vs 4.75 pp, hold USD 10.0m vs 9.7m (now 10.5m vs 9.9m), tenor 6.2 vs 6.2 years
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
  the normalized name (340 extra cases with names made of short words, e.g. "GS XX Corporation"). Names are
  cleaned in a second pass (D28).
- **Evidence.** 1.9% empty names; median name persistence 0.91; a name is found in its own identifier in 99.5% of
  cases; no borrower repeats within a family in either output file.

### D14. Sample start 2023Q2 (consequential, AI)
- New loans can be identified from 2022Q4, but the first quarters have short history and partial filings, and the
  t-2 market spread for 2023Q1 would need 2022Q3 new loans. From 2023Q2 every loan has a t-2 market spread.

### D15. One loan line per borrower (AI)
- The funded term line with the largest held principal. Goldman Sachs labels no instruments; its largest line is in
  practice the term loan. Spread range across a family's funds above 0.25 pp: 61 of 9,771 family loans.

### D17. Secondary-market buyers (consequential; AI, revised in revision 2)
- **Why it came up again.** Patrick excluded Palmer Square (54 loans in our sample); an early diagnostic in session 1
  showed most of its dated "new" loans bought earlier, but those were CLO tranches, now excluded (D16).
- **Measures per family** (`output/tables/family_diagnostics.csv`): precision against acquisition dates (only where
  dates exist), share of spreads at most 3.5 pp, share of borrowers held by 3+ other managers in the same quarter,
  and, new, the share of the family's candidate new loans that are existing loans of other lenders (same maturity
  held earlier, or held earlier and tenor below 5 years), which needs no acquisition dates.
- **Evidence.** Palmer Square: no dated loans; existing-loan share 22% (Goldman 24%, First Eagle 34%, highest
  Investcorp 50% on 18 candidates); share held by 3+ others 57% (BlackRock 57%, Antares 61%, Jefferies 73%); spreads
  at most 3.5 pp 22% (Apollo and Goldman 22%, AllianceBernstein 58%). Palmer Square is not an outlier on any measure.
- **Options.** (1) Exclude by judgement. (2) Rule on the spread level (selects on the target: rejected). (3) Rule on
  syndication share (would also exclude Jefferies, Antares, BlackRock, i.e. club lenders). (4) General rule on
  behaviour: a family is a secondary-market buyer if more than half of its dated new loans were acquired earlier (at
  least 5 dated) or more than half of its candidate new loans are existing loans of other lenders (at least 20).
- **Choice.** (4). It excludes no family today, so Palmer Square stays; the syndicated share stays a flag (D25) and
  a sensitivity check for notebook 02 (163 core loans have a spread of at most 3.5 pp and 3+ other holders).
  Limitation noted by the second review: the existing-loan share counts loans that step 9b removes anyway, so the
  rule only bites for a family whose new loans are mostly such loans. **Reversible:** one line in step 9.

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
- Hand check (50 loans, drawn before D22): (a) 35, (b) 14, (c) 1. In the 39 checked loans that remain in the final
  sample (after D28; counted as in D29): (a) 33 = 85% (95% CI 70 to 93%), (b) 5 = 13%, (c) 1 = 3%. After revision 2
  (D30 to D35): 37 checked loans remain, (a) 32 = 86% (95% CI 72 to 94%), (b) 4 = 11%, (c) 1 = 3%. Optimistic (D22
  designed on these loans; about half of the (a) verdicts rest on tenor and absence of earlier holders).
- The commitment says: below about 80%, the target becomes "spread of loans newly added to a BDC portfolio". The
  point estimate is just above 80%, the interval is not. Revision 2 chose the conservative wording "spread of loans
  newly added to a BDC portfolio (mostly new originations)".
- **Change in work order 3 (team instruction).** The point estimate is above the 80% threshold, so the wording
  follows the commitment: the target stays **"the spread over SOFR of newly originated loans"**, and wherever the
  target is described (notebook header, data dictionary, README, `docs/for_modelling.md`, data report) it carries the
  caveat: "The hand check finds about 86% true originations (95% CI 72 to 94%); the remaining loans are newly added
  to a BDC portfolio through purchases or transfers." The data are unchanged. Easy to reverse (wording only).
- **Second hand check (credit: Patrick Eppler).** Patrick classified 50 loans of his own version (8 managers, (a) or
  (b); `docs/hand_check_patrick.csv`). With the matching rule of D29, 27 are in our final sample: (a) 26, (b) 1
  (Oxbow Carbon, Goldman Sachs 2023Q3); no loan was checked by both of us. Of his 9 (b) loans our filters remove 8
  (4 existing loans of other managers, 3 refinancings, 1 tenor 3 to 4 years), of his 41 (a) loans 15 (9
  refinancings and add-ons of existing borrowers, which our main sample excludes by definition, D35). Combined over
  both checks, each loan once: (a) 58 of 64 = 91% (95% CI 81 to 96%), (b) 5, (c) 1. Patrick's classes rest on his
  own evidence standard (no class (c)), so the combined figure is reported next to ours, not instead of it; the
  caveat keeps our own 86%. No filter was changed: the single (b) case is not a pattern. The 6 other removed (a)
  loans: tenor 3 to 4 years 2, existing loan of another manager 1, held by the family before 1, previous-quarter
  filing incomplete 1, not a candidate 1. The combined interval treats two differently designed samples (Patrick's:
  8 managers, 21 of 50 loans Goldman Sachs) as one random sample, so it is a secondary figure. In
  `docs/hand_check_patrick.csv` the column `source_url` is Patrick's evidence link (often the previous quarter's
  filing or another BDC's filing), not necessarily the loan's own filing.
- **Out-of-sample verification (D40).** 30 further loans checked by a fresh AI agent: (a) 24 of 30 = 80% (95% CI
  63 to 90%); 23 of the 29 still in the sample after D40 = 79%. Close to the 80% threshold. The work order fixed
  the caveat text; the docs for the team add this figure next to it, and the team may revisit the wording.

### D25. Broadly syndicated loans (consequential, AI; open for the team)
- **Why.** Reviewer: the sample mixes direct-lending and broadly syndicated loans; the share of loans with a spread
  of at most 3.5 pp rises from 2% (2023) to 14% (2024), 16% (2025) and 26% (2026).
- **Options.** Filter by `n_other_families_same_q >= 3` (35% of loans at the time; now 667 loans = 38%), by a spread floor (selection on the target:
  rejected), or keep and flag.
- **Choice.** Keep and flag: club deals of three or more direct lenders look the same in the data, so the filter
  would also remove genuine private credit loans. Notebook 02 should report results with and without these loans.

### D26. Principal, unfunded lines and joint-venture lines (AI; reviewer findings)
- Lines with fair value and cost both zero are unfunded commitments (excluded). Principal/fair value near 1,000 or
  1/1,000 is a unit error (rescaled: 932 lines at the time); other ratios outside 0.5 to 2 used fair value as size
  (partly drawn or distressed). **Superseded by D37** (the tagged principal is kept). PennantPark tags its joint venture's schedule ("Related Party PSSL/PSLF"): these lines are the JV's
  loans, excluded as candidates but kept as holdings evidence.

### D27. Exclude PIK loans (consequential, AI)
- Some filers include the PIK part in the tagged spread and others do not, so the target is not comparable; PIK
  loans are mostly restructured or stressed credits. 355 family loans removed (all BDCs); PIK stays descriptive only.

### D28. Second naming pass (consequential for the sample; AI, after the team's re-check of 19 Nov 2026)
- **Why.** The team's re-check of the hand check found borrower names with a prefix glued to the legal name
  ("VWhite Cap Buyer LLC", "Services Regis Regis Corporation", "Parexel Pheoenix Newco Inc.", "Sterling Pharm Saffron
  Bidco Ltd"). Counted in the core sample before the fix: 140 names with a repeated display name, 7 with a stray
  capital letter, 9 with an industry fragment. The filings' printed tables show the right names; the prefixes come
  from the XBRL member names (Apollo/MidCap write "display name + legal name"; some Goldman Sachs and
  AllianceBernstein members start with a stray letter) and from our parser (a learned category prefix could cut an
  industry label in two: "Consumer | Services Regis ...").
- **Options.** (1) Leave names as they are (cosmetic within a family, but the cross-family checks fail).
  (2) Hand-made corrections for the affected names. (3) General rules, applied to all holdings.
- **Choice.** (3): industry labels are stripped before and after learned category prefixes ("and" = "&"); then a
  second pass over all BDCs drops an immediately repeated first part, a stray capital letter when the remainder is a
  name used by another BDC, and, for BDCs where at least 10% of names repeat (display-name formats), leading words
  when the remaining legal name is used by another BDC and contains a distinctive word (used in at most 20 names);
  no cut next to "of", "and", "the". After the fix: 0 repeated, 1 stray letter ("GTreasury G Treasury SS LLC"),
  0 industry fragments in the core sample.
- **Effect.** Core 1,826 -> 1,798 (train 1,197 -> 1,177, test 629 -> 621); 32 loans left (mostly Apollo loans now
  recognized as held earlier by the family or as existing loans of other lenders), 4 entered (BlackRock loans whose
  industry is now found), 253 renamed. Precision against acquisition dates unchanged (94.1%), medians unchanged.
- **Rejected along the way.** (a) Taking any shorter suffix that another BDC uses as a name: cut "Comoto Holdings
  LLC" to "Holdings LLC". (b) A "same maturity and spread held earlier by the family" rule for renamed borrowers
  ("Flow Control Group" -> "FCG Acquisitions"): of 25 sampled matches, most were different borrowers with
  coincident terms; rejected, the rare renamed loan remains a documented limitation.
- **Reversible?** Yes: `refine_borrowers` in `utils_preprocess.py`; the raw parse is kept as `borrower_raw` in the
  notebook.

### D29. Counting the hand check against the final sample (after the team's re-check of 19 Nov 2026)
- **Why.** The re-check counted 39 checked loans in `loans.csv` (matching by `loan_id`) where the report said 41
  (matching by borrower and quarter). Both were imperfect: `loan_id` hashes the family, so the two Jefferies loans
  (Solis Mammography, AB Centers; Senior Credit Investments was re-mapped to Jefferies) got new ids although they are
  in the sample; and the name changes of D28 break matching by name.
- **Choice.** A checked loan is in the final sample if `loans.csv` has a loan of the same quarter and family with a
  common distinctive name word and the same maturity (within 7 days) or the same spread; computed in step 15e from
  the current files. Result after D28: 39 loans, (a) 33, (b) 5, (c) 1. The re-check's figures (32 / 6 / 1 of 39)
  refer to the files before D28 counted by `loan_id`; after D28, GardaWorld and Saffron (a) are no longer new for
  their family, White Cap (b) is removed, and the two Jefferies loans (a) are counted.
- The re-check also found the principal printed in the filings for all 50 loans (three were recorded as "tagged
  only"); `docs/hand_check.csv` corrected.

### D30. Tranches with different spreads (AI, revision 2; rule from Patrick's version)
- **Why.** Patrick drops loans whose tranches (same borrower, fund, quarter and maturity) carry different spreads;
  we kept the largest line. **Evidence.** 17 core candidates flagged (only 1 with an acquisition date, so precision
  cannot judge); spreads outside 1 to 15 pp are ignored when comparing tranches (the second review found unit
  glitches such as a tagged 0.05). **Choice.** Adopt as a judgment call, not on evidence: a loan with two prices has
  no unambiguous target; cost 14 core loans.

### D31. Near-match rule (consequential; AI, revision 2; rule from Patrick's version)
- **Rule.** A candidate is not new if an earlier holding of the same family contains the first distinctive word of
  the borrower name and has a maturity within 60 days (same loan written differently, e.g. "GS Fullsteam Operation"
  vs "Fullsteam Operations").
- **Correction after the second review.** The first version took the "first word" from an unordered set, so the
  word (and the removed loans) changed from run to run, and it was often "and" or "amendment". Now the words are taken
  in reading order and must be rare (in at most 0.1% of identifiers); two clean runs give identical files.
- **Evidence (fixed version).** Among dated candidates after all other filters, 2 of 4 flagged loans were acquired
  before the quarter vs 8.4% of the others (n = 450): the direction supports the rule, the evidence is weak.
  Removes 19 core loans (46 flagged in all BDCs before other filters).
- **Choice.** Adopt (low cost, consistent with Patrick's validation). **Reversible:** switch `APPLY_NEAR_MATCH`.

### D32. Undrawn lines (consequential; AI, revision 2)
- **Why.** Patrick treats a line without a tagged interest rate as undrawn; about 49 of our loans (mostly Goldman Sachs)
  were in our sample but undrawn for him; a few had a principal far above his.
- **Evidence (14 loans checked in the EDGAR filings).** Two different cases:
  (a) Goldman Sachs Private Credit Corp. lines without rate but with principal, cost and fair value printed (AL GCX,
  Vizient, Syncapay, Kohler Energy, Zelis, Albaugh): the footnote says "position or portion thereof unsettled as of
  [date]; interest rate ... not known prior to the settlement date". These are owned positions with a known spread,
  not undrawn: Patrick's rule is wrong for them. (b) Lines whose cost and fair value are printed as "-" (Recochem,
  Crewline, Northstar, Kryptona, Buffalo Merger Sub, ASM Buyer): unfunded commitments, partly in CAD or NOK; our old
  rule missed them because a missing value was not treated as zero. Patrick is right for them. Two of his undrawn
  cases are funded in the filing (MGT Merger Target 6,263 at 11.94%, Arrow Buyer 2,942 at 11.74%). WhiteHorse
  "Camarillo Fitness" is a restructured 13.32% PIK loan not tagged as PIK (kept; noted as residual).
- **Choice.** A line is unfunded when it has no positive fair value and no positive cost; a missing value counts as
  "no" only in filings that tag a fair value for most of their lines. Lines without a rate stay, with the flag
  `no_rate_tagged` (38% of core loans: Apollo, First Eagle and others never tag rates; at Goldman Sachs the flag marks
  unsettled purchases). The 17,000 newly flagged term lines are mostly lines with zero principal that were never
  candidates.
- **Correction after the second review.** A borrower whose lines at a fund are all committed but not yet funded (a
  loan signed shortly before the reporting date, e.g. Crewline Buyer 2023Q3, Kryptona Bidco 2024Q3) would otherwise
  never enter: next quarter it counts as held before. Such a borrower is now a candidate in that quarter, its pricing
  quarter, with the commitment as size and the flag `committed_not_funded` (399 lines; 31 core loans, 30 Goldman).

### D33. Principal units and floor (AI, revision 2; rules from Patrick's version)
- A filing whose median position is below USD 50,000 and at least 200 times smaller than the BDC's usual median is in
  thousands: rows below 500,000 (and their cost and fair value) are multiplied by 1,000 (7 filings, 1,174 rows; e.g.
  Varagon 2023-2024, principal 72,000 with fair value 70,000). Positions of the family below USD 100,000 are dropped as
  implausible for a new term loan (18 core loans; e.g. BlackRock positions of USD 30,000 to 70,000).
- The mirror case (second review): a filing whose median position is at least 200 times the BDC's usual median is
  tagged 1,000 times too large (TCW 2023; "Mark Andy" USD 7.0bn); its rows above USD 500m are divided by 1,000.
  The notebook asserts a hold below USD 1bn.

### D34. Hold size and base rate across a loan's lines (AI, revision 2)
- Hold size now sums all funded term lines of the loan with the same maturity at each fund (Patrick's definition; a
  loan is often split into rows), then over the family's funds. Principal agreement with Patrick within 5%: 74.5% ->
  76%; the rest is mostly funds he counts that are not candidates in ours (e.g. a fund's first filing).
- The base rate counts as SOFR stated when any family fund states SOFR for the loan (sample check: Stellus "Morgan
  Electrical" was dropped because the lead fund wrote no rate). +8 core loans.

### D35. Refinancings and add-ons of existing borrowers (consequential; AI, revision 2)
- **Why.** Patrick counts a new borrower x maturity as new; 260 of his loans are refinancings or add-ons that our
  borrower-level rule excludes. This is the largest single difference between the versions.
- **Evidence.** Variant `data/processed/loans_incl_refi.csv` (same filters; a candidate is new when the family did not
  hold the same loan before, i.e. the borrower with a maturity within 60 days or a holding without maturity, by name
  match or exact name; acquisition date of the chosen line; each loan once, at first appearance): 2,205 loans, of
  which 390 refinancings/add-ons and 58 with tenor 3 to 4 years. Dated refinancings/add-ons were acquired in their
  quarter in only 47% of cases (9 of 19; CI 27 to 68%) against 95% for new borrowers (261 dated); their median spread
  is 4.31 vs 5.00 pp. Many are add-ons under an existing credit agreement, priced at or near its terms.
- **Choice.** Keep the borrower-level rule for the main sample; offer the variant for robustness. Limitation of the
  variant: one line per borrower, fund and quarter, so a second loan of the same borrower in the same quarter is not
  represented (41 of Patrick's refinancings).

### D36. Modelling helpers (AI, revision 2; design from Patrick's version)
- `code/modelling_helpers.py`: `load_data`, `make_preprocessor` (median imputation and z-scores, one-hot with a
  dropped reference and pooled infrequent categories, all inside a sklearn pipeline), `time_cv_splits` (expanding
  window by quarter, one-quarter gap), `final_train_test` (train up to 2025Q1 by default). Adapted from Patrick
  Eppler's `preprocessing.py`; features log_principal, tenor_years, mkt_spread_t2_all, baa_spread_prev, sofr_prev,
  sector, lien, family. Dry run in step 15f: 4 folds (validate 2024Q3 to 2025Q2), final train 1,016 / test 607 (now 1,000 / 604)
  loans. Documented after review: one final model means a gap of 2 to 4 quarters for later test quarters, and a
  category unseen in training maps to the reference category.

### D37. Fair value out of the hold size (consequential for a feature; AI, work order 3, leakage audit)
- **Why.** The leakage audit (fresh agent) found that step 6 set a line's principal to its fair value when the ratio
  principal / fair value was outside 0.5 to 2 and not a unit error (partly drawn or distressed lines). Fair value is a
  never-feature (priced together with the spread), and it then entered `log_principal`: a real, small leak of a
  never-feature into a feature. Effect: 34 core loans change their hold size (Goldman Sachs
  19, Apollo 13, WhiteHorse 2; median change of `log_principal` +0.2); one Goldman Sachs loan (Pearl Acquisition,
  2025Q4) leaves because its largest line, now the lead line, carries a mis-tagged maturity (2099).
- **Options.** (1) Keep: few loans, small effect; violates the commitment. (2) Set the size to missing (imputed in the
  pipeline): loses information. (3) Keep the tagged principal and flag the line (`principal_fix`).
- **Choice.** (3); the flag is in the interim data of step 6 (`principal_fix`), not in the output files. Fair value
  is still used in two binary ways: to detect a unit error (a ratio near 1,000, which fixes the scale, not the
  value) and, with cost, to tell funded from unfunded lines (D32), which decides which tranches are summed. **Reversible:** one line in step 6.

### D38. Filing date in the splits, per-test-quarter evaluation (AI, work order 3)
- **Why.** The audit found 4 loans of 2024Q4 (a WhiteHorse 10-K/A filed 10 June 2025) inside the training fold that
  validates 2025Q2 (cutoff 1 April 2025): by D2 we keep the latest amendment and its filing date. The work order also
  asked for a per-test-quarter evaluation.
- **Choice.** `time_cv_splits`, `final_train_test` and `test_quarter_splits` keep only training rows whose
  `filed_date` is before the cutoff (`known_before`); `time_cv_splits` asserts contiguous quarters. New:
  `test_quarter_splits` / `evaluate_per_test_quarter` (one model per test quarter t, trained on all loans up to t-2,
  including earlier test quarters, hyperparameters fixed before) and `summarize_errors` (MAE in bps, share within
  plus or minus 50 bps, by quarter or family), `error_frame`, and both committed baselines as code: `baseline_t2`
  (`mkt_spread_t2_all`) and `baseline_sector_size` (window exactly t-5 to t-2, terciles cut on the window, fallback
  to the sector median and then to baseline 1 below 5 loans; specified after the fresh-reader test). Proposed main
  test protocol: one model per test quarter (team to confirm). Effect: the last validation fold trains on 842 instead of 844 loans
  (2 WhiteHorse loans of 2024Q4 remain after D40; 4 before); no test split changes. The original 10-K was probably public in time, so this is conservative. **Reversible.**
- **Also documented, not changed (audit findings 3 to 6).** Name rarity, the industry vocabulary, the comparatives
  used for "held before", and the choice of industry-reporting BDCs use all quarters, so sample construction (not
  feature values) uses information from after the cutoff; FRED "before the cutoff" refers to the observation date
  (the last SOFR of a quarter is published on the morning of the cutoff day); descriptives of spreads by year and
  the syndicated share include test quarters and were shown in reviews, but no filter threshold was set on them.
  Notebook 02 must not use the test-period trend to choose a model.

### D39. Headline numbers and the BDC count (AI, work order 3)
- **Why.** Docs quoted 45 and 46 BDCs. 46 was the count before revision 2; the notebook now writes every quoted
  number to `output/tables/headline_numbers.csv`.
- **Definition.** "Lead BDCs" = distinct `cik` in `loans.csv` (the family's BDC with the largest position). `bdc_name`
  has more distinct values because some BDCs were renamed. "BDCs holding the loans" adds the other BDCs of the family
  that hold a loan in its first quarter.

### D40. Joint-venture schedules at WhiteHorse and Monroe; out-of-sample verification (AI, work order 3)
- **Why.** The out-of-sample verification (fresh agent, 30 loans, `docs/verification_sample_30.csv`) found that
  WhiteHorse's "Pirtek Holdco" (2023Q4) is a line of the unconsolidated STRS joint venture, whose schedule WhiteHorse
  tags in its own filing; WhiteHorse's own schedule does not list the borrower.
- **Evidence.** In WhiteHorse's filings the JV lines are the only loan lines without a tagged net-assets percentage
  (10-K for 2023: 68 of 175 lines with principal). A scan of all filings for lines without that tag, in filings where
  most lines have it, shows the same pattern for Monroe Capital Corp (its Senior Loan Fund, about 80 lines per
  filing); at other BDCs the untagged lines are own holdings (tranches, revolvers), so the rule is not general.
  Carlyle's "Credit Fund" JV lines never reached the sample. Effect: 1,676 WhiteHorse and 785 Monroe lines
  excluded; 18 WhiteHorse core loans leave (46 to 28); Monroe Capital Corp had no loans in the files. The t-2 market
  median of 2024Q1 moves from 5.375 to 5.25 pp. Core sample 1,766 to 1,747 loans (with D37).
- **Choice.** Exclude, like PennantPark's PSSL lines (D26): the JV is not the BDC and its loans are often bought from
  the BDC. **Reversible:** `JV_SCHEDULE_BDCS` in step 7.
- **Other verification findings, documented, not changed.** (1) Crescent's "Affordable Care Inc." (2026Q2) is a
  restructuring of a borrower Crescent held as "ACI Group Holdings": a name change defeats the family-history check;
  no general rule can catch renames, so this stays a known limitation (one loan). (2) Stellus, TCW and Onex print the
  lien only as a table header, so `lien` is "unknown" for almost all their loans; with `family` in the model this
  acts like a family effect. (3) One acquisition date differs by 6 days from the printed one (descriptive column).
- **Verification result.** The sample was drawn from `loans.csv` before D37 and D40 (1,766 loans); 29 of the 30 are
  still in the sample (Pirtek left). Borrower, spread, maturity and principal correct for 30 of 30; class (a) 24 of
  30 = 80% (95% CI 63 to 90%), 23 of 29 = 79% on the loans still in the sample, (b) 5, not new 1. 15 of the 29 are
  test-quarter loans; D40 was triggered by a 2023Q4 loan and set no threshold on test-row outcomes. Lower than the hand checks (86% and 96%), within their intervals; it supports
  the caveat that the target includes loans newly added through purchases.

### D41. Target wording, test protocol, sample definitions (preprocessing owner, work order 5; to be confirmed by team)
- **Target wording.** Keep "the spread over SOFR of newly originated loans". The commitment reinterprets the target
  only if fewer than about 80% of checked loans are originations; the combined evidence is above 80%: our hand check
  32 of 37, Patrick's 26 of 27, the out-of-sample check 24 of 30 (80%, the cleanest estimate: no filter was designed on
  it), all distinct checked loans in the sample 81 of 93 = 87% (95% CI 79 to 93%; notebook step 15e,
  `headline_numbers.csv`). Wherever the target is described the three checks are shown, with the sentence "About one
  loan in five to one in ten may be a purchase or transfer rather than a fresh origination; it is still a loan newly
  priced into a BDC portfolio."
- **Final evaluation protocol.** Main: one model per test quarter, trained on all loans up to t-2
  (`evaluate_per_test_quarter`): the test gap equals the validation gap, each test loan is predicted exactly once by a
  model that never saw it, and model choice happens only on validation folds. Secondary view: one model trained up to
  2025Q1 (`final_train_test`). Options considered: only the single model (simpler, but gaps of 1 to 4 quarters make
  later test quarters harder than validation).
- **Sample definitions** (D35 refinancings out, D22 existing loans of other managers dropped, D3 industry-reporting
  universe, D8 tenor 4 to 8 years, D25 syndicated loans kept): unchanged, status "recommended by the preprocessing
  team, to be confirmed", each with its reason and robustness file or flag in the README.
- **Reversible:** wording and protocol choice only; no data change.

### D42. Release polish (AI, work order 5; no sample definition or filter changed)
- **Rounding.** Processed files write pp and % columns with 4 decimals and USD amounts in whole dollars (float
  artefacts such as 1.7500000000000002 removed). All computations in the notebook use the unrounded values.
- **Display names.** `borrower` is a cleaned display name (`utils_preprocess.display_name`): trailing maturity,
  acquisition, rate, amendment or "Cov-Lite" text, a display name in front of the legal name, a glued code, names cut
  at "&" or by an HTML "amp;"; 41 names changed in loans.csv, 43 in loans_all_bdc.csv, 42 in
  loans_incl_refi.csv (e.g. "CFP Holdings LLC Matrity 09/13/2030", "GTreasury G Treasury SS LLC"). `borrower_key`, matching and `loan_id` are unchanged; the hand-check matching
  uses both the display name and the parsed name. Two WhiteHorse lines name no borrower at all (only "Oil & Gas
  Storage & Transportation"); their display name shows that text.
- **Roles.** `data_dictionary.csv` uses the roles target, feature, feature_optional, never_feature, flag, id, time,
  split, descriptive, check (detail in `note`); the notebook asserts that "feature" equals `NUM + CAT` of the helpers.
