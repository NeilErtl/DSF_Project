"""Hand check v2: 50 loans of the final dataset (data/processed/loans.csv), checked by hand against EDGAR.

Why a second version of Patrick's hand check: his first 50 loans (docs/hand_check_patrick.csv) come from his own,
earlier preprocessing version; only 26 of them are in the final sample. This check draws 50 loans directly from the
final loans.csv, so every checked loan is a loan the models are trained and tested on (decision D55).

Run from the repository root:
    python code/hand_check_v2.py --draw       writes data/interim/hand_check_v2_proposals.csv
    python code/hand_check_v2.py              summary of the entered check -> output/tables/hand_check_v2_shares.csv

Step 1 (--draw). Sample: 50 loans, allocated to manager families by their share of the pool (largest remainder),
seed 2027. The pool excludes every loan of the earlier checks (docs/hand_check.csv, docs/hand_check_patrick.csv,
docs/verification_sample_30.csv, docs/verification_sample_10_release.csv): by loan_id, and for the two hand
checks also by the name rule of code/hand_check_fetch.py (same family and quarter, a shared distinctive word), so
the new check adds distinct loans. Weight of a loan = loans of its family in loans.csv /
loans drawn from that family.
For each loan the script searches every schedule of investments in the SEC BDC data sets (data/raw/sec/*.zip, as
downloaded by notebook 01) for the borrower and proposes a class with one report to open in EDGAR:
  - the same loan (maturity within 7 days) at another manager before the quarter -> (b), that manager's report;
  - an acquisition date inside the quarter printed in the lead BDC's report -> (a), this report;
  - only older loans of the borrower (other maturity) at other managers -> (a), the latest such report;
  - the borrower at other managers, maturity not tagged -> (a), the latest such report (check the maturity there);
  - otherwise -> (a), the lead BDC's report of the previous quarter (the loan must not be there).
Loans that three or more other managers first hold in the same quarter get a lower confidence (syndicated: the
filings cannot show whether they were bought at issue or later in the market).
Step 2 (by hand, Patrick Eppler, 25 Nov 2026): each proposal confirmed or corrected in the filing; result in
docs/hand_check_patrick_v2.csv (class_abc = final class).
"""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))
import utils_preprocess as up  # noqa: E402
from hand_check_fetch import name_words  # noqa: E402

SEED, N = 2027, 50
OUT_CSV = ROOT / "docs" / "hand_check_patrick_v2.csv"
EARLIER = ["hand_check.csv", "hand_check_patrick.csv", "verification_sample_30.csv",
           "verification_sample_10_release.csv"]
NAME_RULE = ["hand_check.csv", "hand_check_patrick.csv"]


def draw_sample(loans):
    ids, frames = set(), []
    for f in EARLIER:
        d = pd.read_csv(ROOT / "docs" / f, dtype={"loan_id": str})
        if "loan_id" in d:
            ids |= set(d.loan_id)
        if f in NAME_RULE:   # loans of other preprocessing versions: matched by name (their loan_id may differ)
            frames.append(d[["bdc_name", "quarter_str", "borrower"]])
    chk = pd.concat(frames)
    chk["family"] = [up.family_of_names([b]) for b in chk.bdc_name]
    keys = {(f, q, w) for f, q, b in zip(chk.family, chk.quarter_str, chk.borrower) for w in name_words(b)}
    excluded = [(i in ids) or any((f, q, w) in keys for w in name_words(b))
                for i, f, q, b in zip(loans.loan_id, loans.family, loans.quarter_str, loans.borrower)]
    pool = loans[~pd.Series(excluded, index=loans.index)]
    share = pool.family.value_counts() / len(pool) * N
    alloc = share.astype(int)
    for f in (share - alloc).sort_values(ascending=False).index[: N - alloc.sum()]:
        alloc[f] += 1
    s = pd.concat([pool[pool.family == f].sample(k, random_state=SEED) for f, k in alloc.items() if k > 0])
    s["weight"] = s.family.map(loans.family.value_counts() / alloc)
    print("excluded as checked before:", sum(excluded), " pool:", len(pool), " sample:", len(s))
    return s


# Borrower patterns where the distinctive words of the name are too generic or too narrow (checked by reading the
# matched lines), and the word to search for with Cmd+F in the report.
PATTERNS = {"ea1e03ea9f": [r"\bmh sub i\b"], "2c878ed07e": [r"\bkona buyer\b"], "02d900cca8": [r"\belevation newco\b"],
            "a65335c600": [r"\bdenali intermediate\b"], "922827ebb8": [r"\bessential services\b"],
            "ec24c9bffe": [r"\bprimo (?:brands|water)\b"], "d74a258404": [r"\bamer sports\b"],
            "323ac9a399": [r"\bprgx\b"], "5c935b9d29": [r"\bkarman holdings\b"], "0c93f11696": [r"\bineos us finance\b"]}
