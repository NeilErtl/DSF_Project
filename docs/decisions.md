# Decision log

Status: `proposed` = suggested in the feasibility study, may be changed. `taken` = implemented (by the team or the AI, with justification). `agreed` = confirmed by the team in a review session.
Consequential decisions (target, sample, split, metric, dropping observations, main model) are reviewed by the whole team (deck P3).
For every new or changed decision, add below the table: why it came up, options, pros and cons, evidence, choice, reversibility.

| # | Decision | Status | Reason |
|---|----------|--------|--------|
| D1 | Data source: SEC BDC Data Sets, `soi.tsv`, quarter-ends Sep 2022 to Jun 2026 (16 quarters). | proposed | Official, free, public domain, already structured (spread, principal, maturity as tagged fields). Not on Kaggle (only 25-row commercial teasers on other questions, checked 9 Nov 2026). |
| D2 | One filing per BDC and quarter: if a quarter has several filings (amendments), keep the latest. | proposed | Avoids duplicate loans. 8 of 1,895 BDC-quarters are affected. |
| D3 | BDC universe: BDCs whose loan descriptions state the industry (about 16 funds, 7 manager families: Goldman Sachs, PennantPark, Varagon, Silver Point, SCP, Great Elm, Investcorp). | proposed | Industry is a key feature and is only reliably available in these descriptions. Keeps the sample in the 1,000 to 2,000 range. Limitation: results speak for these lenders, not the whole market. |
| D4 | New loan = the **borrower** did not appear in the same BDC one quarter earlier. Where the BDC reports an acquisition date, use it directly (acquired within the quarter). | proposed | The prototype compared description strings; when a BDC reworded its descriptions, old loans looked new. Check: only 54% of prototype "new" loans with an acquisition date were really acquired in that quarter. Borrower-name matching fixes this. |
| D5 | Keep only funded, floating-rate, USD term loans over SOFR. Drop revolvers, delayed-draw lines, equity, fixed-rate debt, EURIBOR/SONIA loans. | proposed | Revolvers and delayed-draw lines are priced differently; non-USD base rates are a different market. |
| D6 | Duplicates: the same loan held by several funds of the same manager counts once (one row per borrower x manager family x quarter). Loans of the same borrower held by different managers stay separate. | proposed | Co-investing funds of one manager share one pricing decision. Different managers price independently. |
| D7 | Spread cleaning: convert unit errors (e.g. 525 to 5.25), keep spreads between 1 and 15 percentage points. | proposed | Values outside this range are data errors for senior private credit. |
| D8 | Remaining maturity filter: keep loans with 2 to 8 years to maturity at origination; drop impossible values (negative, over 10 years). | proposed (open) | A freshly signed term loan has 5 to 7 years. The exact window is to confirm once D4 is implemented. |
| D9 | Sectors: map the raw industry labels (about 295) to about 11 GICS-style sectors with a documented mapping table. | proposed | 295 categories are too many for one-hot encoding with about 1,500 loans. |
| D10 | Market features: high-yield credit spread (FRED series BAMLH0A0HYM2) and SOFR level at the end of the previous quarter; median new-loan spread of the previous quarter in our own data. | proposed | Spreads fell from about 5.85 (2023) to 4.50 (2026) percentage points; models need to see the market level. Previous quarter only, to respect the cutoff. |
| D11 | Split by time: test = last 4 quarters (2025 Q3 to 2026 Q2); train = earlier quarters; expanding-window CV by quarter inside train. | proposed | Imitates how the model meets new data: pricing future loans. |
| D12 | Baseline: median spread of new loans in the previous quarter. Metric: MAE in basis points. | proposed | Simple, realistic rule a deal team could use; MAE is easy to explain ("we are off by x bps on average"). |
