# coi-checker

**Screen suggested or invited reviewers for conflicts of interest with the authors: recent
co-authorship, same institution, the reviewer being an author, and shared co-author networks.**

Part of the *Research Automation Toolkit*: 100 open tools for daily research work.

## Why

Editors, programme committee chairs and authors suggesting reviewers must avoid conflicts of
interest; most journals and funders define a conflict as co-authorship within the last few years or a
shared institution. Checking dozens of candidates by searching each name is slow and easily incomplete.
Given publication records (exported from Scholar, Scopus, ORCID or a group bibliography), the check is
automatic and documented.

## Features

- Publication records from BibTeX or CSV (`authors` separated by `;`, `year`)
- Name normalization: `Silva, Ana M.` = `Ana M. Silva` = `A. Silva`; LaTeX accents and particles handled
- Conflicts: reviewer is an author; co-authorship within `--window` years (high) or earlier (medium);
  same institution (high); co-authors shared with the authors (medium)
- Severity ranking, JSON output, exit code 1 if any high-severity conflict

## Usage

```bash
pip install .
coi-checker --authors "Ana Silva; Bo Chen" --author-affiliations "University of Lisbon" \
    --reviewers candidates.csv --papers group_publications.bib --papers scopus_export.csv --window 3
```

Name matching uses surname and first initial, so different people with the same name can be flagged and
transliterated names can be missed; treat results as screening and always ask reviewers to declare conflicts.

## Testing

```bash
python -m unittest discover -s tests -t .
```

## License

MIT (c) JANIN A APURBA
