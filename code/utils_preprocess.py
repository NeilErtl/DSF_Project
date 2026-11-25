"""Helper functions for code/01_preprocess.ipynb.

Kept in a separate file so that the notebook stays readable. Every function is small and
documented; the notebook explains why each step is done and checks its result.
"""
import os
import time
from pathlib import Path

import requests

SEC_BASE = ("https://www.sec.gov/files/datastandardsinnovation/data/"
            "business-development-company-bdc-data-sets/")
FRED_BASE = "https://fred.stlouisfed.org/graph/fredgraph.csv?id="


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------
def sec_user_agent(repo_root):
    """Return the User-Agent for SEC requests.

    The SEC fair-access policy asks automated clients to identify themselves with a contact
    e-mail. We do not hard-code a personal address in a shared repository. The value is read
    from the environment variable SEC_USER_AGENT or, if not set, from the gitignored file
    `sec_user_agent.txt` in the repository root (one line, e.g. "Project-name you@example.com").
    """
    ua = os.environ.get("SEC_USER_AGENT", "").strip()
    if ua:
        return ua
    path = Path(repo_root) / "sec_user_agent.txt"
    if path.exists():
        raw = path.read_bytes()
        # PowerShell may write UTF-16 with a byte order mark; handle both encodings.
        text = raw.decode("utf-16") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw.decode("utf-8-sig")
        ua = text.strip().strip('"').strip()
    if not ua:
        raise RuntimeError("Set SEC_USER_AGENT or create sec_user_agent.txt (see README, 'How to rebuild the data').")
    return ua


def sec_file_names(first_quarter="2022q4", last_quarter="2025q4", last_month="2026_10"):
    """List the BDC data set zip names: quarterly files, then monthly files from 2026."""
    names = []
    y, q = int(first_quarter[:4]), int(first_quarter[-1])
    ly, lq = int(last_quarter[:4]), int(last_quarter[-1])
    while (y, q) <= (ly, lq):
        names.append(f"{y}q{q}_bdc.zip")
        q += 1
        if q == 5:
            y, q = y + 1, 1
    my, mm = int(last_month[:4]), int(last_month[-2:])
    for m in range(1, mm + 1):
        names.append(f"{my}_{m:02d}_bdc.zip")
    return names


def download(url, dest, user_agent, pause=0.5):
    """Download url to dest unless dest already exists. Returns the file size in bytes.

    The pause keeps us far below the SEC limit of 10 requests per second.
    """
    dest = Path(dest)
    if dest.exists() and dest.stat().st_size > 0:
        return dest.stat().st_size
    dest.parent.mkdir(parents=True, exist_ok=True)
    r = requests.get(url, headers={"User-Agent": user_agent}, timeout=300)
    r.raise_for_status()
    tmp = dest.with_suffix(dest.suffix + ".part")
    tmp.write_bytes(r.content)
    tmp.replace(dest)
    time.sleep(pause)
    return dest.stat().st_size


# ---------------------------------------------------------------------------
# Extraction of soi.tsv
# ---------------------------------------------------------------------------
META_COLS = ["adsh", "cik", "name", "ddate", "qtrs", "form", "filed", "period", "inlineurl"]

# Columns of soi.tsv we keep (short name -> SEC column label). Columns missing in a file become NaN.
SOI_COLS = {
    "identifier": "Investment, Identifier Axis",
    "issuer_axis": "Investment, Issuer Name Axis",
    "issuer_enum": "Investment, Issuer Name [Extensible Enumeration]",
    "industry_axis": "Industry Sector Axis",
    "industry_enum": "Investment, Industry Sector [Extensible Enumeration]",
    "type_axis": "Investment Type Axis",
    "type_enum": "Investment, Type [Extensible Enumeration]",
    "lien_axis": "Lien Category Axis",
    "instrument_axis": "Financial Instrument Axis",
    "affiliation_axis": "Investment, Issuer Affiliation Axis",
    "rate_type_enum": "Investment, Variable Interest Rate, Type [Extensible Enumeration]",
    "spread_raw": "Investment, Basis Spread, Variable Rate",
    "rate_raw": "Investment Interest Rate",
    "floor_raw": "Investment, Interest Rate, Floor",
    "pik_raw": "Investment, Interest Rate, Paid in Kind",
    "cash_rate_raw": "Investment, Interest Rate, Paid in Cash",
    "maturity_raw": "Investment Maturity Date",
    "acq_date_raw": "Investment, Acquisition Date",
    "principal_raw": "Investment Owned, Balance, Principal Amount",
    "face_raw": "Investment Owned, Face Amount",
    "fair_value_raw": "Investment Owned, Fair Value",
    "fair_value2_raw": "Initial fair value of Investment",
    "cost_raw": "Investment Owned, Cost",
    "cost2_raw": "Adjusted cost basis",
    "net_assets_pct_raw": "Investment Owned, Net Assets, Percentage",
}


def read_soi(zip_path):
    """Read the kept columns of soi.tsv from one BDC data set zip (all values as text).

    Returns None if the zip has no (or an empty) soi.tsv.
    """
    import zipfile
    import pandas as pd

    with zipfile.ZipFile(zip_path) as z:
        names = [n for n in z.namelist() if n.endswith("soi.tsv")]
        if not names or z.getinfo(names[0]).file_size < 100:
            return None
        wanted = set(META_COLS) | set(SOI_COLS.values())
        d = pd.read_csv(z.open(names[0]), sep="\t", dtype=str, usecols=lambda c: c in wanted,
                        quoting=3, encoding="utf-8", encoding_errors="replace")
    d = d.rename(columns={v: k for k, v in SOI_COLS.items()})
    for c in list(SOI_COLS) + META_COLS:
        if c not in d.columns:
            d[c] = pd.NA
    d["source_file"] = Path(zip_path).name
    return d[META_COLS + list(SOI_COLS) + ["source_file"]]


