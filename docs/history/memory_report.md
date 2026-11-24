# Memory report: notebook 01 on an 8 GB machine (work order 6)

Work order: `course_ref/5_For_the_repo/PROMPT_MEMORY_FIX.md`. Goal: notebook 01 runs with a peak memory well below
8 GB (target under 4 GB) and writes byte-identical output files.

## How memory was measured
An instrumented copy of the notebook (outside the repository) adds a first cell that starts a thread sampling the
kernel's memory every 20 to 50 ms, and after every code cell a line that logs the peak during the cell. Two measures
(Windows 11, Python 3.12, pandas 3.1.1):
- **RSS** (working set): the memory resident in RAM; Windows can trim or compress it, so it can understate.
- **Private** (committed private bytes): everything the process has allocated, resident or not. This is closer to
  what a container limit (Nuvolos) enforces, so it is the main measure here.
Every run starts from the raw zips (no cache in `data/interim/`), as on a fresh machine.

## Before (main at 77c10eb)
Run time 12 to 15 minutes. Peak RSS 4.8 GB, **peak private memory 5.9 GB**; memory is never released after step 8.

| Cell (step) | Peak RSS, GB | Peak private, GB | Private at end, GB | Seconds |
|---|---|---|---|---|
| 5 (2, read all zips) | 2.39 | 2.84 | 2.13 | 11 |
| 7 (3, current period) | 2.61 | 3.06 | 1.92 | 11 |
| 11 (5, borrower names) | 2.24 | 2.68 | 2.36 | 356 |
| 13 (6, loan lines) | 2.30 | 2.74 | 2.61 | 21 |
| 15 (7, candidates) | 2.58 | 3.03 | 2.99 | 18 |
| 17 (8, new-loan rule) | 4.81 | 5.48 | 5.25 | 153 |
| 19 (9, sample filters) | 4.38 | 5.51 | 5.32 | 81 |
| 29 (10, processed files) | 3.59 | 5.81 | 5.81 | 4 |
| 43 (end) | 3.65 | 5.93 | 5.92 | 0 |

**Responsible steps and objects** (object sizes measured after step 8 by re-executing the cells in a script):
- Step 2 stacked all 23 zips into one table of 2,035,844 rows x 35 text columns (about 2 GB) and kept it until step 3
  had taken the current period and the comparatives from it.
- `cur` (current-period rows, about 1.5 GB) stayed alive to the end, although after step 5 only three of its columns
  are used; `hold` (all holdings with parsed names, about 1.4 GB), `ln` (loan lines, about 0.9 GB) and the
  intermediate tables of step 7 (`elig`, `same_loan`, about 0.9 GB) also stayed alive to the end.
- Step 8 builds `HoldingsIndex` over 1.5 million holdings and comparatives: one token set per row, with a separate
  string object for every word of every row (about 1.9 GB), on top of everything above. This is the peak.

## Changes (code only; no rule, threshold, order of operations, rounding or seed changed)
1. **Step 2 reads the zips one at a time.** Of each file it keeps the current-period rows (`ddate == period`) and the
   prior-period comparatives with an identifier (5 columns); the stacked table is never built. Rows keep their row
   number in the stacked table, so order and index are unchanged. Ten columns that no step uses (`qtrs`, issuer,
   type, lien, instrument and affiliation axes, cash rate, acquisition date tag) are dropped after reading. The
   `soi_all.pkl` cache is removed: reading all zips takes about 15 seconds.
2. **`HoldingsIndex` shares memory between equal values.** An identifier repeats every quarter: equal identifiers now
   share one token set and equal words one string object. Sets and their contents are unchanged.
3. **Objects are freed after their last use** (`del`, `gc.collect()`): `cur` is cut to `cik`, `q_int`, `family`
   after step 5; the step 7 intermediates after step 7; `hold`, the holdings evidence and the index after step 8;
   `ln` after the industry finder of step 9. `match_cache` is kept (used by the de-duplication of step 9).

Side effect outside the outputs: the gitignored derived cache `data/interim/cand.pkl` no longer has the ten unused
columns (no tracked code reads it).

## After (branch fix-01-memory)
Run time about 10 minutes (13 to 18 minutes for the in-place runs while other work ran on the machine). Peak RSS
2.2 GB, **peak private memory 2.6 GB** (before: 4.8 and 5.9 GB).

| Cell (step) | Peak RSS, GB | Peak private, GB | Private at end, GB | Seconds |
|---|---|---|---|---|
| 5 (2, read the zips) | 0.96 | 1.40 | 1.13 | 10 |
| 7 (3, current period) | 1.15 | 1.58 | 1.15 | 10 |
| 11 (5, borrower names) | 1.38 | 1.85 | 1.31 | 352 |
| 13 (6, loan lines) | 1.13 | 1.56 | 1.49 | 20 |
| 15 (7, candidates) | 1.41 | 1.85 | 1.60 | 19 |
| 17 (8, new-loan rule) | 2.19 | 2.63 | 1.52 | 137 |
| 19 (9, sample filters) | 1.30 | 1.75 | 1.40 | 33 |
| 29 (10, processed files) | 1.00 | 1.86 | 1.86 | 2 |
| 43 (end) | 1.05 | 1.94 | 1.94 | 0 |

**Whole project (`main.ipynb`, runs 01, 02 and 03 in one kernel).** Peak private memory 2.65 GB (RSS 2.2 GB) during
notebook 01; notebooks 02 and 03 stay below (2.2 GB). Run time 46 to 53 minutes on our laptop: notebook 01 takes 39
to 46 minutes inside `%run` against 10 to 18 minutes run alone (the same slowdown existed before this change).

## Proof that nothing changed
1. **Reference.** Before any change, every file in `data/processed/`, `output/tables/` and `output/figures/` (41
   files) was copied outside the repository.
2. **Steps 2 and 3 in isolation.** The new `cur` and comparatives equal the old ones built from the stacked table
   (`assert_frame_equal` with exact values, plus identical index and dtypes; 1,072,616 and 701,289 rows).
3. **Notebook 01, three runs from a clean kernel** (one instrumented, two in place): 41 of 41 files byte-identical
   to the reference each time. The printed text of the two in-place runs is identical.
4. **Notebooks 02 and 03.** Run on the result, they reproduce 34 of 41 files byte for byte. Seven differ from the
   committed versions: Linear regression and Ridge predictions of notebook 02 differ in the third to sixth decimal
   (at most 0.1 bps in a table), and the files built from them. **The same seven files differ in the same way when
   notebooks 02 and 03 of untouched `main` are run on this machine** (separate worktree of main): main and this
   branch give 41 of 41 identical files here. So the cause is not this change; most likely it is floating-point
   linear algebra that differs between machines (the committed predictions were produced on another machine). The seven files are
   therefore not part of this branch (restored from main).
5. **Code review** by a fresh agent ("find any change that could alter results ..."): no result-changing issue.
   It checked every deleted name against later use, merges and whole-frame operations, the dtype behaviour of
   `concat`, and the token-set rebuild (index, weights and all 16,677 borrower matches identical).

## Not done (possible further savings, not needed below 4 GB)
`cur` could be cut before the 6-minute name parsing of step 5, and a few small objects (`keys`, `vocab`, `fil`) are
never freed. Notebook 02's machine dependence (point 4) is a separate issue for the notebook 02 owner.
