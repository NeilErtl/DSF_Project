# AI audit trail

Short record per work session: what the AI did, what was checked, what was rejected. Decisions and their
evidence are in `docs/decisions.md`; results in `docs/data_report.md`.

## Session 1, 18 Nov 2026: building the working dataset (01_preprocess), Claude Opus 5.5 in Claude Code

**Task.** Work order `course_ref/5_For_the_repo/PROMPT_CLAUDE_CODE.md`, then the team's binding commitments in
`docs/lecturer_feedback_and_commitments.md` (received mid-session; they replaced the work order where they conflict).

**What the AI did**
- Set up the environment (Python 3.12 user install, project `.venv`, `requirements.txt`) and the folder structure.
- Wrote `code/01_preprocess.ipynb` and `code/utils_preprocess.py`: download (SEC, FRED), extraction of `soi.tsv`,
  one filing per BDC and quarter, family mapping, borrower parsing, new-loan rule, features, filters, outputs,
  validation. Built `data/processed/loans.csv`, `loans_all_bdc.csv` and the mapping and dictionary tables.
- Wrote `docs/data_report.md`, the decision entries D13 onward and updates of D1 to D12, this audit trail, and the
  README section "How to rebuild the data".

**What was checked (and changed because of it)**
- Borrower parsing: share of empty names (1.6%), quarter-to-quarter persistence per BDC (median 0.91); inspected
  every BDC-quarter with persistence below 0.6 and fixed the parser where it failed (category headers, industry
  written in front of names, commas before "Company", country prefixes).
- New-loan rule against acquisition dates: the first version (exact matching, previous quarter only) had only 72%
  precision on dated loans. Causes found and fixed: incomplete 2022Q4 filings (coverage rule), industry words inside
  names (distinctive-word matching), garbage dates (year bounds), short-tenor seasoned loans (tenor filter),
  incomplete filings (prior-period comparatives as evidence).
- Units: spread unit detected per filing; tagged spreads compared with the spread written in the text (1,917 of
  1,931 agree; the 14 differences are typos in the text such as "SOFR+59" for 590 bps).
- Cutoff: every FRED value dated before the quarter start (asserted); every t-2 loan used for the market spread
  filed before the quarter start (asserted; 60 excluded); recomputed one quarter by hand.
- Hand check of 50 loans against the EDGAR filings (`docs/hand_check.csv`), plus an adversarial review by a fresh
  AI agent (see below).

**What was rejected**
- The prototype's rule (normalized identifier string absent one quarter earlier): breaks when managers reword.
- Exact borrower-name matching only: misses rewording and industry prefixes (147 of 13,497 decisions in the core
  families need the weighted matching).
- ICE BofA high-yield spread as a feature: FRED now only provides it from November 2023.
- The 16-BDC universe of the feasibility study: with the stricter new-loan rule it yields only about 680 loans; the
  rule-based industry-reporting universe gives 1,826 (consequential decision D3, for team review).
- Inferring currency or instrument type where the filer writes nothing: such loans stay in the all-BDC file only.

**Adversarial review** (fresh AI agent, no access to the author's reasoning; prompt as in the work order). Nine
findings; what was done with each:

| # | Finding | Response |
|---|---|---|
| 1 | PennantPark's tagged JV schedule ("Related Party PSSL/PSLF") entered as loans; "By ..." names re-flagged as new | Fixed: JV lines excluded from candidate loans (kept as holdings evidence); words of 1-2 letters ignored in matching; exact-name second check |
| 2 | Jefferies Credit Partners and Senior Credit Investments are one manager (60 duplicated deals across train/test) | Fixed: family rule, plus an automatic guard (no two families may share more than half of their new loans). The guard found two more: LGAM Private Credit (Morgan Stanley) and Commonwealth Credit Partners (Comvest) |
| 3 | Numeric "borrowers" (footnote numbers) in the all-BDC file, new every quarter | Fixed: footnote numbers no longer count when learning category prefixes; names need a real word |
| 4 | Unfunded commitments chosen as the loan line (principal up to USD 270m, fair value 0) | Fixed: lines with fair value and cost both zero excluded |
| 5 | Principal in thousands for some filers | Fixed: ratio to fair value of about 1,000 or 1/1,000 rescaled; other ratios outside 0.5 to 2 use fair value as size |
| 6 | Interest rate converted with the spread's unit, so the fixed-rate check failed for some filers | Fixed: unit detected per filing and per column |
| 7 | Broadly syndicated loans mixed with direct lending; their share rises towards the test period | Not filtered (no reliable marker: club deals of 3+ direct lenders look the same); documented as open risk and decision D25 for the team; sensitivity analysis recommended for notebook 02 |
| 8 | Hand-check result optimistic and partly circular (filter designed on the same 50 loans; CI below 80%) | Accepted: reported as such; two contradictory evidence entries corrected (confidence lowered); target wording changed to the conservative version (D23) |
| 9 | "Delay Draw" not caught; spreads with and without PIK mixed; t-2 newness and industry universe use later filings; one-quarter origination lag | Fixed: regex, PIK loans excluded. Accepted as limitations: later filings are used only to decide newness and the universe (sample construction), never as feature values |
