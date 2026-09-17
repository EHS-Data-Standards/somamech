# kb/publications/

The validated corpus: one `Container-<author><year>.yaml` file per extracted
publication. Files land here through the `/claim-paper` or `/fetch-and-curate`
workflow — extracted from the paper with exact-quote evidence, validated
(`just validate-all`), and merged by PR. Every file names its source paper in
`source_publication` and every extracted measurement carries an `evidence`
block quoting the paper.

Do not hand-edit files here without re-running `just validate-file <file>`.
