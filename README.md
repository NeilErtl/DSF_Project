# Predicting the spread over SOFR of new private credit loans

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
3. Open `code/main.ipynb` and run *Restart, Run All*. It runs `01_preprocess.ipynb` (10 to 20 minutes run alone and
   46 minutes inside `main.ipynb` on our laptop, longer on the first run because of the downloads; peak memory about
   2.6 GB, so it runs on an 8 GB machine such as Nuvolos, `docs/history/memory_report.md`), `02_estimate.ipynb` (about 2 minutes) and `03_evaluate.ipynb` (seconds).
   To rebuild only the models and the evaluation, run `code/02_estimate.ipynb` and then `code/03_evaluate.ipynb`:
   they read `data/processed/` (in Git) and need no download or `sec_user_agent.txt`. Two runs of notebook 01 give
   byte-identical output files. From the command line
   (in `code/`): `jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=-1 main.ipynb`
   (`-1` switches off the per-cell time limit: notebook 01 runs inside one `%run` cell, which takes longer than
   the default limit).

## The working dataset (numbers from `output/tables/headline_numbers.csv`)
- `data/processed/loans.csv`: **1,705 new loans**, 2023Q2 to 2026Q2, 31 manager families; the lead BDC of each loan
  is one of 45 BDCs (distinct `cik`). Train 1,122 loans (to 2025Q2), test 583 (2025Q3 to 2026Q2).
- Target: spread over SOFR of newly originated loans (median 5.00 pp). Four origination checks: our hand check 32 of
  36 (89%), Patrick's first hand check 25 of 26 (96%; loans of his earlier preprocessing version), an out-of-sample
  check 24 of 30 (80%, 95% CI 63 to 90%), and Patrick's hand check v2 of 50 loans drawn from the final dataset 47 of
  50 (94%, 95% CI 84 to 98%); no filter was designed on the last two, so they are the cleanest estimates. Over all 141
  distinct checked loans in the sample 90% (95% CI 84 to 94%). About one loan in five to one in ten may be a purchase
  or transfer rather than a fresh origination; it is still a loan newly priced into a BDC portfolio.
- Largest families: Apollo 19%, Goldman Sachs 11%, BlackRock 7%, Antares 7%, First Eagle 5%.
- Robustness files: `loans_all_bdc.csv` (6,979 loans, all BDCs), `loans_incl_refi.csv` (2,170 loans incl.
  refinancings and add-ons). Columns: `data_dictionary.csv`. How to use them: `docs/for_modelling.md`.

## Result on the test quarters (numbers from `output/tables/test_headline.csv`, `docs/evaluation_report.md`)
- Main model (random forest on the deviation from the market median, chosen on the validation quarters before any
  test prediction): **MAE 58.1 bps** on 583 test loans (2025Q3 to 2026Q2), 55% within plus or minus 50 bps.
- Baseline 1 (market median of new loans in quarter t-2): 86.3 bps; baseline 2 (sector x size median): 79.9 bps.
- Gap to baseline 1: -28.2 bps (95% bootstrap interval -33.3 to -23.1); the model is better in every test quarter
  and in the robustness variants (all BDCs, refinancings included, without likely syndicated loans).

## Folder map
| Folder | Content |
|---|---|
| `code/` | `main.ipynb` (runs everything), `01_preprocess.ipynb`, `utils_preprocess.py` (functions of notebook 01), `02_estimate.ipynb` (baselines, models, horse race, choice of the main model, predictions for 03), `03_evaluate.ipynb` (test metrics, by quarter and family, bootstrap, robustness; fits no model), `modelling_helpers.py` (loading, pipeline, time splits, metrics for 02 and 03), `hand_check_fetch.py` (EDGAR look-up for the hand checks), `hand_check_v2.py` (sample and proposals of hand check v2) |
| `data/raw/`, `data/interim/` | Downloads and caches, rebuilt by the code, not in Git |
| `data/processed/` | Working datasets, data dictionary, sector and family mappings; predictions of notebook 02 for notebook 03 (`predictions_validation.csv`, `predictions_test.csv`, `predictions_robustness.csv`) |
| `output/tables/`, `output/figures/` | Funnel, precision, hand check, headline numbers; validation race (02); test metrics `test_*.csv` (03); figures, including the report and slide figures of notebook 03 (step 9) |
| `docs/` | `for_modelling.md`, `data_report.md`, `model_report.md` (summary of notebook 02), `evaluation_report.md` (summary of notebook 03), `decisions.md`, hand checks (`hand_check.csv`, `hand_check_patrick.csv`, `hand_check_patrick_v2.csv`, `verification_sample_30.csv`), `lecturer_feedback_and_commitments.md`, `ai_audit_trail.md`, `history/` (work reports) |

