# Release report (work order 5)

Work order: `course_ref/5_For_the_repo/PROMPT_FINAL_RELEASE.md`. PR #3 was converted to draft at the start
(Step 0) and is marked ready only if the release gate (Step 4) is met.

## Step 1. Decisions (D41, taken by the preprocessing owner, to be confirmed by the team)
- Target stays "the spread over SOFR of newly originated loans", shown everywhere with the three origination checks
  (our hand check, Patrick's, the out-of-sample check) and their combination over all distinct checked loans
  (`headline_numbers.csv`), plus the sentence on purchases and transfers.
- Main test protocol: one model per test quarter (`evaluate_per_test_quarter`); secondary view `final_train_test`.
- The five sample definitions are kept, "recommended by the preprocessing team, to be confirmed", each with its reason
  and robustness file or flag in the README.

## Step 2. Polish (D42)
pp and % columns rounded to 4 decimals, USD to whole dollars; cleaned display names (`borrower`); fixed role
vocabulary in `data_dictionary.csv` (asserted against `NUM` and `CAT`); a "Current definitions in force" table at the
top of `docs/decisions.md`; README, `for_modelling.md` and `data_report.md` re-read against `headline_numbers.csv`.

## Step 3. Checks by a dedicated checker agent, fixes, second check
| Check | First checker | After D43 (second checker) | After D44 |
|---|---|---|---|
| 1 Row rules | PASS | PASS | PASS |
| 2 Newness | FAIL (spelling variants, sister-BDC acquisition dates, label names) | FAIL (8 brand-prefixed or doubled names, 1 SARON loan) | PASS (1 documented residual, D44) |
| 3 Cutoff | PASS | PASS | not re-run (no feature changed) |
| 4 Numbers | PASS (one false claim in D13) | PASS for headline; 3 stale doc numbers | PASS |
| 5 EDGAR, 10 more loans | 7 (a), 2 (b), 1 not new (since removed) | values still match for the 9 loans | not re-run |
| 6 Fresh clone | PASS (byte-identical) | PASS (byte-identical) | PASS (byte-identical, 44 min) |
| 7 Teammate test | PASS | PASS | not re-run |
| 8 Hygiene | PASS | PASS | not re-run (no new file types) |

Fixes: D43 (spelling variants, family-level acquisition date and spreads, per-line spread unit, industry labels are
not names, "InvestmentType" and "amp;"), D44 (matching key from the cleaned name, brand-prefix rule, implied base rate
at least 2.5 pp). Sample: 1,747 to 1,725 (D43) to 1,705 loans (D44). Documented residuals: D43 and D44.

## Step 4. Release gate
Met. The second checker re-ran newness, row rules, numbers and the fresh clone on the final data commit: all PASS.
- Checker items: all PASS. Remaining low items (none affects correctness): "Project Titan Tyber Medical"
  (cba6cf5c91, very likely not new, documented in D44); keys with trailing amendment text (Onex "LSCS Holdings 2025
  refinancing", "Victra fourth amendment"), new today but a later round would rely on the near-match rule. Two wording
  points were fixed in `docs/decisions.md` (implied-base rule, matching key now from the cleaned name).
- `main.ipynb` run twice after D44: all 16 output files byte-identical, and identical to the fresh-clone run (new venv
  from `requirements.txt`). Justified exception: the notebook file itself differs only in execution timestamps and in
  how the kernel split printed output into chunks; the content is identical.
- README, `for_modelling.md`, `data_report.md` and `decisions.md` agree with `headline_numbers.csv` (checker).
- `docs/ai_audit_trail.md` session 5 written; `docs/history/` holds the revision, finalization and this release report.
