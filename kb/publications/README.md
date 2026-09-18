# kb/publications/

The validated corpus: one `Container-<author><year>.yaml` file per extracted
publication. Files land here through the `/claim-paper` or `/fetch-and-curate`
workflow — extracted from the paper with exact-quote evidence, validated
(`just validate-all`), and merged by PR. Every file names its source paper in
`source_publication` and every extracted measurement carries an `evidence`
block quoting the paper.

Do not hand-edit files here without re-running `just validate-file <file>`.

## The pooled workbook

These YAML files are the source of truth. Everyone who wants spreadsheets
gets the **pooled workbook** — one Excel file with one tab per entity type
(protocols, key events, each assay type and its outputs), one row per entity
from ALL papers, each row's first column naming the paper it came from.

- Build it locally any time: `just generate-workbook` (writes
  `exports/soma_extractions.xlsx`; the folder is gitignored — the workbook
  is a generated product and is never committed or hand-edited).
- CI rebuilds and publishes it after every merge to main: download the
  current copy from the repo's **workbook-latest** release.
- `just check-entity-ids` (part of `just qc`) enforces the pooling rules:
  KeyEvent IDs are shared vocabulary across papers; every other ID belongs
  to exactly one paper.