# ---------------------------------------------------------------------------
# Manager families
# ---------------------------------------------------------------------------
# (keyword in the BDC name, family). First match wins. BDCs without a match form their own family.
FAMILY_RULES = [
    ("GOLDMAN SACHS", "Goldman Sachs"), ("PHILLIP STREET", "Goldman Sachs"), ("WEST BAY", "Goldman Sachs"),
    ("PENNANTPARK", "PennantPark"), ("SILVER POINT", "Silver Point"), ("VARAGON", "Varagon"),
    ("SCP PRIVATE CREDIT", "SLR"), ("SLR ", "SLR"), ("GREAT ELM", "Great Elm"), ("INVESTCORP", "Investcorp"),
    ("GOLUB", "Golub"), ("ANTARES", "Antares"), ("ARES ", "Ares"), ("BLACKSTONE", "Blackstone"), ("BLUE OWL", "Blue Owl"),
    ("OWL ROCK", "Blue Owl"), ("APOLLO", "Apollo"), ("MIDCAP", "Apollo"), ("MORGAN STANLEY", "Morgan Stanley"),
    ("NORTH HAVEN", "Morgan Stanley"), ("SL INVESTMENT", "Morgan Stanley"), ("T SERIES", "Morgan Stanley"),
    ("KKR", "KKR / FS"), ("FS ", "KKR / FS"), ("NEW MOUNTAIN", "New Mountain"), ("NMF SLF", "New Mountain"),
    ("NUVEEN CHURCHILL", "Nuveen Churchill"), ("OAKTREE", "Oaktree"), ("OHA ", "OHA"), ("BARINGS", "Barings"),
    ("BAIN CAPITAL", "Bain Capital"), ("BLACKROCK", "BlackRock"), ("CARLYLE", "Carlyle"),
    ("AB PRIVATE", "AllianceBernstein"), ("AUDAX", "Audax"), ("CRESCENT", "Crescent"), ("FIDELITY", "Fidelity"),
    ("FRANKLIN BSP", "Franklin BSP"), ("HPS ", "HPS"), ("KAYNE", "Kayne Anderson"), ("MONROE", "Monroe"),
    ("MAIN STREET", "Main Street"), ("MSC INCOME", "Main Street"), ("PROSPECT", "Prospect"), ("STELLUS", "Stellus"),
    ("STONE POINT", "Stone Point"), ("TCW ", "TCW"), ("TRIPLEPOINT", "TriplePoint"), ("TWIN BROOK", "AG Twin Brook"),
    ("COMVEST", "Comvest"), ("CCS IX", "Crescent"), ("JEFFERIES", "Jefferies"), ("SENIOR CREDIT INVESTMENTS", "Jefferies"), ("LGAM PRIVATE CREDIT", "Morgan Stanley"), ("COMMONWEALTH CREDIT PARTNERS", "Comvest"), ("SIXTH STREET", "Sixth Street"), ("ONEX", "Onex"), ("LORD ABBETT", "Lord Abbett"),
    ("MUZINICH", "Muzinich"), ("GLADSTONE", "Gladstone"), ("BC PARTNERS", "BC Partners"), ("BCP INVESTMENT", "BC Partners"),
    ("PORTMAN RIDGE", "BC Partners"), ("LOGAN RIDGE", "BC Partners"), ("FIRST EAGLE", "First Eagle"),
    ("VENTURE LENDING", "WTI"), ("WTI FUND", "WTI"), ("STEPSTONE", "StepStone"), ("CION", "CION"),
]


def family_of_names(names):
    """Family of a BDC with several registrant names: the first name (in time) that matches a rule."""
    for n in names:
        fam = family_of(n)
        if fam != str(n).upper().title():
            return fam
    return family_of(names[-1])


def family_of(name):
    """Return the manager family of a BDC from its registrant name (rules above)."""
    n = str(name).upper()
    for key, fam in FAMILY_RULES:
        if key in n:
            return fam
    return n.title()


# ---------------------------------------------------------------------------
# Text parsing of the free-text investment identifier
# ---------------------------------------------------------------------------
import re
from collections import Counter, defaultdict

import numpy as np
import pandas as pd

LEGAL_WORDS = {"inc", "incorporated", "llc", "corp", "corporation", "co", "ltd", "limited", "lp", "llp",
               "lllp", "plc", "gmbh", "ag", "sa", "sas", "sarl", "bv", "nv", "ab", "as", "oy", "pty",
               "ulc", "spa", "the", "pbc", "lc", "kg", "aps", "asa", "srl", "se", "dac"}
_LEGAL_RE = (r"(?:Inc|Incorporated|LLC|L\.L\.C|Corp|Corporation|Co|Company|Ltd|Limited|L\.?P|LLP|LLLP|PLC|GmbH|"
             r"AG|S\.?A|SAS|S\.?a\.?r\.?l|B\.?V|N\.?V|AB|Pty|ULC|S\.?p\.?A|Oy|A/S|DAC)")

# Legal suffixes after which a comma belongs to the name ('Holdings, LLC'); not 'Company' (Varagon writes
# ', Company <name>').
_LEGAL_PROTECT_RE = (r"(?:Inc|Incorporated|LLC|L\.L\.C|Corp|Corporation|Ltd|Limited|L\.?P|LLP|LLLP|PLC|GmbH|"
                     r"AG|S\.?A|SAS|S\.?a\.?r\.?l|B\.?V|N\.?V|AB|Pty|ULC|S\.?p\.?A|Oy|DAC)")
COUNTRIES = ["united states of america", "united states", "canada", "united kingdom", "germany", "france",
             "netherlands", "luxembourg", "australia", "ireland", "sweden", "spain", "italy", "denmark", "norway",
             "finland", "switzerland", "belgium", "jersey", "cayman islands", "bermuda", "israel", "new zealand",
             "japan", "singapore", "india", "brazil", "mexico", "austria", "poland", "portugal", "guernsey"]

# Labels that start a non-name field inside an identifier.
_FIELD_LABELS = [
    r"Industry", r"Instrument", r"Investment Type", r"InvestmentType", r"Asset Type", r"Type of Investment", r"Facility Type",
    r"Security", r"Interest Rate", r"InterestRate", r"Interest Term", r"Reference Rate", r"ReferenceRate",
    r"Spread Above Index", r"Spread above Index", r"Basis Point Spread", r"Current Coupon", r"All In Rate",
    r"Total Coupon", r"Maturity", r"Due \d", r"Initial Acquisition", r"Original Acquisition", r"Acquisition Date",
    r"Acquisition \d", r"Investment date", r"Original Purchase Date", r"Region", r"Benchmark", r"Ref SOFR",
    r"Rate S\s?\+", r"Rate E\s?\+", r"Rate SOFR", r"Variable Index", r"SOFR Spread", r"EURIBOR Spread",
    r"Index S\+", r"Current election", r"Type ", r"Investment First", r"Investment Senior",
    r"Investment Structured", r"Investment Last", r"Investment Second", r"Acq \d", r"Mat \d", r"Issuer Name",
]
_FIELD_RE = re.compile(r"\b(" + "|".join(_FIELD_LABELS) + r")", re.I)
# Labels that announce the borrower name.
_NAME_LABEL_RE = re.compile(r"^(?:Issuer Name|Company)\s+", re.I)
# Instrument words: a name is cut where these start.
_INSTRUMENT_RE = re.compile(
    r"\b(First[- ]Lien|1st Lien|Second[- ]Lien|2nd Lien|Senior Secured|Senior Sub\w*|Term Loan|Delayed Draw|"
    r"Delayed Term|Revolv\w*|Unitranche|Subordinated|Incremental|DDTL|One stop|Junior|Secured Debt|Secured Loans?|"
    r"Mezzanine|Last[- ]Out|First[- ]Out|Senior Notes|Senior Loan|Term Debt|Initial Term|Closing Date Term|"
    r"Super Senior|Unsecured|Bridge Loan|Secured Note|Common|Preferred|Warrant|Equity|Class [A-Z]\b|"
    r"Debt Investments|Debt investments)", re.I)
_INSTR_WORDS_RE = re.compile(r"\b(lien|loan|debt|revolv|secured|term|facility|notes?|bonds?|unitranche|equity|"
                             r"stock|warrants?|units|shares|investments?|affiliated|issuer|portfolio|clo)\b", re.I)


def clean_identifier(s):
    """Normalize spacing and remove numbers that change every quarter (percent of net assets)."""
    s = str(s).replace("\xa0", " ").replace("Rateand", "Rate and").replace("–", "-").replace("—", "-")
    s = re.sub(r"\s*-?\s*\d+(?:\.\d+)?\s*%\s*(?:of Net Assets)?", " ", s)  # '- 159.5%' etc.
    s = re.sub(r"\s+", " ", s).strip()
    return s


