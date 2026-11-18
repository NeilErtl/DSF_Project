# [Project Title – ...]

**Collaborators:** Neil Ertl, Patrick Eppler, Mathis Aeby, Nathan Steiner

**Goal:** one sentence - follows after project idea

## How to rebuild the data

The working dataset is built by `code/01_preprocess.ipynb` from public sources only (SEC BDC Data Sets, FRED).
Raw files are downloaded by the notebook into `data/raw/` (not in Git, about 600 MB); outputs go to `data/processed/`.

1. Install Python 3.12 and the packages: `python -m pip install -r requirements.txt`
2. The SEC asks automated clients to identify themselves with a contact e-mail. Either set the environment variable
   `SEC_USER_AGENT`, or create a one-line file `sec_user_agent.txt` in the repository root (it is gitignored), e.g.
   `DSF-HSG-student-project your.name@student.unisg.ch`.
3. Open `code/01_preprocess.ipynb` and run *Restart, Run All* (about 10 minutes on a laptop; the first run also
   downloads the data). Or from the `code/` folder:
   `jupyter nbconvert --to notebook --execute --inplace 01_preprocess.ipynb`

Outputs:

| File | Content |
|---|---|
| `data/processed/loans.csv` | Main sample: new loans of BDCs that state borrower industries |
| `data/processed/loans_all_bdc.csv` | Same rules, all BDCs (industry may be missing), for the robustness check |
| `data/processed/data_dictionary.csv` | Every column: meaning, unit, known at the cutoff, role |
| `data/processed/sector_mapping.csv` | Raw industry label to sector |
| `data/processed/bdc_family_mapping.csv` | BDC to manager family |
| `output/tables/*.csv`, `output/figures/*.png` | Funnel, precision checks, distributions |

Documentation: `docs/data_report.md` (what was done and the results), `docs/decisions.md` (all decisions),
`docs/ai_audit_trail.md` (what the AI did), `docs/hand_check.csv` (50 loans checked against the filings).
