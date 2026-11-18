# Lecturer feedback and our binding commitments

Source: our project description (10 Nov 2026, file `docs/Project_Description_BDC_Loan_Spreads.docx`), the lecturers'
answers and feedback, and our reply (section 5). **The commitments below are binding.** Where they conflict with
`docs/decisions.md` or the work order, these commitments win.

## Lecturers' answers to our questions
- A pooled cross-section of new loans over 13 quarters with a time split is acceptable, even with repeated lenders.
- Identifying new loans from consecutive filings is acceptable as a starting point and a reasonable approximation;
  we must acknowledge its limitations.
- Target and features from the same filing are fine, as long as the features are available at the stated cutoff.

## Lecturers' feedback (summary)
1. A loan appearing for the first time need not be an origination (secondary purchase, transfer between funds).
   Check a sample against the original filings; if it cannot be verified, adjust the interpretation of the target.
2. Distinguish origination dates, reporting dates and filing dates. A spread statistic from the previous quarter's
   filings may not have been public at the term-sheet date. Verify what loan size and maturity measure.
3. Report performance separately by test quarter, in addition to overall MAE. Clarify the implications of
   restricting the analysis to the 16 BDCs that report industry.

## Our commitments (section 5 of our reply)
### (1) Identifying originations
- Hand-check about **50 loans** flagged as new, **stratified by manager**, against the original 10-Q/10-K filings.
- Where a BDC reports an acquisition date: compare it with the quarter of first appearance and **drop loans acquired before that quarter**.
- Classify each checked loan as (a) originated in that quarter, (b) originated earlier and acquired, (c) transferred
  from an affiliated vehicle. Report the shares with **95% confidence intervals**.
- A loan is new only if **no BDC of the same manager family** held it in the previous quarter (captures transfers
  between affiliated funds).
- **Flag** loans whose borrower appeared earlier in the portfolio of an **unaffiliated** BDC (likely secondary purchases).
- If fewer than about **80%** of checked loans are originations, the target becomes "the spread of loans newly added
  to a BDC portfolio".

### (2) Timing of the predictors (cutoff)
- Cutoff = **start of the quarter** in which a loan first appears (the exact term-sheet date is unknown).
- Filings for quarter t-1 are submitted up to about 45 days after its end (later for 10-Ks), so they may not be public
  at the cutoff. The **market-level spread is computed from quarter t-2 filings**, and we verify with the SEC filing
  date (`filed`) that they were submitted before the start of quarter t.
- The same rule applies to both baselines and to the training data: a model predicting quarter t is trained only on
  loans up to quarter t-2 (**one-quarter gap** in validation and testing).
- **Loan size** = the BDC's held principal at the reporting date (its share of the loan, possibly after drawdowns or
  repayments): an approximation of the lender's hold size, not the total facility size. State this.
- **Tenor** = maturity date minus the start of the quarter of first appearance (known at the cutoff).

### (3) Evaluation and sample
- Report MAE overall **and for each test quarter**, for all models and baselines.
- The 16-BDC restriction: results apply mainly to these lenders (Goldman Sachs about 52%, PennantPark about 25% of loans)
  and to smaller positions (median USD 5.2m). Compare the distributions of spread, position size and tenor with
  **all other BDCs**.
- Robustness check: run the model **without the industry variable on all BDCs that report spreads**. So the data step
  must also produce an all-BDC version of the new-loan dataset (same rules, industry may be missing).

## Also stated in our project description
- Features: log loan size, maturity/tenor, industry (grouped into about 12 sectors), manager, loan type, market-level
  median spread of new loans (now from t-2 filings, see above).
- **Leakage exclusions: no interest rate** (contains SOFR + spread), **no fair value or cost** (only known at the
  reporting date), **no PIK or floor** (negotiated together with the spread). PIK/floor may be kept as descriptive
  columns or for sample filtering, but never as model features.
- Baselines: (1) median spread of new loans in the reference quarter; (2) median by industry and size class over the
  previous four quarters (both respecting the t-2 rule).
- Metrics: MAE in bps (main), share of loans within plus or minus 50 bps, errors by quarter and by manager.
- Split: by time, test = the last four quarters (2025 Q3 to 2026 Q2), used once; expanding-window validation.
