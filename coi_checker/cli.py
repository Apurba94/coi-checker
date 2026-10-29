"""Command-line interface for coi-checker."""
import argparse
import csv
import json

from .core import check_reviewers, load_papers


def main(argv=None):
    ap = argparse.ArgumentParser(prog="coi-checker", description="Screen candidate reviewers for conflicts of interest.")
    ap.add_argument("--authors", required=True, help="manuscript authors, separated by ';'")
    ap.add_argument("--author-affiliations", default="", help="authors' institutions, separated by ';'")
    ap.add_argument("--reviewers", required=True, help="CSV with name, affiliation columns")
    ap.add_argument("--papers", action="append", required=True, help="publication records: .bib or CSV (authors;year)")
    ap.add_argument("--window", type=int, default=5, help="years within which co-authorship is a conflict")
    ap.add_argument("--year", type=int, help="current year (default: latest year in the records)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    papers = [p for f in args.papers for p in load_papers(f)]
    with open(args.reviewers, encoding="utf-8-sig", newline="") as fh:
        reviewers = list(csv.DictReader(fh))
    res = check_reviewers([a.strip() for a in args.authors.split(";") if a.strip()], reviewers, papers, args.window,
                          args.year, [a for a in args.author_affiliations.split(";") if a.strip()])
    if args.json:
        print(json.dumps(res, indent=2))
    else:
        for r in res:
            print("%-7s %-25s %s" % (r["severity"].upper(), r["reviewer"], "; ".join(r["conflicts"]) or "no conflict found"))
        print("\nScreening is based only on the records provided; always ask reviewers to declare conflicts.")
    return 1 if any(r["severity"] == "high" for r in res) else 0
