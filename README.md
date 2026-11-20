# Pricing new private credit loans from public BDC filings

**Collaborators:** Neil Ertl, Patrick Eppler, Mathis Aeby, Nathan Steiner (DSF, HSG, Fall 2026)

**Question.** What credit spread over SOFR should a deal team expect for a newly originated US private credit loan,
before the term sheet is signed? **Decision maker:** the deal team of a private credit fund, or a sponsor or CFO
negotiating a loan, who wants a market-based reference price.

## Data
SEC "Business Development Company (BDC) Data Sets" (schedules of investments from Inline XBRL, file `soi.tsv`,
public domain) and FRED market series (BAA10Y, SOFR). Notebook 01 downloads everything into `data/raw/` (not in Git,
about 600 MB). The SEC asks automated clients to identify themselves: create a one-line file `sec_user_agent.txt` in
the repository root (it is gitignored), for example `DSF-HSG-student-project your.name@example.com`, or set the
environment variable `SEC_USER_AGENT`.

## How to run
1. Python 3.12: `python -m pip install -r requirements.txt`
2. Create `sec_user_agent.txt` (see above).
3. Open `code/main.ipynb` and run *Restart, Run All* (it runs `01_preprocess.ipynb`; about 25 minutes, longer on the
   first run because of the downloads). Notebooks 02 and 03 will be added to `main.ipynb`.

## The working dataset (numbers from `output/tables/headline_numbers.csv`)
- `data/processed/loans.csv`: **1,747 new loans**, 2023Q2 to 2026Q2, 31 manager families; the lead BDC of each loan
  is one of 45 BDCs (distinct `cik`). Train 1,143 loans (to 2025Q2), test 604 (2025Q3 to 2026Q2).
- Target: spread over SOFR of newly originated loans (median 5.00 pp). The hand check finds about 86% true
  originations (95% CI 72 to 94%); the remaining loans are newly added to a BDC portfolio through purchases or
  transfers. A further out-of-sample check of 30 loans finds 80% (95% CI 63 to 90%).
- Largest families: Apollo 19%, Goldman Sachs 11%, BlackRock 7%, Antares 7%, First Eagle 5%.
- Robustness files: `loans_all_bdc.csv` (7,303 loans, all BDCs), `loans_incl_refi.csv` (2,185 loans incl.
  refinancings and add-ons). Columns: `data_dictionary.csv`. How to use them: `docs/for_modelling.md`.

## Folder map
| Folder | Content |
|---|---|
| `code/` | `main.ipynb` (runs everything), `01_preprocess.ipynb`, `utils_preprocess.py` (functions of notebook 01), `modelling_helpers.py` (loading, pipeline, time splits, metrics for 02 and 03), `hand_check_fetch.py` (EDGAR look-up for the hand checks) |
| `data/raw/`, `data/interim/` | Downloads and caches, rebuilt by the code, not in Git |
| `data/processed/` | Working datasets, data dictionary, sector and family mappings |
| `output/tables/`, `output/figures/` | Funnel, precision, hand check, headline numbers, figures |
| `docs/` | `for_modelling.md`, `data_report.md`, `decisions.md`, hand checks (`hand_check.csv`, `hand_check_patrick.csv`, `verification_sample_30.csv`), `lecturer_feedback_and_commitments.md`, `ai_audit_trail.md`, `history/` (work reports) |

## Open decisions for the team (status: proposed)
1. **Refinancings and add-ons** of existing borrowers: out of the main sample, in `loans_incl_refi.csv` (D35).
2. **Existing loans of other managers** (bought later in the market): dropped, not flagged (D22).
3. **Universe**: all BDCs that state borrower industries (31 families) rather than a hand-picked list (D3).
4. **Tenor**: 4 to 8 years in the main sample; 3 to 4 years only in the variant (D8, D35).
5. **Syndicated loans**: kept; sensitivity check without loans held by 3 or more other families (D25).

## Who did what
- Mathis Aeby: preprocessing (notebook 01), documentation. *(to be completed)*
- Patrick Eppler: independent preprocessing version, comparison, hand check of 50 loans, modelling helpers design.
  *(to be completed)*
- Neil Ertl, Nathan Steiner: *(to be completed)*

## Use of AI
The preprocessing code and documentation were written with an AI assistant (Claude Code) under the rules in
`CLAUDE.md`: every decision it took is logged with evidence in `docs/decisions.md`, every work session in
`docs/ai_audit_trail.md`. The results were checked against the original filings by hand (`docs/hand_check.csv`,
prepared with the AI and re-checked by Mathis; Patrick's `docs/hand_check_patrick.csv`), by a fresh AI agent
(`docs/verification_sample_30.csv`), and against Patrick's independent version.
