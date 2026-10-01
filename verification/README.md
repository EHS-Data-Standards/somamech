# Verification receipts

One JSON file per paper with at least one quote **CI cannot verify
directly**: the committed cache entry (`references_cache/PMID_<n>.md`) is
abstract-only — the publisher blocks automated full-text fetching — and the
quote does not itself resolve in that committed entry, so only the curator's
local full-text check can vouch for it.

A receipt records a SHA-256 hash of every such snippet, written by
`just verify-snippets` **only after** the quote checker passed against the
paper's full text in the curator's local, gitignored
`references_cache_local/`. In CI, `just check-receipts` recomputes each hash
from the kb YAML and requires a match: a quote with no receipt, or one edited
after verification, fails the build. Quotes CI can check itself never appear
here: papers with full text in the committed cache, and abstract-only papers
whose quotes are verbatim in the committed abstract (issue #108) — the
reference validator verifies those directly, so no receipt is needed and an
abstract-only paper with no obtainable PDF can still go green.

Never write or edit these files by hand. A receipt is the pipeline's record
that a local verification actually ran; a hand-written one is fabricated
evidence, treated in review exactly like a hand-written cache entry.
Reviewers of restricted papers should re-derive the text from the PDF
(`just extract-paper-text pdfs/<file> PMID:<n>`) and re-run
`just verify-snippets` rather than trusting the receipt.
