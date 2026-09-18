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
git grep -h -A6 '"KE:ke-decreased-cftr"' origin/main -- kb/ | head -12
```

- If the ID exists anywhere in `kb/` on main, copy that block **verbatim** —
  same name, same description, same fields. Do not improve the wording; a
  wording fix is its own PR touching every file that uses the block.
- Mint a new `KE:` ID only when no existing key event fits, and keep its
  content minimal so it is easy for the next paper to reuse.

## Step 5 — Verify

```bash
just validate-file kb/publications/<file>.yaml    # schema + terms + quotes
just verify-snippets kb/publications/<file>.yaml  # quotes incl. local PDF text
```

Save `verify-snippets` output — its summary goes in the PR description.

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
