# CLAUDE.md: framework contract for AI assistants

This file is read by the AI at the start of every session. It holds the current rules only.
History of decisions lives in `docs/decisions.md`. What the AI contributed lives in `docs/ai_audit_trail.md`.

## Project in one paragraph
DSF group project (HSG, Fall 2026, Binswanger & Grigoryeva). We predict the **credit spread over SOFR**
of a **newly originated US private credit loan** held by a Business Development Company (BDC).
Users: a private credit fund's deal team (or a sponsor/CFO negotiating a loan) who wants a market-based
reference price before term sheets are signed. Data: SEC "Business Development Company (BDC) Data Sets",
file `soi.tsv` (schedule of investments, from Inline XBRL), public domain.
Deadline 30 Nov 2026 (report, slides, code, data). Interview: every step must be explainable.

## Prediction design (fixed; binding details in `docs/lecturer_feedback_and_commitments.md`, which wins in case of conflict)
- **Unit of observation:** one new loan = one borrower x one lender family x one quarter of first appearance.
  New = no BDC of the same manager family held it in the previous quarter; drop loans whose reported acquisition date
  is before that quarter; flag borrowers seen earlier at unaffiliated BDCs.
- **Target:** spread over SOFR, percentage points (errors in basis points). If the 50-loan hand check finds fewer than
  about 80% true originations, the target is reinterpreted as "spread of loans newly added to a BDC portfolio".
- **Cutoff:** start of the quarter of first appearance. Market-level spread from quarter t-2 filings, verified with the
  SEC filing date. A model predicting quarter t is trained only on loans up to t-2 (one-quarter gap).
- **Features allowed:** log held principal (approximation of hold size), tenor (maturity minus start of quarter),
  sector, manager family, loan type, market-level spread (t-2), external market data known at the cutoff.
  **Never as features:** interest rate, fair value, cost, PIK, floor.
- **Data type:** cross-section with a date (each loan appears once). Not a panel.
- **Split:** by time; test = 2025 Q3 to 2026 Q2, used once at the end; expanding-window validation by quarter.
- **Baselines:** (1) median new-loan spread of the reference quarter (t-2 rule); (2) median by sector and size class
  over the previous four available quarters.
- **Metrics:** MAE in bps (main), share within plus or minus 50 bps, MAE by test quarter and by manager.
- **Models:** only course models: linear regression, ridge, lasso, tree, random forest, boosting, small neural net.
  Horse race with the same folds and metric for all (deck 16, notebook 209).

## Coding rules
- Follow the style of the course notebooks (pandas, scikit-learn, matplotlib). No libraries beyond what the course uses
  unless agreed and logged.
- All preprocessing that learns from data (scaling, imputation, encoding, power transforms) lives inside a scikit-learn
  `Pipeline` / `ColumnTransformer` and is fitted on training data only (deck 06, notebook 211).
- Notebooks run top to bottom (Restart, Run All) and are the source of truth. Nothing important lives only in the chat
  or the terminal (deck P2).
- Fixed random seeds. Raw data in `data/raw/` is never edited. Processed data is produced by code into `data/processed/`.
- Every notebook step: a markdown cell saying what it does and why, and a check at its end (row counts, ranges, uniqueness).
- Repo structure follows `docs/github_workflow.md` (`code/01_preprocess.ipynb`, `02_estimate`, `03_evaluate`).

## How the AI must work
- Specify before generating: restate the task and what is fixed before writing code.
- The AI may take decisions on its own, without waiting for approval, **if** each one is logged in `docs/decisions.md`
  with: why the decision came up, the options considered, pros and cons of each, the evidence (numbers), the choice,
  and whether it is easy to reverse. Mark decisions that change the target, sample, split, metric or main model as
  `consequential`: the team reviews those afterwards.
- Report every change to definitions, sample, preprocessing, model or evaluation.
- Separate decisions made by the team from choices the AI made.
- Never touch the test set before the final evaluation. Never choose between models on the test set.
- Update existing files instead of creating new versions. One place for each thing.
- Write a short entry in `docs/ai_audit_trail.md` after each work session: what the AI did, what was checked, what was rejected.
- Do not push to `main`. Work on a branch; the team reviews via pull request.
