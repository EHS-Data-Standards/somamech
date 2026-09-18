# Verification receipts

One JSON file per paper whose committed cache entry
(`references_cache/PMID_<n>.md`) is **abstract-only** — the publisher blocks
automated full-text fetching, so CI cannot verify quotes from it directly.

A receipt records a SHA-256 hash of every evidence snippet quoted from that
paper, written by `just verify-snippets` **only after** the quote checker
passed against the paper's full text in the curator's local, gitignored
`references_cache_local/`. In CI, `just check-receipts` recomputes each hash
from the kb YAML and requires a match: a quote with no receipt, or one edited
after verification, fails the build. Papers with full text in the committed
cache never appear here — CI verifies those quotes directly.

Never write or edit these files by hand. A receipt is the pipeline's record
that a local verification actually ran; a hand-written one is fabricated
evidence, treated in review exactly like a hand-written cache entry.
Reviewers of restricted papers should re-derive the text from the PDF
(`just extract-paper-text pdfs/<file> PMID:<n>`) and re-run
`just verify-snippets` rather than trusting the receipt.