def split_pieces(s):
    """Split an identifier into pieces at '|', ' - ', commas, semicolons and field labels.

    Commas directly followed by a legal suffix ('Holdings, LLC') are kept inside the name.
    Returns a list of (label, text) pairs; label is '' for unlabeled pieces.
    """
    s = re.sub(r",\s*(?=" + _LEGAL_PROTECT_RE + r"\b)", " ", s)
    s = re.sub(r"\([^()]*\)", " ", s)                    # parentheticals: dba, fka, country, footnotes
    parts = re.split(r"\s*\|\s*|\s+-\s+|,\s*|;\s*", s)
    out = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        pos = [m.start() for m in _FIELD_RE.finditer(p)]
        if not pos or pos[0] > 0:
            pos = [0] + pos
        for a, b in zip(pos, pos[1:] + [len(p)]):
            chunk = p[a:b].strip()
            m = _FIELD_RE.match(chunk)
            label = m.group(1).strip().lower() if m else ""
            text = chunk[m.end():].strip() if m else chunk
            if text:
                out.append((label, text))
    return out


_FOOTNOTE_TAIL = re.compile(r"(\s+(\d{1,2}|one|two|three|four|five|six|seven|eight|nine|ten))+$", re.I)


def name_key(name):
    """Normalized borrower key: lowercase, no punctuation, no legal suffixes, no footnote markers."""
    if not isinstance(name, str):
        return ""
    s = re.split(r"\b(?:dba|d/b/a|fka|f/k/a|aka|a/k/a|formerly)\b", name, flags=re.I)[0]
    s = re.sub(r"\([^()]*\)", " ", s)
    s = s.replace("&", " and ").lower()
    s = re.sub(r"\b(l\.l\.c|s\.a\.r\.l|s\.à r\.l|l\.p|b\.v|n\.v|s\.a)\b\.?", " ", s)
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    s = _FOOTNOTE_TAIL.sub("", s)
    words = s.split()
    while words and words[-1] in LEGAL_WORDS:
        words.pop()
    while words and words[0] == "the":
        words.pop(0)
    return " ".join(words)


def learn_prefixes(pieces_by_row, min_continuations=5, min_share=0.01):
    """Learn word prefixes that are category labels in one BDC's identifiers.

    A prefix (first k words of a piece) is treated as a label (e.g. '... Secured Debt Software') when it is
    followed by at least `min_continuations` different words and starts at least `min_share` of the pieces.
    A borrower name is followed by one or two different words only, so it is not removed.
    """
    cont = defaultdict(set)
    count = defaultdict(int)
    n = 0
    for pieces in pieces_by_row:
        for label, text in pieces:
            if label:
                continue
            w = text.lower().split()
            n += 1
            for k in range(1, min(len(w), 12)):
                if re.fullmatch(r"\d{1,2}|one|two|three|four|five|six|seven|eight|nine|ten", w[k]):
                    continue          # footnote numbers after a name are not different continuations
                cont[tuple(w[:k])].add(w[k])
                count[tuple(w[:k])] += 1
    return {p for p, s in cont.items() if len(s) >= min_continuations and count[p] >= max(10, min_share * n)}


def strip_prefix(text, prefixes):
    """Remove the longest learned label prefix from the start of a piece."""
    w = text.split()
    low = [x.lower() for x in w]
    best = 0
    for k in range(1, min(len(w), 12)):
        if tuple(low[:k]) in prefixes:
            best = k
    return " ".join(w[best:])


def _cut_instrument(t):
    m = _INSTRUMENT_RE.search(t)
    if m and m.start() > 0:
        t = t[:m.start()]
    return t.strip(" ,-:/")


def _vocab_word(x):
    """Word form used to compare text with industry labels: lowercase letters, '&' and ':'; 'and' counts as '&'."""
    x = re.sub(r"[^a-z0-9&:]", "", x.lower())
    return "&" if x == "and" else x


def strip_vocab(text, vocab, max_words=7):
    """Remove leading industry labels (from a vocabulary of known labels), up to two times."""
    for _ in range(2):
        w = text.split()
        low = [_vocab_word(x) for x in w]
        best = 0
        for k in range(1, min(len(w), max_words + 1)):
            if " ".join(low[:k]) in vocab and k < len(w):
                best = k
        if best == 0:
            break
        text = " ".join(w[best:])
    return re.sub(r"^(?:and|&)\s+", "", text)


def strip_vocab_tail(text, vocab, max_words=7):
    """Remove a trailing industry label (e.g. 'Acuity Specialty Products, Inc. Chemicals')."""
    w = text.split()
    low = [_vocab_word(x) for x in w]
    best = 0
    for k in range(1, min(len(w), max_words + 1)):
        if " ".join(low[-k:]) in vocab and k < len(w):
            best = k
    return " ".join(w[:len(w) - best]) if best else text


_LEAD_JUNK = re.compile(r"^(?:(?:debt|loans?|investments?|secured|senior|lien|first|1st|/|-|:|and|bank|s)\b\s*|inv\. in ncna port comp \w+\s*)+", re.I)


def _sub_pieces(t, vocab):
    """Split a piece at instrument phrases and clean each part (leading junk words, industry, country)."""
    out = []
    for sub in _INSTRUMENT_RE.split(t)[::2]:          # even positions: text between instrument phrases
        sub = _LEAD_JUNK.sub("", sub.strip(" ,-:/")).strip(" ,-:/")
        sub = strip_vocab_tail(strip_vocab(sub, vocab), vocab).strip(" ,-:/")
        if sub:
            out.append(sub)
    return out


# Category headers of a schedule of investments, never a borrower name.
_CATEGORY_RE = re.compile(r"\bnon-?control\w*(?:/non-?affiliat\w*)?(?: investments?)?|\bnon-?affiliat\w*(?: investments?)?|"
                          r"portfolio compan\w*|portfolio investments|\b(?:debt|equity) investments|"
                          r"^investments\b|^total\b.*|^other assets.*|bank loans:?", re.I)


def pick_borrower(pieces, prefixes, boiler, vocab=frozenset()):
    """Choose the borrower name among the pieces of one identifier.

    Order of preference: a piece announced by a name label (Issuer Name, Company); else the first unlabeled,
    non-boilerplate piece that contains a legal suffix; else the first unlabeled piece that does not look like
    an instrument description. Leading category or industry labels and trailing instrument words are cut off.
    """
    cands = []
    for label, text in pieces:
        if label == "issuer name":
            return _cut_instrument(text)
        if label:
            continue
        m = _NAME_LABEL_RE.match(text)
        if m:
            return _cut_instrument(text[m.end():])
        if text.lower() in boiler:
            continue
        last = None
        for last in _CATEGORY_RE.finditer(text):
            pass
        if last is not None:                       # drop a category header in front of the name
            text = text[last.end():].strip(" :,-")
        # industry labels are removed before and after the learned category prefixes, so that a prefix cannot cut
        # an industry label in two ('Consumer | Services Regis ...')
        for t in _sub_pieces(strip_vocab(strip_prefix(strip_vocab(text, vocab), prefixes), vocab), vocab):
            if t.lower() not in boiler:
                cands.append(t)
    cands = [t for t in cands if re.search(r"[A-Za-z]{3,}", t)]   # a name needs a real word, not '6' or '5.000'
    for t in cands:
        if re.search(r"\b" + _LEGAL_RE + r"\b", t):
            return t
    for t in cands:
        if not _INSTR_WORDS_RE.search(t):
            return t
    return cands[0] if cands else ""


