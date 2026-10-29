"""Names are normalized to 'surname|first initial'; papers come from BibTeX or CSV (authors; year)."""
import csv
import re
import unicodedata


def _ascii(s):
    s = re.sub(r"\\[a-zA-Z]+\s*|[{}\\'\"`^~]", "", s)
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c))


def name_key(name):
    """'Silva, Ana M.' / 'Ana M. Silva' / 'A. Silva' -> 'silva|a'. Particles kept: 'van der Berg, J' -> 'vanderberg|j'."""
    n = _ascii(name).strip()
    if not n:
        return ""
    if "," in n:
        last, first = [p.strip() for p in n.split(",", 1)]
    else:
        parts = n.split()
        idx = next((i for i, p in enumerate(parts[:-1]) if p[:1].islower()), len(parts) - 1)
        last, first = " ".join(parts[idx:]), " ".join(parts[:idx])
    last = re.sub(r"[^a-z]", "", last.lower())
    init = re.sub(r"[^a-z]", "", first.lower())[:1]
    return "%s|%s" % (last, init)


def _split_authors(field):
    return [a.strip() for a in re.split(r"\s+and\s+|;", field) if a.strip()]


def load_papers(path):
    """Return list of (year or None, [author names]). BibTeX (.bib) or CSV with 'authors' and 'year' columns."""
    with open(path, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    papers = []
    if path.lower().endswith(".bib"):
        for m in re.finditer(r"@\w+\s*\{[^,]*,(.*?)\n\}", text, re.S):
            body = m.group(1)
            au = re.search(r"author\s*=\s*[{\"](.*?)[}\"]\s*,?\s*\n", body, re.S | re.I)
            yr = re.search(r"year\s*=\s*[{\"]?(\d{4})", body, re.I)
            if au:
                papers.append((int(yr.group(1)) if yr else None, _split_authors(" ".join(au.group(1).split()))))
    else:
        for r in csv.DictReader(text.splitlines()):
            y = (r.get("year") or "").strip()
            papers.append((int(y) if y.isdigit() else None, _split_authors(r.get("authors", ""))))
    return papers


def coauthor_index(papers):
    """{name_key: {coauthor_key: [years]}}"""
    idx = {}
    for year, authors in papers:
        keys = [name_key(a) for a in authors if name_key(a)]
        for a in keys:
            for b in keys:
                if a != b:
                    idx.setdefault(a, {}).setdefault(b, []).append(year)
    return idx


def _norm_inst(s):
    s = _ascii(s).lower()
    s = re.sub(r"\b(the|of|and|for|dept|department|school|faculty|institute|university|universit[aey]|college)\b", " ", s)
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", s).split())


def check_reviewers(authors, reviewers, papers, window=5, current_year=None, author_affils=(), editors_note=True):
    """authors: manuscript author names; reviewers: list of dicts(name, affiliation).
    Returns list of dicts(reviewer, conflicts=[...], severity)."""
    idx = coauthor_index(papers)
    years = [y for y, _ in papers if y]
    current_year = current_year or (max(years) if years else 0)
    akeys = {name_key(a): a for a in authors}
    inst = {_norm_inst(a) for a in author_affils if _norm_inst(a)}
    out = []
    for r in reviewers:
        rk = name_key(r["name"])
        conflicts = []
        if rk in akeys:
            conflicts.append(("author", "reviewer appears to be an author (%s)" % akeys[rk]))
        for ak, aname in akeys.items():
            ys = idx.get(rk, {}).get(ak, [])
            if ys:
                recent = [y for y in ys if y is not None and current_year - y < window]
                if recent:
                    conflicts.append(("coauthor", "co-authored with %s in %s" % (aname, ", ".join(map(str, sorted(set(recent)))))))
                else:
                    conflicts.append(("past-coauthor", "co-authored with %s earlier (%s)" % (
                        aname, ", ".join(str(y) for y in sorted(set(y for y in ys if y)) or ["year unknown"]))))
        ri = _norm_inst(r.get("affiliation", ""))
        if ri and any(ri == i or (len(ri) > 6 and (ri in i or i in ri)) for i in inst):
            conflicts.append(("institution", "same institution as an author (%s)" % r.get("affiliation")))
        shared = set(idx.get(rk, {})) & {k for ak in akeys for k in idx.get(ak, {})} - set(akeys)
        if shared:
            conflicts.append(("network", "%d shared co-author(s) with the authors" % len(shared)))
        sev = "high" if any(c[0] in ("author", "coauthor", "institution") for c in conflicts) else \
            "medium" if conflicts else "none"
        out.append({"reviewer": r["name"], "affiliation": r.get("affiliation", ""), "severity": sev,
                    "conflicts": [m for _, m in conflicts]})
    order = {"high": 0, "medium": 1, "none": 2}
    return sorted(out, key=lambda x: (order[x["severity"]], x["reviewer"]))