## Sample definitions
| Definition | Reason | Robustness file or flag |
|---|---|---|
| Refinancings and add-ons of existing borrowers out (D35) | Only 52% of dated ones were acquired in their quarter, against 95% for new borrowers: mostly add-ons priced at old terms | `loans_incl_refi.csv`, flag `refi_of_existing_borrower` |
| Existing loans of other managers dropped (D22) | Same loan held earlier by an unaffiliated BDC: a secondary purchase, not a new price | none (filter step 9b); kept borrowers seen earlier elsewhere carry `seen_at_other_family_before` |
| Universe: BDCs that state borrower industries (D3) | Sector is a committed feature; 31 families instead of a hand-picked list | `loans_all_bdc.csv` (run without sector) |
| Tenor 4 to 8 years (D8) | Shorter tenors are mostly older loans bought later (lower precision) | `loans_incl_refi.csv`, flag `tenor_3_to_4` |
| Syndicated loans kept, with a sensitivity check (D25) | No clean marker; club deals look alike | flag `n_other_families_same_q` (3 or more: 39% of loans) |

Main test protocol (D41): one model per test quarter, trained on all loans up to t-2 (`docs/for_modelling.md`).

## Who did what
- Mathis Aeby: preprocessing, notebook 01 and `docs/data_report.md`; documentation; his part of the report and
  slides.
- Patrick Eppler: independent preprocessing version and comparison, hand checks of 50 loans each
  (`docs/hand_check_patrick.csv`, `docs/hand_check_patrick_v2.csv`), design of the modelling helpers; his part of the
  report and slides.
- Neil Ertl: estimation, notebook 02 and `docs/model_report.md` (validation design, baselines, model race, residual
  target, choice of the main model, test predictions); his part of the report and slides.
- Nathan Steiner: evaluation on the test quarters, notebook 03 and `docs/evaluation_report.md`; his part of the
  report and slides.

## Use of AI
**Tools.** Claude (Anthropic): mainly the model Claude Opus 5.5 in Claude Code for code and documentation, and the
Claude chat for explanations and text drafts.

**What the AI did.**
- *Code:* it wrote most of the code of the three notebooks (preprocessing, estimation, evaluation) and the figures,
  following our instructions.
- *Checks:* it ran automated checks (row counts, leakage and cutoff audits, reruns giving identical output); fresh AI
  agents re-checked the pipeline and a sample of 30 loans against the SEC filings (`docs/verification_sample_30.csv`).
- *Hand checks:* it drew the samples and prepared, for each loan, the filing to open and a proposed class
  (`code/hand_check_fetch.py`, `code/hand_check_v2.py`).
- *Text:* it drafted the documentation in this repository and first versions of parts of the report, which we edited.

**What we did.**
- We chose the question, the data source and the design agreed with the lecturers (target, cutoff, split,
  baselines, metrics, allowed models; `docs/lecturer_feedback_and_commitments.md`).
- In the preprocessing, the AI took smaller decisions itself and logged them; choices that change the target, sample,
  split or metric were marked `consequential` and reviewed by the team.
- In estimation and evaluation, every consequential choice (feature set, main model, test protocol) was put to the
  notebook owner with options and a recommendation before it was taken.
- We decided every hand-checked loan ourselves in the original filings (`docs/hand_check.csv`,
  `docs/hand_check_patrick.csv`, `docs/hand_check_patrick_v2.csv`), compared the pipeline with an independent
  preprocessing version, and reviewed all changes through pull requests.

**How it is documented.** The rules for the AI are in `CLAUDE.md`; every AI decision is logged with its evidence in
`docs/decisions.md`, and every work session in `docs/ai_audit_trail.md`.
