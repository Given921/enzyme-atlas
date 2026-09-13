# Enzyme Atlas agent guide

## Product intent

Enzyme Atlas is a recommendation-first literature site for all enzyme researchers. Do not personalize ranking to one researcher or turn the product into a general-purpose literature search engine. Preserve independent visibility for multi-enzyme cascades, enzyme cascade assembly, and fusion enzymes.

## Authoritative data

- `data/papers.json`: the currently published weekly edition (`edition`, bilingual `items[].en`, `observationsEn`).
- `data/editions.json`: the edition archive manifest; every entry points at the data file holding that edition.
- `data/history/papers-<date>.json`: frozen past editions. Never edit an archived edition.
- `data/classics.json`: the curated classics library, each record carrying `en.note`.
- `i18n.js`: UI strings plus the controlled vocabularies (topics, classic topics, source groups, kinds, labels) used to render data values in English.
- `scripts/weekly_contract.py`: weekly-edition schema and publication gates.
- `scripts/validate_site.py`: cross-file, archive, bilingual and DOI validation.

Treat counts displayed by the site as derived data. Never introduce a promotional or hard-coded paper total.
The Chinese values in the data files are canonical: they are the filter keys and the vocabulary keys. English is resolved at render time, so never rename a `topic`, `sourceGroup`, `kind` or `label` value without updating `i18n.js` (validation enforces coverage).

## Evidence rules

- Use DOI/publisher metadata to identify papers and check version relationships.
- Keep summaries, recommendation reasons, and evidence claims within the abstract or full-text evidence actually inspected.
- Check correction and retraction status before weekly publication.
- A DOI resolving successfully does not by itself prove that a title, journal, year, or scientific claim is correct.
- Every classic needs a concise explanation of why it is foundational or reusable.
- English copy is editorial work, not machine output: it must preserve the Chinese evidence boundary (what the abstract does or does not support) rather than adding claims.

## Update rules

1. Collect candidates into `data/staging/`; never write collector output directly to `data/papers.json`.
2. Curate the full weekly edition with exactly three editorial observations and 3–5 featured papers.
3. Every new paper needs both Chinese copy and an inline `en` object (`summary`, `why`, `evidence`, `audience`, `verification`); each edition needs `observationsEn` with three non-empty title/body pairs. Do not hand-write `edition` — the publisher assigns previous + 1.
4. Run all local validation before publication.
5. Publish only when every gate passes. On any network, schema, DOI, correction/retraction, test, push, or Pages failure, keep the previous public edition.
6. Never silently remove a classic paper or change the non-personalized product positioning.
7. Never edit `data/history/` by hand, and never delete an archived edition; `data/editions.json` is rebuilt by the publisher.

## Required checks

```powershell
python scripts/validate_site.py
python scripts/validate_site.py --online
python scripts/test_weekly_pipeline.py
node --check i18n.js
node --check app.js
node --check search.js
node --check classics.js
node --check archive.js
node scripts/test_classics_ui.js
```

After a successful Pages deployment, run `scripts/verify_public_site.py` against the URL derived from the Git remote. The script must confirm the homepage, classics page, archive page, i18n runtime, weekly data, edition manifest, exact checked-out classic count, requested edition, and English coverage of both data sets.


