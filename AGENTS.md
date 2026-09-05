# Enzyme Atlas agent guide

## Product intent

Enzyme Atlas is a recommendation-first literature site for all enzyme researchers. Do not personalize ranking to one researcher or turn the product into a general-purpose literature search engine. Preserve independent visibility for multi-enzyme cascades, enzyme cascade assembly, and fusion enzymes.

## Authoritative data

- `data/papers.json`: the currently published weekly edition.
- `data/classics.json`: the curated classics library.
- `scripts/weekly_contract.py`: weekly-edition schema and publication gates.
- `scripts/validate_site.py`: cross-file and DOI validation.

Treat counts displayed by the site as derived data. Never introduce a promotional or hard-coded paper total.

## Evidence rules

- Use DOI/publisher metadata to identify papers and check version relationships.
- Keep summaries, recommendation reasons, and evidence claims within the abstract or full-text evidence actually inspected.
- Check correction and retraction status before weekly publication.
- A DOI resolving successfully does not by itself prove that a title, journal, year, or scientific claim is correct.
- Every classic needs a concise explanation of why it is foundational or reusable.

## Update rules

1. Collect candidates into `data/staging/`; never write collector output directly to `data/papers.json`.
2. Curate the full weekly edition with exactly three editorial observations and 3–5 featured papers.
3. Run all local validation before publication.
4. Publish only when every gate passes. On any network, schema, DOI, correction/retraction, test, push, or Pages failure, keep the previous public edition.
5. Never silently remove a classic paper or change the non-personalized product positioning.

## Required checks

```powershell
python scripts/validate_site.py
python scripts/validate_site.py --online
python scripts/test_weekly_pipeline.py
node --check app.js
node --check search.js
node --check classics.js
node scripts/test_classics_ui.js
```

After a successful Pages deployment, run `scripts/verify_public_site.py` against the URL derived from the Git remote. The script must confirm the homepage, classics page, weekly data, exact checked-out classic count, and requested edition.


