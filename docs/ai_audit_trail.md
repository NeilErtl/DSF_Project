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

**Human verification (19 Nov 2026).** Mathis re-checked the 50 hand-check loans against the EDGAR filings himself; all values and classifications in `docs/hand_check.csv` were confirmed, with two corrections handled in session 2 (count of checked loans in the final sample; principal printed for all 50).

## Session 2, 19 Nov 2026: corrections after the team's re-check, Claude Opus 5.5 in Claude Code

**Task.** The team's re-check of the hand check reported (1) only 39 of the 50 checked loans in `loans.csv`
(report: 41) and principal printed for all 50 (report: 47), and (2) borrower names with a prefix glued to the name.

**What the AI did**
- Verified (1) before changing anything: matching by `loan_id` gives 39 and by borrower and quarter 41; the
  difference is two Jefferies loans that are in the sample under new ids (the id hashes the family). Fetched the
  three disputed filings: the principal is printed in the schedule table for all three, so 50/50 is right.
- Verified (2): the prefixes come from the XBRL member names (Apollo/MidCap display names, a stray capital letter)
  and from the parser cutting an industry label in two. Counted 140 + 7 + 9 affected core names. Fixed the parser
  (D28), reran the notebook top to bottom twice (identical files), compared the sample before and after
  (`docs/data_report.md`, section 5).
- Replaced the hand-check matching by a rule that uses quarter, family, a distinctive name word and the loan terms
  (D29), so the shares are computed by the notebook from the current files: 39 loans, (a) 33, (b) 5, (c) 1.

**What was checked**
- The 4 loans that entered and a sample of the 32 that left the core sample; all 50 hand-check pairs between
  `docs/hand_check.csv` and `loans.csv` by eye.

**What was rejected**
- Hard-coding the re-check's shares (32 / 6 / 1 of 39): they describe the files before the name fix counted by
  `loan_id`; the notebook now reports what the current files give.
- A "same maturity and spread held earlier" rule for renamed borrowers: most matches were different borrowers.
- A broad "known shorter name" rule: it cut generic names ("Comoto Holdings LLC" -> "Holdings LLC").
- First versions of the new hand-check matching (name only with 3-letter words; legal words such as "Inc"
  counted): they paired checked loans with other loans of the same quarter.

## Session 3, 19 to 20 Nov 2026: revision after comparison with Patrick's version, Claude Opus 5.5 in Claude Code

**Task.** Work order `course_ref/5_For_the_repo/PROMPT_REVISION_2.md`: test our dataset against Patrick's independent
version (`course_ref/patrick_version/`), revise where the evidence says so, report in `docs/history/revision_report_2.md`.

**What the AI did**
- Matched our loans to Patrick's candidates and dataset (family, quarter, distinctive name word, maturity) so that
  every difference has a cause (`output/tables/comparison_with_patrick.csv`).
