"""Helper for the hand checks: fetch each sampled loan's filing from EDGAR and show the text around the borrower
name, with automatic checks of spread, maturity, principal and industry.

Run from the repository root:
    python code/hand_check_fetch.py  > data/interim/hand_check_evidence.txt            (docs/hand_check.csv)
    python code/hand_check_fetch.py --draw-verification                                 (draws the 30-loan sample)
    python code/hand_check_fetch.py docs/verification_sample_30.csv > data/interim/verification_evidence.txt
The verification sample (work order 3) is a second, out-of-sample check: 30 loans of loans.csv as of revision 2
(1,766 loans, before D37 and D40; redrawing from the current file gives a different sample), seed 2026,
stratified by family, excluding the loans of both earlier hand checks (ours and Patrick's).
The classification (a)/(b)/(c) and the evidence column of docs/hand_check.csv were then filled in by reading this
output together with the earlier holdings of each borrower at other BDCs (see 01_preprocess, step 15e).
Requires the SEC User-Agent (SEC_USER_AGENT or sec_user_agent.txt, see README). About one request per second.
"""
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))
import utils_preprocess as up  # noqa: E402


def norm(s):
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def name_words(b):
    t = [x for x in up.tokens(str(b)) if x not in up.LEGAL_WORDS]
    return {x for x in t if len(x) >= 3 and x not in up.GENERIC_NAME_WORDS} or set(t)


def draw_verification_sample(n=30, seed=2026):
    """30 loans of loans.csv, allocated to families by their share (largest remainder), excluding hand-checked loans.

    A loan counts as hand-checked when a loan of either hand check has the same quarter and family and shares a
    distinctive borrower word (the matching rule of 01_preprocess, step 15e, without the maturity condition, so the
    exclusion is generous).
    """
    loans = pd.read_csv(ROOT / "data" / "processed" / "loans.csv", dtype={"loan_id": str})
    checked = pd.concat([pd.read_csv(ROOT / "docs" / "hand_check.csv")[["bdc_name", "quarter_str", "borrower"]],
                         pd.read_csv(ROOT / "docs" / "hand_check_patrick.csv")[["bdc_name", "quarter_str", "borrower"]]])
    checked["family"] = [up.family_of_names([b]) for b in checked.bdc_name]
    keys = {(f, q, w) for f, q, b in zip(checked.family, checked.quarter_str, checked.borrower) for w in name_words(b)}
    excluded = [any((f, q, w) in keys for w in name_words(b))
                for f, q, b in zip(loans.family, loans.quarter_str, loans.borrower)]
    pool = loans[~pd.Series(excluded, index=loans.index)]
    share = pool.family.value_counts() / len(pool) * n
    alloc = share.astype(int)
    for f in (share - alloc).sort_values(ascending=False).index[: n - alloc.sum()]:
        alloc[f] += 1
    sample = pd.concat([pool[pool.family == f].sample(k, random_state=seed) for f, k in alloc.items() if k > 0])
    cols = ["loan_id", "family", "bdc_name", "quarter_str", "borrower", "spread_pp", "maturity_date", "principal",
            "lien", "industry", "acq_date", "inlineurl"]
    out = sample[cols].sort_values(["family", "quarter_str"]).copy()
    for c in ["found_in_filing", "spread_ok", "maturity_ok", "principal_ok", "lien_ok", "class_abc", "confidence",
              "evidence"]:
        out[c] = ""
    print("excluded as hand-checked:", sum(excluded), " pool:", len(pool), " sample:", len(out))
    return out


def main(path=ROOT / "docs" / "hand_check.csv"):
    ua = up.sec_user_agent(ROOT)
    hc = pd.read_csv(path, dtype={"loan_id": str})
    for r in hc.itertuples():
        snips, nhits = up.filing_snippets(r.inlineurl, r.borrower, ua, width=500, max_hits=80)
        sp = float(r.spread_pp)
        sp_pats = {f"{sp:.2f}%", f"{sp:.1f}%", f"{sp:.3f}%", f"+{int(round(sp * 100))}", f"{sp:.2f}".rstrip("0") + "%"}
        m = pd.Timestamp(r.maturity_date)
        mat_pats = {f"{m.month}/{m.day}/{m.year}", f"{m.month:02d}/{m.day:02d}/{m.year}",
                    f"{m.month:02d}/{m.day:02d}/{str(m.year)[2:]}", f"{m.month}/{m.day}/{str(m.year)[2:]}",
                    f"{m.month:02d}/{m.year}", f"{m.month}/{m.year}", m.strftime("%B %Y"), m.strftime("%b %Y")}
        p = float(r.principal)
        pr_pats = {f"{p:,.0f}", f"{p / 1000:,.0f}", f"{round(p / 1000):,}", f"{p / 1e6:,.1f}"}

        def has(pats):
            return any(any(x in s.replace(" %", "%").replace("+ ", "+") for x in pats) for s in snips)

        print("=====", r.loan_id, r.family, r.quarter_str, r.borrower, "| hits", nhits,
              "| spread", has(sp_pats), "maturity", has(mat_pats), "principal", has(pr_pats),
              "industry", any(norm(r.industry) in norm(s) for s in snips), "| url", r.inlineurl)
        for s in snips[:3]:
            print("   ", s[:600].encode("ascii", "replace").decode())


if __name__ == "__main__":
    if sys.argv[1:] == ["--draw-verification"]:
        target = ROOT / "docs" / "verification_sample_30.csv"
        if target.exists():
            sys.exit(f"{target.name} exists (results entered); delete it first to draw again")
        draw_verification_sample().to_csv(target, index=False)
    else:
        main(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs" / "hand_check.csv")
