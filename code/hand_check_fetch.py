"""Helper for the hand check (docs/hand_check.csv): fetch each sampled loan's filing from EDGAR and show the text
around the borrower name, with automatic checks of spread, maturity, principal and industry.

Run from the repository root:  python code/hand_check_fetch.py  > data/interim/hand_check_evidence.txt
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


def main():
    ua = up.sec_user_agent(ROOT)
    hc = pd.read_csv(ROOT / "docs" / "hand_check.csv", dtype={"loan_id": str})
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
              "industry", any(norm(r.industry) in norm(s) for s in snips))
        for s in snips[:3]:
            print("   ", s[:600].encode("ascii", "replace").decode())


if __name__ == "__main__":
    main()
