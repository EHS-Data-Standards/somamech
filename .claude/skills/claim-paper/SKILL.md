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

A candidate has to pass two checks before you claim it: nobody else has it,
and the whole paper — not just its abstract — can be fetched.

### Is it free? — the three-surface check

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

This grep is deliberately `kb/`-only, unlike the Key Event lookup in Step 4.
It asks "has this paper already been extracted", and the test fixtures must
not answer that — widening it to `tests/` would report fixture papers as
already done.

### Is the whole paper fetchable? — full text before abstract-only

A paper whose full text lands in the committed `references_cache/` is worth
much more than one that arrives as an abstract: CI can verify every quote in
it, the extraction can cover methods and results instead of a summary, and it
needs no verification receipt. So **extract fully downloadable papers first,
and take an abstract-only paper only when the queue has no full-text paper
left.**

Run the check over the candidates that survived the three-surface check:

```bash
just check-fulltext PMID:<a> PMID:<b> PMID:<c>
```

It fetches anything not already cached and reports one line per paper:

```
  PMID:20420656        FULL TEXT      (full_text_pdf)
  PMID:38809424        ABSTRACT ONLY  (abstract_only)
```

Take the first `FULL TEXT` paper in queue order and go on to Step 2.
Queue order still puts `EXTRACT` before `UNDECIDED`, but full text outranks
both: a full-text `UNDECIDED` paper comes before an abstract-only `EXTRACT`
one.

**Put every `ABSTRACT ONLY` paper back in the queue** — which means: do not
claim it, and do not touch its stub. Nothing was claimed, so it is already
back; `next-unclaimed` will offer it again. The check also re-tries the
full-text fetch each time a cached entry never cleanly attempted one, so a
paper that was abstract-only because a provider was down can come back as
full text on a later run.

If none of your candidates is full text, widen the search instead of
settling: ask `next-unclaimed` for more and check those too. Extract an
abstract-only paper only once **every** unclaimed paper in the queue is
abstract-only. When you do fall back, prefer one whose stub has a
`pdf_filename:` — there is a local PDF, so you can at least read the full
text on this machine (Step 3) — and tell the user plainly that the queue held
nothing fully downloadable.

**The stub's `open_access:` flag does not answer this question.** It records
only that the paper has a PubMed Central record. Every stub in the queue today
says `open_access: true`, yet two of the four papers extracted so far came
back `abstract_only` — a PMC record often carries no retrievable text. The
fetched cache entry's `content_type:` is the only evidence.

`check-fulltext` leaves a cache entry behind for every paper it checked,
including the ones you did not claim. Those are untracked and harmless — just
never `git add references_cache/` wholesale (Step 6).

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

Step 1's `check-fulltext` already fetched it into
`references_cache/PMID_<number>.md` — the abstract, or the full text when the
paper is open access (the file's `content_type:` says which). If you arrived
here without it, fetch it now:

```bash
just fetch-reference PMID:<number>
```

Never create or edit cache files by hand; a cache the extractor can edit
can't catch anything.

For the `full_text_*` paper Step 1 chose, you have everything you need — go
to Step 4.

You are here with an abstract-only paper only if Step 1 found nothing better
in the entire queue. If a local PDF of it exists, make its full text checkable
on this machine (this local cache is gitignored and never pushed — that is how
paywalled text stays out of the public repo):

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

First count the variants, so a disagreement is visible rather than hidden
below the fold:

```bash
git grep -h -A3 '"KE:ke2-goblet-hyperplasia"' origin/main -- kb/ tests/data/valid/ \
  | grep -E 'name:|biological_action:' | paste - - | sort | uniq -c | sort -rn
```

That prints one line per distinct wording with its count. One row means the
corpus is unanimous — copy that block and move on. More than one row is a
disagreement, and the counts are exactly what the "prefer the majority" rule
below needs. This is what the output looked like while this ID was still
contested (unified in #170 — do not expect these exact counts):

```
  30       name: "Goblet cell hyperplasia"                          biological_action: increased
   2       name: "Goblet cell hyperplasia and mucin hypersecretion"  biological_action: increased
```

Then read the full block you chose (`-A6`) to copy it verbatim. Do not pipe
the full-block form through `head` — with `-A6` a dozen lines is under two
blocks, so a contested ID looks unanimous and you never reach the tie-break.

Search `tests/data/valid/` as well as `kb/` — `kb/publications/` starts out
holding only a README, so a `kb/`-only grep silently returns nothing and
leads you to re-author a block that already exists. The canonical wording for
the founding vocabulary lives in the test fixtures.

- If the ID exists anywhere on main, copy that block **verbatim** — same name,
  same description, same fields. Do not improve the wording; a wording fix is
  its own PR touching every file that uses the block.
- Mint a new `KE:` ID only when no existing key event fits, and keep its
  content minimal so it is easy for the next paper to reuse.
- **The corpus has drifted before, so a grep can hand you two answers.** At
  one point 5 of the 22 KE IDs on main carried more than one wording,
  including two that disagreed inside a single file (unified in #170) —
  which is why you count first instead of trusting the first block you see.

  When the count shows more than one row, pick the variant whose name matches
  its ID (`KE:ao-decreased-lung-function` → "Decreased lung function"), prefer
  the majority wording, and ignore `tests/data/quote_mismatch/` — that fixture
  is deliberately corrupt.

  When the names tie, apply the same majority rule to `biological_action`.
  `KE:ke-altered-ciliogenesis` was the case in point: both variants were named
  "Altered ciliogenesis" and differed only in the action (`altered` vs the
  majority `decreased`), so the name test could not decide it — only the
  counts could. Say in the PR body which variant you chose. A conflict that
  lives only in fixtures is invisible to `check-entity-ids` today; it fires
  the moment two `kb/publications/` files disagree (#128 tracks closing that
  gap).

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
  `verify-snippets`. When the paper is abstract-only, `validate-file` does not
  fail on it either: the recipes set `ALLOW_ABSTRACT_ONLY_MISSES=1`, which
  tells the wrapper to ignore misses flagged `only abstract available for
  PMID:...` and hand responsibility to the committed receipt instead (see
  below). Against a paper that is NOT abstract-only, the same miss is a hard
  CI failure.
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
