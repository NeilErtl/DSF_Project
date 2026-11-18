# Data report: working dataset of newly originated private credit loans

Notebook: `code/01_preprocess.ipynb` (runs top to bottom). Decisions with evidence: `docs/decisions.md`.

## 0. Task as understood (restated before building)
- **Question.** Predict the spread over SOFR of a newly originated US private credit loan held by a BDC, so that a
  deal team (or sponsor / CFO) has a market-based reference price before the term sheet is signed.
- **Unit.** One new loan = one borrower x one manager family x one quarter of first appearance. New = no BDC of the
  same family held the borrower before; loans with an acquisition date before that quarter are dropped; borrowers
  seen earlier at unaffiliated BDCs are flagged.
- **Target.** Spread over SOFR in percentage points (errors to be reported in basis points).
- **Cutoff.** Start of the quarter of first appearance. Market-level spread from quarter t-2 filings (checked with
  the filing date); external market data: last value before the cutoff. Never features: interest rate, fair value,
  cost, PIK, floor.
- **Split.** By time: test = 2025Q3 to 2026Q2 (used once), expanding-window validation inside training, one-quarter
  gap (a model for quarter t is trained on loans up to t-2).
- **Baselines.** (1) Median new-loan spread of the reference quarter (t-2 rule); (2) median by sector and size class
  over the previous four available quarters.
- **Metric.** MAE in bps (main), share within +/- 50 bps, MAE by test quarter and by manager.
- **Plan for this step.** Download SEC and FRED data by code; keep one current-period filing per BDC and quarter;
  parse borrower names from the free-text identifiers of all managers; identify new loans at the family level with a
  matching rule that survives rewording; build features known at the cutoff; validate (funnel, precision against
  acquisition dates, hand check of 50 loans, distributions, cutoff checks); have a fresh AI reviewer attack the result.
  No model fitting and no learned preprocessing in this step.
