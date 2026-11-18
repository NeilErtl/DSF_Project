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
  rule-based industry-reporting universe gives about 2,400 (consequential decision D3, for team review).
- Inferring currency or instrument type where the filer writes nothing: such loans stay in the all-BDC file only.
