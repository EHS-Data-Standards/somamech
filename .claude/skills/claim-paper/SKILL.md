---
name: claim-paper
description: Claim the next paper in the extraction queue, extract it into a verified kb/publications/ YAML file with exact-quote evidence, and open the pull request
user_invocable: true
---

# /claim-paper — take the next paper from the corpus and extract it

This is the main command of the paper-extraction pipeline. One run carries one
paper all the way: pick it, claim it publicly, extract its data with quoted
evidence, verify everything, and open a PR. One paper per run, one paper per
PR, always.

The user may name a specific paper ("claim the Montgomery paper",
"/claim-paper PMID:32275839"); otherwise take the next available one.

## Step 1 — Pick a paper

```bash
just fetch-claims          # open "claim" issues = papers someone is working on
just next-unclaimed 5      # next papers in the queue nobody has claimed
```

`next-unclaimed` already skips claimed papers. Papers marked `EXTRACT`
(screened in) come before `UNDECIDED` ones.

Before committing to a paper, make sure it isn't already done or in flight
somewhere the claim list can't see. Check all three places:

```bash
# 1. Already extracted on main (even under a different filename)?
git fetch origin main
git grep -l "PMID:<number>" origin/main -- kb/ || true

# 2. Already in an open claim issue title? (covered by just fetch-claims)

# 3. Already in an open PR? (the easy one to miss)
gh pr list --state open --search "PMID:<number>" --json number,title,url
```

The `|| true` matters: `git grep` exits nonzero when it finds nothing, which
is the good case here.

## Step 2 — Claim it

Open a GitHub issue that tells everyone this paper is taken:

```bash
gh issue create \
  --title "Extract <short paper title> (PMID:<number>)" \
  --assignee "@me" \
  --label claim,extraction \
  --body "Extracting **<full title>** (PMID:<number>) into kb/publications/.

Stub: stubs/<stub-file>.yaml
Source: <corpus_csv or keyword_search>"
```

Two details are load-bearing:
- **The `claim` label** — it is how `just fetch-claims` finds open claims
  instantly (a label list query is immediately consistent; text search lags).
- **The PMID in the title** — it is the key everything matches on. An issue
  titled "extract the Montgomery paper" reserves nothing.

Never write the claim into the stub file. The issue is the single source of
truth for "who is working on what"; the stub only says "this paper is in the
queue". Two records of one fact drift apart.