WORDS = {"ea1e03ea9f": "MH Sub", "5c935b9d29": "Karman", "d74a258404": "Amer Sports", "3566c6f2b0": "Titan Home",
         "da40a406b5": "Third Coast", "b976899a5a": "Crown Equipment", "453fe07215": "Falcon",
         "494e38d539": "Bending Spoons", "4be40df066": "Gen4", "f1bd0bb778": "O2B", "c34da7e717": "Detroit Quality",
         "bd0a97adc7": "TEGA", "1142cdf823": "ABC Buyer", "922827ebb8": "Essential Services", "9202228c0e": "Dartlet",
         "7ff2ba2751": "Said Intermediate", "a65335c600": "Denali", "0f738236b8": "Legacy", "cdf074b75d": "HIPH",
         "8e4dd7613e": "eResearch", "2c878ed07e": "Kona Buyer", "02d900cca8": "Elevation",
         "0c93f11696": "INEOS US Finance"}


def fmt(d):
    return f"{d.month:02d}/{d.day:02d}/{d.year}"


def load_holdings():
    keep = ["cik", "name", "ddate", "filed", "inlineurl", "identifier", "issuer_axis", "issuer_enum",
            "maturity_raw", "acq_date_raw"]
    zips = sorted((ROOT / "data" / "raw" / "sec").glob("*.zip"))
    h = pd.concat([d[keep] for d in (up.read_soi(z) for z in zips) if d is not None], ignore_index=True)
    h = h[h.ddate.notna()].copy()
    h["txt"] = (h.identifier.fillna("") + " | " + h.issuer_axis.fillna("") + " | " + h.issuer_enum.fillna("")).str.lower()
    h["dd"] = pd.to_datetime(h.ddate, errors="coerce")
    h["cik"] = pd.to_numeric(h.cik, errors="coerce")
    h["mat"] = pd.to_datetime(h.maturity_raw, errors="coerce")
    h["filed_d"] = pd.to_datetime(h.filed, errors="coerce")
    return h


def propose(s, loans, h):
    names = h.groupby("cik").name.agg(lambda x: list(dict.fromkeys(x.dropna())))
    fam = {c: up.family_of_names(n) for c, n in names.items()}
    fam.update(loans.groupby("cik").family.first().to_dict())
    # the report of a BDC for a date = its first filing for that date (later filings repeat it as a comparative)
    urls = h.dropna(subset=["inlineurl"]).sort_values("filed_d").groupby(["cik", "dd"]).inlineurl.first()
    rows = []
    for r in s.itertuples():
        qs = pd.Timestamp(r.quarter_start_date)
        pe, qe = qs - pd.Timedelta(days=1), qs + pd.offsets.QuarterEnd(0)
        m = np.ones(len(h), bool)
        for p in PATTERNS.get(r.loan_id, [r"\b" + re.escape(w) + r"\b" for w in name_words(r.borrower)]):
            m &= h.txt.str.contains(p, regex=True).values
        hit = h[m].copy()
        hit["mat2"] = hit.mat.fillna(hit.identifier.map(up.maturity_from_text))
        mat = pd.Timestamp(r.maturity_date)
        fam_ciks = {c for c, f in fam.items() if f == r.family} | {r.cik}
        oth = hit[(hit.dd < qs) & ~hit.cik.isin(fam_ciks)]
        cur = hit[(hit.cik == r.cik) & (hit.dd == qe)]
        acq_in = [a for a in sorted(pd.to_datetime(cur.acq_date_raw, errors="coerce").dropna().unique()) if qs <= a <= qe]
        same = oth[(oth.mat2 - mat).abs() <= pd.Timedelta(days=7)]
        diff = oth[oth.mat2.notna() & ((oth.mat2 - mat).abs() > pd.Timedelta(days=7))]
        word = max(name_words(r.borrower), key=len)
        found = re.search(re.escape(word), r.borrower, re.I)
        word = WORDS.get(r.loan_id, found.group(0) if found else word)
        conf = "high"
        if len(same):
            e = same.sort_values("dd").iloc[0]
            prop, label, link = "b", "open", urls.get((e.cik, e.dd))
            why = (f"Same loan (maturity {fmt(e.mat2)}) already held by {e['name'].title()} on {fmt(e.dd)}, before "
                   f"our quarter -> {r.family} bought it later")
            see = f"'{word}' with maturity {fmt(e.mat2)} (report date {fmt(e.dd)})"
        elif acq_in:
            prop, label, link = "a", "open (this report)", r.inlineurl
            why = f"The report prints an acquisition date {fmt(acq_in[0])}, inside the quarter; no BDC held this loan before"
            if len(oth):
                why += " (other managers held an older loan of this borrower, other maturity)"
            see = f"'{word}' with acquisition date {fmt(acq_in[0])}"
        elif len(diff):
            e = diff.sort_values("dd").iloc[-1]
            prop, conf, label, link = "a", "medium", "open (older loan)", urls.get((e.cik, e.dd))
            why = (f"Other managers held only an older loan of this borrower (e.g. {e['name'].title()} on {fmt(e.dd)}, "
                   f"maturity {fmt(e.mat2)}); our loan matures {fmt(mat)} -> new / refinancing loan")
            see = f"'{word}' with maturity {fmt(e.mat2)}, NOT {fmt(mat)}"
        elif len(oth):
            e = oth.sort_values("dd").iloc[-1]
            prop, conf, label, link = "a", "medium", "open (older holder)", urls.get((e.cik, e.dd))
            why = (f"Other managers held this borrower before (e.g. {e['name'].title()} on {fmt(e.dd)}), but no line "
                   f"with our maturity {fmt(mat)} was found in any SEC BDC filing -> most likely a new / refinancing loan")
            see = f"'{word}' found, but no line with maturity {fmt(mat)}"
        else:
            prop, label, link = "a", "open (previous report)", urls.get((r.cik, pe))
            why = "No BDC held this loan before the quarter (searched all SEC BDC filings)"
            see = f"'{word}' NOT found, or only with a maturity other than {fmt(mat)}"
        if prop == "a" and r.n_other_families_same_q >= 3 and not acq_in:
            conf = "medium" if conf == "high" else "low"
            why += (f"; caveat: {int(r.n_other_families_same_q)} other managers first hold it in the same quarter "
                    "(syndicated loan, could also be bought in the market)")
        rows.append(dict(loan_id=r.loan_id, family=r.family, bdc_name=r.bdc_name, quarter_str=r.quarter_str,
                         borrower=r.borrower, spread_pp=r.spread_pp, maturity_date=r.maturity_date,
                         principal=r.principal, proposal=prop, confidence=conf, why=why, link_label=label,
                         check_url=link, search_word=word, what_to_see=see, this_report_url=r.inlineurl,
                         strictly_new="no" if r.seen_at_other_family_before else "yes", weight=r.weight))
    return pd.DataFrame(rows)


