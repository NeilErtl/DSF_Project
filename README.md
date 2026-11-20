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
- Target: spread over SOFR of newly originated loans (median 5.00 pp). Three origination checks: our hand check 32 of 37 (86%), Patrick's
  hand check 26 of 27 (96%), and an out-of-sample check 24 of 30 (80%, 95% CI 63 to 90%; the cleanest estimate, since
  no filter was designed on it); over all 93 distinct checked loans in the sample 87% (95% CI 79 to 93%). About one
  loan in five to one in ten may be a purchase or transfer rather than a fresh origination; it is still a loan newly
  priced into a BDC portfolio.
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

## Sample definitions (status: recommended by the preprocessing team, to be confirmed)
| Definition | Reason | Robustness file or flag |
|---|---|---|
| Refinancings and add-ons of existing borrowers out (D35) | Only 47% of dated ones were acquired in their quarter, against 95% for new borrowers: mostly add-ons priced at old terms | `loans_incl_refi.csv`, flag `refi_of_existing_borrower` |
| Existing loans of other managers dropped (D22) | Same loan held earlier by an unaffiliated BDC: a secondary purchase, not a new price | none (filter step 9b); kept borrowers seen earlier elsewhere carry `seen_at_other_family_before` |
| Universe: BDCs that state borrower industries (D3) | Sector is a committed feature; 31 families instead of a hand-picked list | `loans_all_bdc.csv` (run without sector) |
| Tenor 4 to 8 years (D8) | Shorter tenors are mostly older loans bought later (lower precision) | `loans_incl_refi.csv`, flag `tenor_3_to_4` |
| Syndicated loans kept, with a sensitivity check (D25) | No clean marker; club deals look alike | flag `n_other_families_same_q` (3 or more: 38% of loans) |

Main test protocol (D41): one model per test quarter, trained on all loans up to t-2 (`docs/for_modelling.md`).

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