If the `claim` or `extraction` label doesn't exist yet, create it with
`gh label create claim` (no `--force` — it would overwrite an existing
label's color and description).

## Step 3 — Get the paper's text

```bash
just fetch-reference PMID:<number>
```

This writes `references_cache/PMID_<number>.md` — the abstract, or the full
text when the paper is open access (the file's `content_type:` says which).
Never create or edit cache files by hand; a cache the extractor can edit
can't catch anything.

If the cache holds only the abstract and a local PDF of the paper exists,
make its full text checkable on this machine (this local cache is gitignored
and never pushed — that is how paywalled text stays out of the public repo):

```bash
just extract-paper-text <path-to-pdf> PMID:<number>
```

## Step 4 — Extract

Work on a fresh branch first:

```bash
git checkout -b extract/<firstauthor><year> origin/main
```

Then follow the **pdf-to-yaml** skill (with **soma-terms** and **oaklib** for
ontology IDs) to produce `kb/publications/Container-<firstauthor><year>-<agent>-<focus>.yaml`.
The pdf-to-yaml skill describes the required `source_publication:` header and
the `evidence:` block every assay must carry — an exact quote from the paper
beside every extracted measurement.

**Key Events are shared vocabulary — reuse, never re-author.** Different
papers informing the same key event must carry byte-identical KeyEvent
blocks: the pooled workbook merges identical blocks and REJECTS the same
`KE:` ID with different wording (`just check-entity-ids`). So before writing
any `informs_on_key_event:` block:

```bash
git grep -h -A6 '"KE:ke-decreased-cftr"' origin/main -- kb/ tests/data/valid/ | head -12
```

Search `tests/data/valid/` as well as `kb/` — `kb/publications/` starts out
holding only a README, so a `kb/`-only grep silently returns nothing and
leads you to re-author a block that already exists. The canonical wording for
the founding vocabulary lives in the test fixtures.

- If the ID exists anywhere on main, copy that block **verbatim** — same name,
  same description, same fields. Do not improve the wording; a wording fix is
  its own PR touching every file that uses the block.
- Mint a new `KE:` ID only when no existing key event fits, and keep its
  content minimal so it is easy for the next paper to reuse.
- **The fixtures are not internally consistent, so a grep can hand you two
  answers.** 5 of the 22 KE IDs on main carry more than one wording, including
  two that disagree inside a single file:

  | ID | variants |
  |---|---|
  | `KE:ao-decreased-lung-function` | "Decreased lung function"/`decreased` vs "Increased airway hyperresponsiveness"/`increased` |
  | `KE:ke-airway-inflammation` | "Airway inflammation" vs "Th2 airway inflammation" |
  | `KE:ke-altered-ciliogenesis` | same name, `altered` vs `decreased` |
  | `KE:ke-goblet-hyperplasia` | "Goblet cell hyperplasia" vs "…and mucin hypersecretion" |
  | `KE:ke2-goblet-hyperplasia` | "Goblet cell hyperplasia" vs "…and mucin hypersecretion" |

  When a grep returns more than one block, pick the variant whose name matches
  its ID (`KE:ao-decreased-lung-function` → "Decreased lung function"), prefer
  the majority wording, and ignore `tests/data/quote_mismatch/` — that fixture
  is deliberately corrupt. Say in the PR body which variant you chose. These
  live in fixtures, so `check-entity-ids` does not see the conflict today; it
  fires the moment two `kb/publications/` files disagree.

## Step 5 — Verify

```bash
just validate-file kb/publications/<file>.yaml    # schema + terms + quotes
just verify-snippets kb/publications/<file>.yaml  # quotes incl. local PDF text
```

Save `verify-snippets` output — its summary goes in the PR description.

**Both must pass, and they check against different caches.** `validate-file`
(and `validate-all`, which is what CI's `just qc` runs) resolves quotes against
the committed `references_cache/` only. `verify-snippets` checks against both:
when a paper also has an entry in `references_cache_local/`, that local PDF
text is *appended* to the committed entry under a `## Full text (local PDF
extraction)` heading, so the checker sees the committed text and the PDF text
together. So:

- A quote taken from the PDF body but absent from the committed cache passes
  `verify-snippets` and **fails CI** unless a committed receipt covers it (see
  below).
- A quote that is verbatim in the committed text keeps verifying even when the
  PDF text layer mangles that same sentence — fi/fl ligatures (`significant` →
  `signiﬁcant`), injected spaces, hyphenated line wraps. The committed copy is
  still in the merged cache to match against, so a PDF artifact alone cannot
  fail a quote you took from the abstract.

When the committed cache is `abstract_only`, quote the abstract: that is the
copy CI resolves against, so a span that is verbatim *there* is the one that
survives. A sentence fragment that verifies beats a whole sentence that does
not. Full text read from a local PDF is still worth having — it belongs in
`description:` fields, which are not quote-checked, and it tells you what is
worth recording. Say in the PR body which claims rest on quotes and which on
locally-read full text.

When the paper's committed cache entry is abstract-only, a passing
`verify-snippets` run also writes `verification/PMID_<number>.json` — a
receipt hashing every locally-verified quote. Commit it with the PR: CI
cannot see the full text, so `just check-receipts` holds those quotes to the
receipt instead (a quote added or edited after verification fails CI). If
`verify-snippets` says the full text is missing from the local cache, go
back to Step 3's `extract-paper-text` — never write a receipt file by hand.

If a quote fails: re-read the source and copy the exact passage, choose a
different passage, or drop the claim. Never reword a quote just to pass the
check, and never report a validation command as passing unless it finished
and you read its output.

The reference validator's `Total checks: N` line counts *issues found*, not
checks performed, so `Total checks: 0` is what a clean file prints. It does
catch real mismatches, but do not read the counter as evidence that anything
was verified.

Term lookups may add rows to `cache/` — commit those too (they are what makes
CI re-runs offline).

## Step 6 — Open the PR

The PR contains exactly one paper's worth of changes:

- `kb/publications/Container-<...>.yaml` (new)
- `references_cache/PMID_*.md` — only the papers THIS file cites
- `cache/**/terms.csv` rows — only the terms THIS file introduced
- `verification/PMID_*.json` — only if this paper is abstract-only (Step 5)
- the paper's stub deleted from `stubs/`

```bash
git add kb/publications/<file>.yaml references_cache/PMID_<number>.md cache/ verification/
git rm stubs/<stub-file>.yaml
git commit -m "extract: <Author Year> (PMID:<number>) — <one-line gist>"
git push -u origin extract/<firstauthor><year>
gh pr create --title "Extract <Author Year>: <short title> (PMID:<number>)" \
  --body "<summary of what was extracted>

## Quote verification
<the verify-snippets summary>

Closes #<claim-issue-number>"
```

`Closes #<issue>` is what releases the claim: merging the PR closes the claim
issue and deletes the stub in one step. Don't add unrelated files — a sweep
like `git add references_cache/` can drag another paper's cache entries into
this PR.

Then stay with the PR until it is merged: respond to review comments, fix
what reviewers find, re-run the checks after every fix.