def summarize():
    hc = pd.read_csv(OUT_CSV, dtype={"loan_id": str})
    loans = pd.read_csv(ROOT / "data" / "processed" / "loans.csv", dtype={"loan_id": str})
    assert hc.loan_id.isin(loans.loan_id).all() and hc.loan_id.is_unique and len(hc) == N
    rows = []

    def add(label, d):
        for k in ["a", "b", "c", "u"]:
            n_k = int((d.class_abc == k).sum())
            lo, hi = up.wilson_ci(n_k, len(d))
            lo = max(lo, 0.0)
            rows.append({"sample": label, "class": k, "n": n_k, "n_checked": len(d), "share": n_k / len(d),
                         "ci_low": lo, "ci_high": hi})

    add(f"hand check v2, all checked ({len(hc)})", hc)
    add(f"hand check v2, strictly new borrowers ({int((hc.strictly_new == 'yes').sum())})", hc[hc.strictly_new == "yes"])
    add(f"hand check v2, borrower seen at another manager before ({int((hc.strictly_new == 'no').sum())})",
        hc[hc.strictly_new == "no"])
    out = pd.DataFrame(rows)
    w = hc.weight
    out.loc[len(out)] = {"sample": "hand check v2, weighted by family (strata)", "class": "a",
                         "n": int((hc.class_abc == "a").sum()), "n_checked": len(hc),
                         "share": (w * (hc.class_abc == "a")).sum() / w[hc.class_abc.isin(["a", "b", "c"])].sum(),
                         "ci_low": np.nan, "ci_high": np.nan}
    # Combined with the earlier checks (distinct loans: v2 excludes every earlier loan; notebook 01, step 15e)
    prev = pd.read_csv(ROOT / "output" / "tables" / "hand_check_shares.csv")
    p = prev[prev["sample"].str.startswith("all checks combined") & (prev["class"] == "a")].iloc[0]
    n_prev = int(re.search(r"\((\d+)\)", p["sample"]).group(1))
    k = int(p.n) + int((hc.class_abc == "a").sum())
    n = n_prev + len(hc)
    lo, hi = up.wilson_ci(k, n)
    out.loc[len(out)] = {"sample": f"all four checks combined, distinct loans in final sample ({n})", "class": "a",
                         "n": k, "n_checked": n, "share": k / n, "ci_low": lo, "ci_high": hi}
    out.to_csv(ROOT / "output" / "tables" / "hand_check_v2_shares.csv", index=False)
    print(out.round(3).to_string(index=False))


if __name__ == "__main__":
    if sys.argv[1:] == ["--draw"]:
        ln = pd.read_csv(ROOT / "data" / "processed" / "loans.csv", dtype={"loan_id": str})
        smp = draw_sample(ln)
        prop = propose(smp, ln, load_holdings())
        (ROOT / "data" / "interim").mkdir(parents=True, exist_ok=True)
        prop.to_csv(ROOT / "data" / "interim" / "hand_check_v2_proposals.csv", index=False)
        print(prop.proposal.value_counts().to_dict(), prop.confidence.value_counts().to_dict())
    else:
        summarize()