GENERIC_NAME_WORDS = {"holdings", "holding", "holdco", "parent", "buyer", "group", "brands", "intermediate",
                      "acquisition", "acquisitions", "purchaser", "borrower", "midco", "topco", "bidco", "newco",
                      "services", "partners", "company", "companies", "capital", "finance", "financing", "lux"}


def refine_borrowers(names, ciks, min_dup_share=0.10):
    """Second pass over parsed names (all BDCs together), removing display names glued in front of a name.

    1. An immediately repeated first part is dropped ('Gaia Gaia Purchaser Inc' -> 'Gaia Purchaser Inc').
    2. A single capital letter glued to the first word is dropped when the rest is a name another BDC uses
       ('VWhite Cap Buyer LLC' -> 'White Cap Buyer LLC'; the letter comes from the XBRL member name).
    3. For BDCs that write 'display name + legal name' (at least `min_dup_share` of their names show rule 1),
       leading words are dropped when the remaining legal name is used by another BDC and contains a distinctive
       word, i.e. one used in at most 20 different borrower names ('Sterling Pharm Saffron Bidco Ltd' ->
       'Saffron Bidco Ltd', but not 'Carbon6 Technologies Inc.' -> 'Technologies Inc.'). No cut next to 'of', 'and'.
    Returns (refined names, rule applied per name: '', 'repeat', 'glued_letter' or 'display_name').
    """
    names = list(names)
    ciks = list(ciks)
    known = defaultdict(set)
    for n, c in zip(names, ciks):
        k = name_key(n)
        if k:
            known[k].add(c)

    def repeat_cut(n):
        w = n.split()
        for m in range(1, len(w) // 2 + 1):
            if [x.lower() for x in w[:m]] == [x.lower() for x in w[m:2 * m]]:
                return " ".join(w[m:])
        return None

    def used_elsewhere(k, c):
        return bool(k) and len(known.get(k, set()) - {c}) > 0

    # a word used in more than 20 different borrower names ('technologies', 'health') is not distinctive
    word_use = Counter(t for k in known for t in set(k.split()))
    generic = GENERIC_NAME_WORDS | {t for t, c in word_use.items() if c > 20}
    rep = [repeat_cut(n) is not None for n in names]
    dup_share = pd.Series(rep).groupby(pd.Series(ciks)).mean()
    display_bdcs = set(dup_share[dup_share >= min_dup_share].index)
    out, how = [], []
    for n, c in zip(names, ciks):
        r = repeat_cut(n)
        if r:
            out.append(r)
            how.append("repeat")
            continue
        if re.match(r"^[A-Z](?=[A-Z][a-z]{2,})", n) and used_elsewhere(name_key(n[1:]), c) \
                and not used_elsewhere(name_key(n), c):
            out.append(n[1:])
            how.append("glued_letter")
            continue
        if re.match(r"^I (?=[A-Z])", n) and used_elsewhere(name_key(n[2:]), c) \
                and not used_elsewhere(name_key(n), c):
            out.append(n[2:])                       # Goldman's stray 'I ' marker ('I AQ Sunshine, Inc.')
            how.append("glued_letter")
            continue
        new = n
        if c in display_bdcs and not used_elsewhere(name_key(n), c):
            w = n.split()
            for k in range(1, len(w)):
                cand = " ".join(w[k:])
                ck = name_key(cand)
                distinctive = [t for t in ck.split() if len(t) >= 3 and t not in generic]
                if {w[k].lower(), w[k - 1].lower()} & {"of", "and", "&", "the", "for", "de", "la", "/"}:
                    continue                       # never cut inside a name ('TravelCenters of America')
                if distinctive and used_elsewhere(ck, c):
                    new = cand
                    break
        out.append(new)
        how.append("display_name" if new != n else "")
    return out, how


def industry_vocabulary(identifiers, min_count=3):
    """Set of industry labels written as 'Industry X' anywhere in the data (lowercase, letters only).

    Used to strip industry words that some managers write directly in front of the borrower name.
    """
    norm = lambda x: " ".join(_vocab_word(w) for w in x.split())  # noqa: E731
    lab = identifiers.dropna().map(industry_from_label).dropna().map(norm)
    vc = lab.value_counts()
    std = []
    for label in STANDARD_INDUSTRIES:          # whole label and its comma-separated parts (we split at commas)
        std.append(norm(label))
        std += [norm(p) for p in label.split(",") if p.strip()]
    return frozenset(vc[vc >= min_count].index) | frozenset(COUNTRIES) | frozenset(std)


# Standard industry lists used by many BDCs: Moody's 35 industries and GICS industries.
STANDARD_INDUSTRIES = [
    "Aerospace & Defense", "Automotive", "Banking, Finance, Insurance & Real Estate", "Beverage, Food & Tobacco",
    "Capital Equipment", "Chemicals, Plastics & Rubber", "Construction & Building", "Consumer Goods: Durable",
    "Consumer Goods: Non-Durable", "Consumer Goods: Non-durable", "Containers, Packaging & Glass",
    "Energy: Electricity", "Energy: Oil & Gas", "Environmental Industries", "Forest Products & Paper",
    "Healthcare & Pharmaceuticals", "High Tech Industries", "Hotel, Gaming & Leisure",
    "Media: Advertising, Printing & Publishing", "Media: Broadcasting & Subscription",
    "Media: Diversified & Production", "Metals & Mining", "Retail", "Services: Business", "Services: Consumer",
    "Sovereign & Public Finance", "Telecommunications", "Transportation: Cargo", "Transportation: Consumer",
    "Utilities: Electric", "Utilities: Oil & Gas", "Utilities: Water", "Wholesale",
    "Energy Equipment & Services", "Oil, Gas & Consumable Fuels", "Chemicals", "Construction Materials",
    "Containers & Packaging", "Paper & Forest Products", "Building Products", "Construction & Engineering",
    "Electrical Equipment", "Industrial Conglomerates", "Machinery", "Trading Companies & Distributors",
    "Commercial Services & Supplies", "Professional Services", "Air Freight & Logistics", "Airlines",
    "Marine Transportation", "Ground Transportation", "Road & Rail", "Transportation Infrastructure",
    "Automobile Components", "Auto Components", "Automobiles", "Household Durables", "Leisure Products",
    "Textiles, Apparel & Luxury Goods", "Hotels, Restaurants & Leisure", "Diversified Consumer Services",
    "Distributors", "Broadline Retail", "Internet & Direct Marketing Retail", "Specialty Retail",
    "Consumer Staples Distribution & Retail", "Food & Staples Retailing", "Beverages", "Food Products", "Tobacco",
    "Household Products", "Personal Care Products", "Personal Products", "Health Care Equipment & Supplies",
    "Health Care Providers & Services", "Health Care Technology", "Biotechnology", "Pharmaceuticals",
    "Life Sciences Tools & Services", "Banks", "Financial Services", "Diversified Financial Services",
    "Consumer Finance", "Capital Markets", "Mortgage Real Estate Investment Trusts", "Insurance", "IT Services",
    "Software", "Communications Equipment", "Technology Hardware, Storage & Peripherals",
    "Electronic Equipment, Instruments & Components", "Semiconductors & Semiconductor Equipment",
    "Diversified Telecommunication Services", "Wireless Telecommunication Services", "Media", "Entertainment",
    "Interactive Media & Services", "Electric Utilities", "Gas Utilities", "Multi-Utilities", "Water Utilities",
    "Independent Power and Renewable Electricity Producers", "Real Estate Management & Development",
    "Health Care", "Healthcare", "Business Services", "Consumer Services", "Consumer Products", "Industrials",
    "Information Technology", "Technology", "Education", "Food & Beverage", "Healthcare Services",
    "Oil & Gas Storage & Transportation", "Oil & Gas Equipment & Services", "Oil & Gas Exploration & Production",
]


def parse_borrowers(df, id_col="identifier", bdc_col="cik", vocab=None):
    """Return a Series with the borrower name parsed from each identifier.

    Prefix labels and boilerplate pieces are learned separately for each BDC, because each BDC
    uses its own identifier format. `vocab` is a set of known industry labels (industry_vocabulary).
    """
    if vocab is None:
        vocab = industry_vocabulary(df[id_col])
    out = pd.Series("", index=df.index, dtype=object)
    for _, g in df.groupby(bdc_col):
        pieces = g[id_col].fillna("").map(clean_identifier).map(split_pieces)
        prefixes = learn_prefixes(pieces)
        # boilerplate pieces: identical unlabeled pieces that occur in many rows (>= 3% and >= 20 rows)
        cnt = Counter(t.lower() for ps in pieces for lab, t in ps if not lab)
        lim = max(20, 0.03 * len(g))
        boiler = {t for t, c in cnt.items() if c >= lim}
        out.loc[g.index] = [pick_borrower(ps, prefixes, boiler, vocab) for ps in pieces]
    return out


# ---------------------------------------------------------------------------
# Matching a borrower against earlier holdings (robust to rewording of identifiers)
# ---------------------------------------------------------------------------
_TOKEN_RE = re.compile(r"[a-z][a-z0-9]+|\d+[a-z][a-z0-9]*")


def ordered_tokens(text):
    """Word tokens in the order they appear (for rules that need the first word of a name)."""
    if not isinstance(text, str):
        return []
    return _TOKEN_RE.findall(text.lower().replace("&", " "))


def tokens(text):
    """Set of lowercase word tokens (letters, or digits followed by letters); pure numbers are dropped."""
    if not isinstance(text, str):
        return frozenset()
    t = text.lower().replace("&", " and ")
    return frozenset(_TOKEN_RE.findall(t))


class HoldingsIndex:
    """Inverted index of all holdings: token -> rows, to ask 'was this borrower held before, and by whom?'.

    A borrower counts as present in an earlier identifier when the distinctive words of its name (words found in
    at most 0.1% of all identifiers), weighted by how rare each word is (inverse document frequency), are covered
    by that identifier to at least `threshold`. Common words ('Holdings', 'Buyer', industry words) are ignored, so
    a manager rewording its identifiers or writing the industry in front of the name does not break the match.
    """

    def __init__(self, holdings, threshold=0.8, common_share=0.001):
        self.q = holdings["q_int"].to_numpy()
        self.fam = holdings["family"].to_numpy()
        self.cik = holdings["cik"].to_numpy()
        # Memory: an identifier repeats every quarter, so equal identifiers share one token set, and equal words share
        # one string object. The sets and their contents are the same as tokens(x) of each row.
        set_of, word_of, self.tok = {}, {}, []
        for x in holdings["identifier"].fillna("").map(clean_identifier):
            ts = set_of.get(x)
            if ts is None:
                ts = set_of[x] = frozenset(word_of.setdefault(t, t) for t in tokens(x))
            self.tok.append(ts)
        del set_of, word_of
        n = len(self.tok)
        df_ = Counter(t for ts in self.tok for t in ts)
        self.idf = {t: np.log(n / c) for t, c in df_.items()}
        self.max_idf = np.log(n)
        self.index = defaultdict(list)
        for i, ts in enumerate(self.tok):
            for t in ts:
                self.index[t].append(i)
        self.index = {t: np.array(v) for t, v in self.index.items()}
        self.threshold = threshold
        self.common = {t for t, c in df_.items() if c > common_share * n}   # words in > 0.1% of identifiers

    def key_tokens(self, key):
        """Distinctive words of a borrower name; if the name has none, all its words.

        Words of one or two letters ('by', 'of') are ignored unless the name has nothing else ('2U Inc.').
        """
        all_kt = [t for t in tokens(key) if t not in LEGAL_WORDS]
        kt = [t for t in all_kt if len(t) > 2] or all_kt
        dist = [t for t in kt if t not in self.common]
        return dist if dist else kt

    def matches(self, key):
        """Row numbers of holdings whose identifier contains the borrower `key` (weighted coverage rule)."""
        kt = self.key_tokens(key)
        if not kt:
            return np.array([], dtype=int)
        w = {t: self.idf.get(t, self.max_idf) for t in kt}
        rare = max(kt, key=lambda t: w[t])
        if rare not in self.index:
            return np.array([], dtype=int)
        cand = self.index[rare]
        total = sum(w.values())
        keep = [i for i in cand if sum(w[t] for t in kt if t in self.tok[i]) / total >= self.threshold]
        return np.array(keep, dtype=int)


# --- loan characteristics from the identifier --------------------------------------------------------
def instrument_type(s):
    """Classify the instrument from identifier text: revolver, delayed_draw, term_loan or unknown."""
    t = str(s).lower()
    if re.search(r"revolv|\brc\b|\brcf\b|line of credit|\bloc\b", t):
        return "revolver"
    if re.search(r"delay(?:ed)?[- ]?draw|delayed term|\bddtl\b|\bdd tl\b|\bdd term|\bdelayed\b", t):
        return "delayed_draw"
    if re.search(r"term loan|\btl\b|term debt|unitranche|one stop|senior secured loan|first[- ]lien loan|"
                 r"secured loan|first lien debt|1st lien|first lien|senior loan|bank debt|senior secured", t):
        return "term_loan"
    return "unknown"


def is_structured(s):
    """True for structured products (CLO tranches, asset-backed notes): not loans to an operating company."""
    return bool(re.search(r"\bCLO\b|structured (?:note|credit|product|finance)|collateralized loan|asset[- ]backed|"
                          r"\bABS\b|mezzanine debt - class|\bclass [a-f]-?\d? notes?\b", str(s), re.I))


def lien_type(s):
    """first_lien (incl. unitranche, one stop, senior secured), first_lien_last_out, second_lien_or_junior, unknown."""
    t = str(s).lower()
    if re.search(r"second[- ]lien|2nd lien|junior|subordinated|mezzanine|unsecured", t):
        return "second_lien_or_junior"
    if re.search(r"last[- ]out", t):
        return "first_lien_last_out"
    if re.search(r"first[- ]lien|1st lien|unitranche|one stop|senior secured|first[- ]out|senior loan|bank debt|"
                 r"secured loan|secured debt", t):
        return "first_lien"
    return "unknown"


def base_rate(ident, rate_enum):
    """Base rate of a floating-rate line: SOFR, LIBOR, PRIME, NON_USD (EURIBOR, SONIA, ...) or UNKNOWN."""
    t = str(ident)
    e = str(rate_enum).lower()
    if re.search(r"EURIBOR|SONIA|BBSY|BBSW|CDOR|CORRA|SARON|STIBOR|NIBOR|TIBOR|BKBM|CIBOR|ESTR|€|£|"
                 r"\b(?:E|EUR|SN|GBP|C|CAD|A|AUD|B|N|NOK|SEK|DKK|CHF|NZD|SA|SON)\s?\+\s?\d|"
                 r"\b(?:EUR|GBP|CAD|AUD|SEK|NOK|DKK|CHF|NZD)\b", t) or re.search(
            r"euro|sonia|sterling|canad|bbsy|bankbill|bank bill|cdor|corra|stibor|nibor|saron|tibor|bkbm|cibor|"
            r"australia|kingdom", e):
        return "NON_USD"
    if re.search(r"\bPrime\b|\bP\s?\+\s?\d|\bPRIME\b", t) or "prime" in e:
        return "PRIME"
    if re.search(r"LIBOR|\bL\s?\+\s?\d", t) or "libor" in e or "londoninterbank" in e:
        return "LIBOR"
    if re.search(r"SOFR|\bS\s?\+|Index S\+", t) or "sofr" in e or "securedovernight" in e:
        return "SOFR"
    return "UNKNOWN"


_DATE = r"(\d{1,2}/\d{1,2}/\d{2,4}|\d{1,2}/\d{4}|\d{1,2}/\d{2}\b)"


def _to_date(x):
    if not isinstance(x, str):
        return pd.NaT
    parts = x.split("/")
    try:
        if len(parts) == 3:
            m, d, y = int(parts[0]), int(parts[1]), int(parts[2])
        else:
            m, d, y = int(parts[0]), 1, int(parts[1])
        if y < 100:
            y += 2000
        if not 1990 <= y <= 2035:
            return pd.NaT
        return pd.Timestamp(year=y, month=m, day=d)
    except (ValueError, TypeError):
        return pd.NaT


def acquisition_date(s):
    """Acquisition (investment) date written in the identifier, if any (month precision is enough for us)."""
    m = re.search(r"(?:Initial |Original )?(?:Acquisition|Investment|Purchase)(?: Date| date)?\s*[-:]?\s*" + _DATE,
                  str(s))
    return _to_date(m.group(1)) if m else pd.NaT


def maturity_from_text(s):
    """Maturity date written in the identifier (Maturity / Due / MD / last date in a pipe list)."""
    t = str(s)
    m = re.search(r"(?:Maturity(?:/ ?Dissolution)?(?: Date| date)?|Due|\bMD\b|M D)\s*[|:\-]?\s*" + _DATE, t)
    if m:
        return _to_date(m.group(1))
    m = re.search(r"\|\s*" + _DATE + r"\s*$", t)  # pipe format: maturity is the last field
    return _to_date(m.group(1)) if m else pd.NaT


def floor_from_text(s):
    """Interest rate floor in percent written in the identifier ('1.00% Floor', 'Floor 0.75%', '(100 Floor)')."""
    t = str(s)
    m = re.search(r"(\d+(?:\.\d+)?)\s*%\s*(?:SOFR\s+)?Floor", t, re.I) or re.search(
        r"Floor(?: rate)?\s*\(?(\d+(?:\.\d+)?)\s*%", t, re.I)
    if m:
        return float(m.group(1))
    m = re.search(r"\(?\b(\d{2,3})\s+Floor\)?", t)  # written in basis points
    return float(m.group(1)) / 100 if m else np.nan


def pik_in_text(s):
    """True if the identifier mentions a PIK component that is not explicitly zero."""
    t = str(s)
    if not re.search(r"\bPIK\b", t, re.I):
        return False
    return not re.search(r"PIK\s*0(?:\.0+)?%|0\.00%\s*PIK", t, re.I)


def industry_from_label(s):
    """Industry written after the word 'Industry', up to the next field label."""
    m = re.search(r"\bIndustry\s+(.+)", clean_identifier(s))
    if not m:
        return None
    rest = m.group(1)
    stop = re.search(r"\s(?:Interest Rate|InterestRate|Reference Rate|ReferenceRate|Current Coupon|Security|"
                     r"Instrument|Investment Type|Type of Investment|Company|Rate\s|Spread|Acquisition|Maturity|"
                     r"Asset Type|Interest Term|Investment|Initial|Original|Basis Point)\b|,|\|", rest)
    out = (rest[:stop.start()] if stop else rest).strip(" ,-")
    return out or None


def family_vocabulary(labels, min_count=2):
    """Industry labels used by one manager family (from its 'Industry X' fields), longest first."""
    vc = labels.dropna().map(lambda x: re.sub(r"\s+", " ", x).strip()).value_counts()
    return sorted(vc[vc >= min_count].index, key=len, reverse=True)


def industry_for(identifier, vocab):
    """Industry of a line: the 'Industry X' label if written, else the longest family label found in the text."""
    lab = industry_from_label(identifier)
    if lab:
        return lab
    text = " " + clean_identifier(identifier).lower() + " "
    for v in vocab:                      # vocab is sorted longest first
        if re.search(r"[\s|,]" + re.escape(v.lower()) + r"[\s|,]", text):
            return v
    return None


# ---------------------------------------------------------------------------
# Industry label -> sector (11 GICS-style sectors). First matching rule wins, so the order matters
# (e.g. 'Health Care Technology' is Health Care, not Information Technology).
# ---------------------------------------------------------------------------
SECTOR_RULES = [
    ("Information Technology", r"it ?consult|^it services"),
    ("Health Care", r"health|pharma|biotech|life science|medical|dental|hospital|veterinar|clinic|drug|"
                    r"physician|behavioral|laborator"),
    ("Real Estate", r"real estate|reit\b"),
    ("Financials", r"financ|insurance|bank|capital markets|asset manag|mortgage|lending|brokerage|wealth|"
                   r"payment|investment vehicle|thrift|credit"),
    ("Utilities", r"utilit|electric power|power generation|renewable|water utilit|independent power|gas utilit"),
    ("Energy", r"energy|oil|gas\b|fuel|petroleum|pipeline"),
    ("Communication Services", r"media|entertainment|telecom|broadcast|publishing|advertis|wireless|interactive|"
                               r"cable|communication|marketing services|movies|music|games"),
    ("Information Technology", r"software|it services|information technology|technolog|internet|semiconductor|"
                               r"electronic|computer|data processing|high tech|digital|cyber|saas|tech\b|"
                               r"hardware|communications equipment"),
    ("Consumer Staples", r"food|beverage|staples|personal (care )?products|personal and non|household products|"
                         r"tobacco|grocer|non-?durable|agricultur|drug retail|beauty"),
    ("Materials", r"chemical|material|container|packag|metal|mining|paper|forest|plastic|glass|steel|rubber"),
    ("Consumer Discretionary", r"consumer|retail|hotel|restaurant|leisure|automo|auto |auto$|household durable|"
                               r"textile|apparel|education|franchis|homebuild|durable|luxury|fitness|recreation|"
                               r"specialty retail|distributors|pet\b|sports|gaming|travel|car wash|home"),
    ("Industrials", r"aerospace|defense|building|construction|commercial|professional|machinery|electrical|"
                    r"industrial|trading compan|transport|freight|logistic|road|rail|airline|marine|environment|"
                    r"capital goods|business services|services: business|security|engineering|staffing|"
                    r"manufactur|equipment|waste|distribution|government|cargo|wholesale|infrastructure|"
                    r"diversified support|office|printing|component|tools|consult|services:? business|conglomerate|"
                    r"event|human resource|employment"),
]


def sector_of(industry):
    """Map a raw industry label to one of 11 GICS-style sectors ('Other' if no rule matches)."""
    if not isinstance(industry, str) or not industry.strip():
        return None
    t = industry.lower()
    for sector, pat in SECTOR_RULES:
        if re.search(pat, t):
            return sector
    return "Other"


# ---------------------------------------------------------------------------
# Industry for any BDC: label, tagged field, or a standard industry name in the text
# ---------------------------------------------------------------------------
def industry_from_tag(axis, enum):
    """Industry from the tagged XBRL fields (axis member text or extensible enumeration URL)."""
    for v in (axis, enum):
        if isinstance(v, str) and v.strip():
            t = v.split("#")[-1]
            t = re.sub(r"(Sector)?Member$", "", t.replace(" Member", "")).strip()
            t = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", t)            # CamelCase -> words
            if t and not re.search(r"\d{3,}", t):
                return t
    return None


class IndustryFinder:
    """Find a known industry label in identifier text (longest match that is not part of the borrower name)."""

    def __init__(self, extra_labels=()):
        labels = {re.sub(r"\s+", " ", x).strip() for x in list(STANDARD_INDUSTRIES) + list(extra_labels)}
        labels = sorted((x for x in labels if 3 <= len(x) <= 60 and not re.search(r"\d|%", x)), key=len, reverse=True)
        self.labels = labels
        self.regex = re.compile(r"(?<![A-Za-z])(" + "|".join(re.escape(x) for x in labels) + r")(?![A-Za-z])", re.I)

    def find(self, identifier, borrower=""):
        text = clean_identifier(identifier)
        b = (borrower or "").lower()
        best = None
        for m in self.regex.finditer(text):
            lab = m.group(1)
            if b and lab.lower() in b:
                continue
            if best is None or len(lab) > len(best):
                best = lab
        return best


def industry_any(identifier, axis, enum, borrower, finder):
    """Industry of a loan line: 'Industry X' label, else tagged field, else a known label found in the text."""
    return industry_from_label(identifier) or industry_from_tag(axis, enum) or finder.find(identifier, borrower)


def wilson_ci(k, n, z=1.96):
    """95% Wilson confidence interval for a share k/n (better than the normal approximation for small n)."""
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    den = 1 + z ** 2 / n
    centre = (p + z ** 2 / (2 * n)) / den
    half = z * np.sqrt(p * (1 - p) / n + z ** 2 / (4 * n ** 2)) / den
    return (centre - half, centre + half)


# ---------------------------------------------------------------------------
# Hand check: text of a filing around a borrower name
# ---------------------------------------------------------------------------
def filing_snippets(url, name, user_agent, width=700, max_hits=3):
    """Download a filing from EDGAR and return text snippets around the first word(s) of a borrower name.

    Used for the hand check of loans against the original 10-Q / 10-K (results in docs/hand_check.csv).
    """
    import html as _html
    url = url.replace("/ix?doc=", "")          # the inline-XBRL viewer link -> the document itself
    r = requests.get(url, headers={"User-Agent": user_agent}, timeout=120)
    r.raise_for_status()
    text = re.sub(r"<[^>]+>", " ", r.text)
    text = _html.unescape(text).replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    words = [w for w in re.findall(r"[A-Za-z0-9&'.-]+", name) if w.lower() not in LEGAL_WORDS][:2]
    pat = re.compile(r"\W+".join(re.escape(w) for w in words), re.I)
    out = [text[max(0, m.start() - 100): m.start() + width] for m in pat.finditer(text)]
    time.sleep(0.3)
    return out[:max_hits], len(out)


# ---------------------------------------------------------------------------
# Display names (work order 5): cosmetic clean-up of the `borrower` column only
# ---------------------------------------------------------------------------
_TRAILING_JUNK = re.compile(r"\s+(?:(?:Ma\w{0,3}rity|Maturity|Acquisitions?|Acquisition Date)\s+\d{1,2}/\d{1,2}/\d{2,4}"
                            r"|Rate and Spread|Reference Rate|Amendment No\.?\s*\d|Cov-Lite\b"
                            r"|(?:Tranche|Term)\s+[A-Z0-9]{1,2}\s+Loan\b).*$", re.I)
_LEADING_JUNK = re.compile(r"^United S\w*tes of America\s+(?=\S+\s+\S)", re.I)    # not "United States Steel"
_LINE_END = re.compile(r"\s*(?:,\s*)?(?:First Lien|1st Lien|Second Lien|2nd Lien|Senior Secured|Senior Loan|"
                       r"Term Loan|Unitranche)\b", re.I)


def _norm_token(t):
    return re.sub(r"[^a-z0-9]", "", t.lower())


def _similar(a, b):
    from difflib import SequenceMatcher
    return a == b or (min(len(a), len(b)) >= 6 and SequenceMatcher(None, a, b).ratio() >= 0.85)


def display_name(name, identifier="", known_names=()):
    """Readable borrower name for the `borrower` column. Never used for matching (that uses `borrower_key`).

    Rules, in order: (1) the name written twice without a space ("F&M Buyer LLCF&M Buyer LLC"); (2) trailing maturity,
    acquisition-date, rate, amendment or "Cov-Lite" text ("CFP Holdings LLC Matrity 09/13/2030"), and a glued
    fragment ("enior Senior Support ..."); (3) a display name in front of the legal name, recognised because the first
    word comes back within the next five words ("SEER GS SEER Group Borrower LLC", "GTreasury G Treasury SS LLC"; not
    for names joining two entities with "and", "&" or "/"); (4) a leading code whose remainder is another borrower's name ("G2CI Evergreen IX
    Borrower 2023 LLC"); (5) a name cut at "&" or an HTML "amp;", completed from the identifier.
    """
    s = str(name).strip()
    ident = str(identifier).replace("amp;", "&")
    compact = s.replace(" ", "")
    half = len(compact) // 2
    if len(compact) % 2 == 0 and half >= 6 and compact[:half] == compact[half:]:
        cut, n = 0, 0                                  # rule 1: keep the first copy with its spaces
        while n < half:
            n += s[cut] != " "
            cut += 1
        s = s[:cut].strip()
    s = _TRAILING_JUNK.sub("", s).strip(" ,")                                          # rule 2
    s = _LEADING_JUNK.sub("", s)                       # misspelled country in front ("United Sates of America X")
    m = re.match(r"([a-z]{3,})([A-Z][a-z]+)\b", s)                 # glued fragment: "eniorSenior" -> "Senior"
    if m and m.group(2).lower().endswith(m.group(1)):
        s = s[len(m.group(1)):]
    toks = s.split()
    if len(toks) >= 2 and len(toks[0]) >= 4 and toks[0].islower() and toks[1].lower().endswith(toks[0]):
        s = " ".join(toks[1:])                                     # "enior Senior Support" -> "Senior Support"
    toks = s.split()
    two_entities = "/" in s or re.search(r"\s(?:and|&)\s", s)       # "A and B": two legal names, keep both
    if not two_entities and len(toks) >= 3 and toks[0].lower() not in GENERIC_NAME_WORDS:  # rule 3
        first = _norm_token(toks[0])
        for k in range(1, min(6, len(toks) - 1)):
            cand = [_norm_token(toks[k]), _norm_token(toks[k]) + _norm_token(toks[k + 1])]
            if first and any(_similar(first, c) for c in cand):
                start = k - 1 if toks[k - 1].lower() == "the" else k
                s = " ".join(toks[start:])
                break
    toks = s.split()
    if (len(toks) >= 3 and re.fullmatch(r"[A-Z0-9]*\d[A-Z0-9]*", toks[0]) and re.search(r"[A-Z]", toks[0])
            and " ".join(toks[1:]) in known_names):                                    # rule 4
        s = " ".join(toks[1:])
    if s.endswith("&") or s.lower() == "amp" or "amp;" in str(identifier):            # rule 5
        stem = s.rstrip("& ").strip()
        stem = "" if stem.lower() == "amp" else stem
        pos = ident.find(stem) if stem else 0
        if pos < 0 or (pos < 20 and not re.search(r"[,|]| - ", ident[:pos])):
            pos = 0                                   # the name starts the identifier ("Name, First Lien ...")
        if pos >= 0:
            rest = ident[pos:]
            m = _LINE_END.search(rest)
            full = (rest[:m.start()] if m else rest).strip(" ,")
            if full.count(",") >= 3:                          # comma-separated list: the first field only
                full = full.split(",")[0].strip()
            fields = [f.strip() for f in ident.split(",")]
            if full in fields and fields.index(full) + 1 < len(fields):
                nxt = fields[fields.index(full) + 1]
                if not re.match(r"(?i)region|reference|interest|maturity|acquisition", nxt):
                    full = nxt                                  # "industry, name, ..." layout (First Eagle)
            if full:
                s = full
    return s


# ---------------------------------------------------------------------------
# Spelling variants of a borrower within a family (release checker, work order 5)
# ---------------------------------------------------------------------------
def compact_key(key, keep_generic=False):
    """Borrower key without legal (and, by default, generic) words and without spaces ("bar tender llc" ->
    "bartender"); a legal word glued to the last word is removed too ("2xllc" -> "2x")."""
    words = [w for w in str(key).split() if w not in LEGAL_WORDS]
    if words:
        words[-1] = re.sub(r"(?<=\w)(llc|ltd|corp)$", "", words[-1]) or words[-1]     # not "inc": "zinc"
    core = words if keep_generic else ([w for w in words if w not in GENERIC_NAME_WORDS] or words)
    return "".join(core)


def held_as_variant(cand, hold, ratio=0.85, days=60, strong=0.9):
    """True for candidates whose family held a spelling variant of the borrower in an earlier quarter.

    Nets on top of the rarity-weighted matching: (1) the same compact key (spaces, legal and generic words removed:
    "Bar Tender" = "BarTender", "2X LLC" = "2xLLC"; or with generic words kept: "Clear Capital" = "ClearCapital"),
    whatever the maturity; (2) a near-identical compact key (similarity at least `ratio`, same first letter, length
    within 2: "Escalen"/"Escalent", "Indera"/"Idera") with a maturity within `days` days, i.e. the same loan under a
    misspelled name; (3) a long compact key (10 letters or more) with similarity at least `strong`, whatever the
    maturity ("Proneri International"/"Froneri International", "GS Fullsteam Operation"/"Fullsteam Operations");
    (4) an earlier compact key of 8 letters or more at the end of the current one, or the reverse (a brand or display
    prefix: "Clarience Technologies Truck-Lite" / "Truck-Lite", "Convergint DG Investment ..." / "DG Investment ...").
    cand: rows with family, q_int, borrower_key, maturity; hold: rows with family, q_int, borrower_key, maturity.
    """
    from difflib import SequenceMatcher
    h = hold[hold.borrower_key != ""].assign(ck=hold.borrower_key.map(compact_key),
                                             ckg=hold.borrower_key.map(lambda k: compact_key(k, keep_generic=True)))
    h = h[h.ck.str.len() >= 2]
    first_q = h.groupby(["family", "ck"]).q_int.min()
    first_q_g = h.groupby(["family", "ckg"]).q_int.min()       # same, keeping generic words ("Clear Capital")
    by_fam = {f: g for f, g in h.groupby("family")[["ck", "q_int", "maturity"]]}
    grams_by_fam = {}                       # 5-letter pieces of long compact keys, to find near-identical names fast
    for f, k in h.loc[h.ck.str.len() >= 10, ["family", "ck"]].drop_duplicates().itertuples(index=False):
        d = grams_by_fam.setdefault(f, {})
        for i in range(len(k) - 4):
            d.setdefault(k[i:i + 5], set()).add(k)
    long_keys = first_q[first_q.index.get_level_values("ck").str.len() >= 8]
    suffix_by_fam = {f: list(zip(g.index.get_level_values("ck"), g.values)) for f, g in long_keys.groupby(level="family")}
    out = []
    for f, q, k, m in zip(cand.family, cand.q_int, cand.borrower_key, cand.maturity):
        ck, ckg = compact_key(k), compact_key(k, keep_generic=True)
        if len(ck) < 2:
            out.append(False)
            continue
        if first_q.get((f, ck), 10**9) < q or first_q_g.get((f, ckg), 10**9) < q:
            out.append(True)
            continue
        g = by_fam.get(f)
        hit = False
        if g is not None and pd.notna(m):
            g = g[(g.q_int < q) & (g.ck.str[0] == ck[0]) & ((g.ck.str.len() - len(ck)).abs() <= 2) & (g.ck != ck)]
            g = g[(g.maturity - m).abs() <= pd.Timedelta(days=days)]
            for other in g.ck.unique():
                sm = SequenceMatcher(None, ck, other)
                if sm.quick_ratio() >= ratio and sm.ratio() >= ratio:
                    hit = True
                    break
        if not hit and len(ck) >= 10 and f in grams_by_fam:       # (3) long, near-identical name, any maturity
            idx5 = grams_by_fam[f]
            pool = set().union(*(idx5.get(ck[i:i + 5], ()) for i in range(len(ck) - 4)))
            for other in pool:
                if (other != ck and first_q.get((f, other), 10**9) < q and abs(len(other) - len(ck)) <= 3
                        and SequenceMatcher(None, ck, other).ratio() >= strong):
                    hit = True
                    break
        if not hit and f in suffix_by_fam:            # (4) a brand prefix: "Clarience Technologies Truck-Lite"
            for other, q0 in suffix_by_fam[f]:
                if q0 < q and other != ck and (ck.endswith(other) or (len(ck) >= 8 and other.endswith(ck))):
                    hit = True
                    break
        out.append(hit)
    return pd.Series(out, index=cand.index)


def is_industry_label(key, vocab):
    """True when a borrower key is only an industry or country label ("hotels", "aerospace and"), not a name."""
    norm = lambda x: " ".join(w for w in str(x).replace("&", " ").split() if w != "and")  # noqa: E731
    k = norm(key)
    if not k:
        return False
    labels = {norm(v) for v in vocab}
    return any(lab == k or lab.startswith(k + " ") for lab in labels)