- Undrawn lines: checked 14 loans in the EDGAR filings. Two cases: unsettled Goldman Sachs purchases (funded, no rate
  tagged: Patrick's rule wrong) and commitments with cost and fair value "-" (our rule wrong). Revised the rule (D32).
- Adopted from Patrick, with credit: filing-level thousands rule and USD 100,000 floor (D33), hold size summed over
  tranches (D34), tranche-consistency rule (D30), near-match rule (D31), the design of `modelling_helpers.py` (D36).
- Built the refinancing variant `loans_incl_refi.csv` (D35), per-family secondary-buyer diagnostics (D17), a sample
  of 15 differences (fixed: base rate when the lead fund writes none; Goldman's "I " name marker).
- Reduced the notebook's memory use (the full extract is freed after step 3): one run had timed out on a laptop with
  little free memory.

**What was checked**
- Precision against acquisition dates for every candidate rule and per family; hand-check counts from the current files;
  two clean runs with identical outputs; adversarial review of this session's changes by a fresh agent.

**Adversarial review (second reviewer, changes of this session only).** Eight findings:

| # | Finding | Response |
|---|---|---|
| 1 | Near-match rule not reproducible: the "first word" came from an unordered set (changed with Python's hash seed) and was often "and" or "amendment" | Fixed: words in reading order, must be rare; rule re-tested (D31); two clean runs now identical |
| 2 | New unfunded rule lost Goldman's largest new loans for good (committed in quarter t, "held before" in t+1) | Fixed: a borrower with only committed lines at a fund is a candidate in its pricing quarter, flag `committed_not_funded` |
| 3 | Variant file repeated loans across quarters (short names never matched) and its refinancings are mostly not new | Fixed: short names keep their words, exact-name check added, each loan once at first appearance; low precision of refinancings reported (D35) |
| 4 | Filings tagged 1,000 times too large (TCW 2023; "Mark Andy" USD 7bn) | Fixed: thousands rule made symmetric; assert hold below USD 1bn |
| 5 | Syndicated loans in a "private credit" sample | Not filtered (no clean marker; club deals look alike); reported with counts, decision for the team (D25) |
| 6 | Tranche rule adopted without evidence; unit glitches create false tranche differences | Fixed: only spreads within 1 to 15 pp compared; logged as a judgment call (D30) |
| 7 | Stray-letter fix mangled "L V F Holdings" | Fixed: restricted to Goldman's "I " marker |
| 8 | Final train/test gap is 2 to 4 quarters for later test quarters; unseen categories map to the reference | Documented in `modelling_helpers.py` |

**What was rejected**
- Patrick's "no interest rate = undrawn" rule as such (wrong for unsettled purchases, EDGAR evidence).
- Excluding Palmer Square by judgement, or any family by the spread level (selection on the target).
- Refinancings/add-ons in the main sample (dated precision about 40% against about 94% for new borrowers).

## Session 4, 20 Nov 2026: finalization (work order 3), Claude Opus 5.5 in Claude Code

**Task.** Work order `course_ref/5_For_the_repo/PROMPT_FINALIZE.md`: corrections, three independent checks by fresh
agents, repository structure, documentation for the modelling notebooks, push of `data-preprocessing` and a pull
request. Report: `docs/history/finalization_report.md`.

**What the AI did**
- Target wording back to "spread over SOFR of newly originated loans" with the hand-check caveat (D23, team
  instruction); headline numbers written by the notebook (D39; "BDCs" = 45 lead BDCs).
- Mapped Patrick's 50 hand-checked loans to the final sample (27 in it, (a) 26) and combined both checks without
  double counting ((a) 58 of 64 = 91%), with credit to Patrick.
- Drew a 30-loan verification sample (seed 2026, by family, excluding both hand checks) and had a fresh agent verify
  it in EDGAR; had a second fresh agent audit leakage and the cutoff; a third read only the README, `for_modelling.md`,
  the data dictionary and the helpers and reported what confused it; a fourth reviewed all changes adversarially.
- Fixes from these checks: fair value no longer enters the hold size (D37); filing date checked in the splits (D38);
  WhiteHorse and Monroe joint-venture schedules excluded (D40, 18 loans); cutoff asserts for every quarter; both
  baselines, error frames and a per-test-quarter evaluation in `modelling_helpers.py`; docs corrected.
- Repository: `code/main.ipynb`, Purpose / Input / Output header, pinned `requirements.txt`, `.gitignore`,
  `docs/for_modelling.md`, short README, reports moved to `docs/history/`; removed two pandas warnings that printed a
  local path into notebook outputs.

**What was checked**
- Verification: borrower, spread, maturity and principal correct for 30 of 30; (a) 24 of 30 = 80% (79% on the 29 still
  in the sample). Leakage audit: FRED values and t-2 medians recomputed exactly for all quarters. Fresh reader: every
  number in the docs matched what it printed. Final review: every headline number recomputed and correct.
- The helpers were tested on validation folds only; a test-set smoke test was refused by the permission classifier
  and replaced by a pseudo-test on training quarters (CLAUDE.md: never touch the test set).

**What was rejected**
- A general "no net-assets percentage = joint venture" rule (at Antares, Golub and others the untagged lines are own
  holdings); a rename rule for restructured borrowers (one case, no reliable signal); changing filters after
  Patrick's hand check (one (b) case is not a pattern).
- Final review findings handled as documentation only: test-period descriptives remain in notebook step 15c
  (labelled, no rule set on them); the combined hand-check interval is a secondary figure.

## Session 5, 20 to 21 Nov 2026: final polish, release checks (work order 5), Claude Opus 5.5 in Claude Code

**Task.** Work order `course_ref/5_For_the_repo/PROMPT_FINAL_RELEASE.md`: freeze PR #3 as a draft, take the open
wording and protocol decisions, polish the processed files, run exhaustive checks by a dedicated checker agent, and
release only if every check passes. Report: `docs/history/release_report.md`.

**What the AI did**
- Converted PR #3 to draft with a comment. Logged D41 (target wording with all three origination checks, main test
  protocol one model per test quarter, five sample definitions "recommended, to be confirmed") and D42 (rounding of
  processed files, cleaned display names, fixed role vocabulary in the dictionary, definitions table in decisions).
- Launched the checker agent with the verbatim instructions. Its newness audit failed: loans that were spelling
  variants of borrowers the family held, acquisition dates at sister BDCs, spreads lost to a unit error, spread
  differences across a family's BDCs, industry labels parsed as names. All fixed in the pipeline (D43): 1,747 to
  1,725 loans. The checker's EDGAR spot check of 10 more loans is in `docs/verification_sample_10_release.csv`.
- A second fresh checker re-ran all checks after D43. It passed rows, cutoff, numbers, the EDGAR batch, the
  fresh clone, the teammate test and hygiene, but found 8 loans that were not new (brand-prefixed or doubled names)
  and one loan priced over SARON. Fixed (D44): matching key from the cleaned name, a suffix rule in the variant
  check, implied base rate at least 2.5 pp, three more energy industry labels: 1,725 to 1,705 loans. The same checker
  then re-ran newness, row rules, numbers and the fresh clone on the final commit.
- The checker hit the API rate limit once and was resumed; a scheduled restart was set at the user's request.
- A first `main.ipynb` run failed on nbconvert's per-cell time limit (notebook 01 runs in one `%run` cell while the
  checker used memory); runs now use `--ExecutePreprocessor.timeout=-1` (documented in README).

**What was checked**
- Two `main.ipynb` runs after D44 and a fresh-clone run (new venv from `requirements.txt`) with byte-identical
  output files (the notebook file itself differs only in execution timestamps and how the kernel split printed
  output into chunks; its content is identical); row
  rules, cutoff dates, every headline number and every number quoted in the docs; hygiene (no e-mail, path or token).

**What was rejected**
- A general fuzzy-name rule without a maturity condition for short names (too many false matches); re-parsing the 447
  candidate lines whose parsed name is an industry label (left for a parser improvement; the lines are excluded).
- Hand-made exclusions of single loans: residual odd names are documented in D43 and D44 instead (e.g. "Project
  Titan Tyber Medical", very likely not new, but no name rule links it to its earlier holding).
