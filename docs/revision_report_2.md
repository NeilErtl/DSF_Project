# Revision report 2: working dataset after comparison with Patrick's version

Work order: `course_ref/5_For_the_repo/PROMPT_REVISION_2.md`. Second opinion tested against: Patrick's preprocessing
(`course_ref/patrick_version/`, 830 loans) and the comparison of 19 Nov 2026. Rules of CLAUDE.md and the lecturer
commitments still apply. Decisions: `docs/decisions.md` (D17, D30 to D36).

## 0. Plan (written before the work)
1. Match our loans to Patrick's candidates (family, quarter, distinctive borrower word, maturity within 7 days).
2. Undrawn lines: check at least 10 in EDGAR; also large principal gaps and positions below USD 100,000.
3. Secondary-market buyers: per-family measures and one general rule. 4. Refinancing variant file.
5. Tranche and near-match rules: quantify and test against acquisition dates. 6. Sample of 15 remaining differences.
7. `code/modelling_helpers.py`. 8. Rebuild twice, comparison table, adversarial review, documentation.

## 1. What was checked and decided
| Point | Evidence | Decision |
|---|---|---|
| Undrawn lines | 14 loans checked in EDGAR. (a) Goldman Private Credit lines without rate but with principal, cost and fair value printed are **unsettled purchases** (footnote: rate "not known prior to the settlement date"), not undrawn. (b) Lines with cost and fair value "-" (Recochem, Crewline, Kryptona, Northstar, Buffalo, ASM Buyer) are **unfunded commitments**; our old rule missed them. Two of Patrick's undrawn loans are funded (MGT Merger Target, Arrow Buyer). | D32: unfunded = no positive fair value and no positive cost; rate-less funded lines kept with flag `no_rate_tagged`. A borrower with only committed lines is kept in its pricing quarter (`committed_not_funded`, 31 core loans, after review). |
| Units and small positions | Varagon filings in thousands (principal 72,000 with fair value 70,000); a TCW filing 1,000 times too large ("Mark Andy" USD 7bn). | D33: filing-level unit rule in both directions (Patrick's rule, extended), floor USD 100,000. |
| Hold size | Principal agreed with Patrick within 5% for only 75% of shared loans: he sums all tranches of a loan, we took the largest line. | D34: sum of tranches with the same maturity; SOFR counts as stated if any family fund states it. |
| Palmer Square / secondary buyers | Palmer Square: no dated loans; 22% of its candidates are existing loans of other lenders (Goldman 24%, First Eagle 34%); 57% held by 3+ other managers (BlackRock 57%, Antares 61%, Jefferies 73%); not an outlier. | D17: general rule (more than half of dated loans bought earlier, or more than half of candidates existing loans of others). Excludes no family; Palmer Square stays. |
| Refinancings / add-ons | Variant `loans_incl_refi.csv`: 2,205 loans, 390 refinancings/add-ons, 58 with tenor 3 to 4 years. Dated refinancings acquired in their quarter: 47% (9 of 19), new borrowers 95% (261 dated). Median spread 4.31 vs 5.00 pp. | D35: main sample stays "new borrower"; variant for robustness. |
| Tranches with different spreads | 17 core loans; 1 dated case, so no precision evidence. | D30: adopted as a judgment call (a loan with two prices has no single target). |
| Near match (60 days) | After fixing its word choice: flags 28 core loans; 2 of 4 dated flagged loans were bought earlier vs 8.4% of the others (weak evidence). | D31: adopted (19 core loans removed). |
| Sample of 15 differences | 3 are loans Patrick counts although the family held them (name variants "GS Fullsteam", "VWhite Cap", "I AQ Sunshine"); 2 matching artifacts; 1 real error on our side (Stellus "Morgan Electrical": SOFR not written by the lead fund, fixed); 7 Goldman Private Credit 2026Q2 and Silver Point loans missing from Patrick's candidates (his parsing/timing). | Fixed our error and the "I " name marker. |

## 2. Adversarial review of this session's changes
A fresh agent found 8 issues; 6 fixed (near-match not reproducible: the first word came from an unordered set; the
new unfunded rule lost Goldman's largest committed deals; repeats in the variant; filings 1,000 times too large;
tranche ranges distorted by unit glitches; stray-letter rule too broad), 2 documented (syndicated mix, larger
effective gap in the final test). Details: `docs/ai_audit_trail.md`, session 3.

## 3. Effect on the sample
| | Before (session 2) | After |
|---|---:|---:|
| Core loans (`loans.csv`) | 1,798 | **1,766** |
| Train / test | 1,177 / 621 | 1,159 / 607 |
| All-BDC file | 7,385 | 7,320 |
| Precision on dated core loans | 94.1% | 94.6% (CI 91.2 to 96.7%, n = 276) |
| Hand check, (a) in final sample | 33 of 39 = 85% | 32 of 37 = 86% (CI 72 to 94%) |
| Variant incl. refinancings | none | 2,205 |

Medians unchanged (spread 5.00 pp, hold USD 10.1m, tenor 6.2 years). Largest families: Apollo 19%, Goldman Sachs 11%.

## 4. Remaining differences with Patrick's version
`output/tables/comparison_with_patrick.csv` (match on family, quarter, distinctive name word, maturity within 7 days).
In the 8 managers both cover, Patrick has 830 loans and we have 485; **390 of his match one of ours** (matching from his side; 102 of ours have no match in his data) (before: about 405 of
487). On these, the spread is identical for 99.2% (before 97%), the maturity for 97.9% (before 94%), the hold within
5% for 76% (he also counts funds whose own line is not a candidate, e.g. a fund's first filing).

| Patrick's loans not in ours (440) | Loans | | Our loans not in Patrick's (102) | Loans |
|---|---:|---|---|---:|
| Refinancing / add-on of an existing borrower | 260 | | He treats as undrawn (unsettled purchases, commitments in the pricing quarter) | 68 |
| Existing loan of another manager (our filter) | 90 | | Not a candidate in his data (parsing, timing; e.g. Goldman Private Credit 2026Q2) | 24 |
| Tenor 3 to 4 years (in our variant) | 29 | | His tranche, near-match, acquisition-date or loan-kind rules | 10 |
| Borrower held by the family before in our data (name variants he misses, e.g. "GS Fullsteam") | 26 | | | |
| Other (previous filing incomplete, spread/PIK, not a candidate, not core) | 35 | | | |

Of the 260 refinancings, 112 are in our variant file; the others are existing loans of other managers (filter applies
in the variant too), a second loan of the same borrower in one quarter (the variant keeps one line), or the same loan
within 60 days.

**Genuine definition choices for the team (Friday):**
1. **Refinancings and add-ons** (Patrick: in; we: out, variant file). Evidence favours out for the main sample.
2. **Existing loans of other managers** (Patrick: flag; we: drop). We drop because most are syndicated loans bought later.
3. **Universe**: 8 managers chosen on parse quality (Patrick) vs 31 by the industry rule (we).
4. **Tenor 3 to 4 years** (Patrick: in; we: variant only). 5. **Syndicated loans** (both keep them; flag for a
   sensitivity check: 163 core loans with spread at most 3.5 pp held by 3+ other managers).
