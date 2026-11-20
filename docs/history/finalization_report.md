# Finalization report (work order 3)

Work order: `course_ref/5_For_the_repo/PROMPT_FINALIZE.md`. Goal: the branch `data-preprocessing` pushed with a
clean, checked preprocessing that teammates can use for notebooks 02 and 03 without asking.

## 0. Plan (written before the work)
1. Corrections: target wording back to "spread over SOFR of newly originated loans" with the hand-check caveat (D23);
   the notebook writes `output/tables/headline_numbers.csv` and all docs take their numbers from it (lead BDCs = 45
   distinct `cik` in `loans.csv`); Patrick's 50 hand-checked loans mapped to our sample and combined with ours.
2. Notebook 01 in the course template style (Purpose / Input / Output, numbered steps); `code/main.ipynb` with `%run`;
   `modelling_helpers.py` with a per-test-quarter evaluation split; pinned `requirements.txt`; `.gitignore` checked.
3. Teammate docs: `docs/for_modelling.md` (one page) and a short `README.md`; privacy scan of the whole repository.
4. Three fresh subagents: out-of-sample verification of 30 loans in EDGAR, leakage and cutoff audit, fresh-reader test.
5. Two clean runs of notebook 01 (identical files), one run of `main.ipynb`, a final adversarial review, decisions and
   audit trail, commits, push of `data-preprocessing` (never `main`) and a pull request.

## 1. Corrections
| Item | Result |
|---|---|
| Target wording (D23) | Back to "spread over SOFR of newly originated loans", with the caveat (about 86% true originations, 95% CI 72 to 94%) in the notebook header, data dictionary, README, `for_modelling.md` and data report. |
| Headline numbers (D39) | Notebook step 15g writes `output/tables/headline_numbers.csv`; README, data report and `for_modelling.md` quote it. "BDCs" = lead BDCs, 45 distinct `cik` (48 names because of renames; 61 BDCs hold the loans; universe 67). The old "46" was the count before revision 2. |
| Patrick's hand check | `docs/hand_check_patrick.csv` (his 50 loans, credit: Patrick Eppler). 27 in our final sample: (a) 26, (b) 1. Our filters remove 8 of his 9 (b) loans and 15 of his 41 (a) loans (9 refinancings/add-ons, which the main sample excludes by definition). No loan checked by both. Combined, each loan once: (a) 58 of 64 = 91% (95% CI 81 to 96%). No filter changed. |

## 2. Fresh-agent checks
| Check | Result | Action |
|---|---|---|
| Out-of-sample verification, 30 loans (`docs/verification_sample_30.csv`) | Borrower, spread, maturity, principal 30/30; lien 27 (1 wrong, 2 not printed). (a) 24 = 80% (95% CI 63 to 90%), (b) 5, not new 1. | Fixed: WhiteHorse and Monroe joint-venture schedule lines counted as BDC holdings (D40, 18 loans removed). Documented: a rename after restructuring (Crescent), lien not written at Stellus, TCW, Onex. |
| Leakage and cutoff audit | No serious leakage; FRED and t-2 medians recomputed exactly. | Fixed: fair value no longer replaces an implausible principal (D37); splits also require the filing date before the cutoff (D38); cutoff asserts cover every quarter; dictionary roles. Documented: sample construction uses later filings; FRED dates are observation dates; test-period descriptives removed from the data report. |
| Fresh-reader test (reads only README, `for_modelling.md`, dictionary, helpers) | Loaded the data and printed all fold sizes; every number in the docs matched. 13 points of confusion: test protocol not named, baseline 2 underspecified, no helper for baselines or error frames, feature lists hard-coded, pitfall on `mkt_spread_t2_core` and unseen families wrong, all-BDC file limitations not stated. | Fixed: proposed main protocol (per test quarter), `baseline_t2`, `baseline_sector_size`, `error_frame`, feature arguments, corrected pitfalls, all-BDC limitations, role of each dictionary value, target name for the report. |

## 3. Repository
`code/main.ipynb` (runs 01 with `%run`; 02 and 03 as placeholders), notebook 01 with Purpose / Input / Output and
numbered steps, `modelling_helpers.py` with `test_quarter_splits`, `evaluate_per_test_quarter`, `summarize_errors`
and `known_before`, pinned `requirements.txt` (Python 3.12.10), `.gitignore` checked, `docs/for_modelling.md`,
short README, reports moved to `docs/history/`. Privacy: no e-mail address, token or local path in the files; two
pandas warnings that printed a local temp path were removed at the source; older commits of this unpushed branch
contained a local path in notebook outputs (see section 5).

## 4. Effect on the sample
| | Before (revision 2) | After |
|---|---:|---:|
| Core loans | 1,766 | **1,747** |
| Train / test | 1,159 / 607 | 1,143 / 604 |
| Final model training loans (gap) | 1,016 | 1,000 |
| All-BDC file / variant | 7,320 / 2,205 | 7,303 / 2,185 |
| Precision on dated core loans | 94.6% | 94.6% (CI 91.2 to 96.7%) |
| Verification sample (a), loans still in the sample | | 23 of 29 = 79% |

## 5. Final review, runs, history and push
- **Final adversarial review** (fresh agent, all changes of this session): every headline number recomputed and
  correct, no leakage of a never-feature. 15 findings, all documentation or wording: stale "fair value as size" text
  (step 6, D26), step references, the `instrument` description, stale numbers in older decisions, the verification
  sample drawn before D37/D40 (29 of 30 still in the sample, (a) 23 of 29), the caveat quoting only the most favourable
  check (verification figure added next to it), README calling the agent's verification a hand check, missing D4 and
  D28 in the data report, hard-coded "check passed" values. All fixed; test-period descriptives in step 15c are kept
  and labelled (no rule was set on them).
- **Runs.** Notebook 01 run with the final code, then `code/main.ipynb` (which runs 01 again): identical data files.
- **History.** Notebook outputs in the older, never pushed commits of this branch contained a local Windows path
  (with the user name). The branch history was rewritten before the first push to remove it from those outputs
  (a local backup ref was kept); the content of the commits is otherwise unchanged.
- **Push and pull request.** `data-preprocessing` pushed (never `main`); pull request into `main`.
