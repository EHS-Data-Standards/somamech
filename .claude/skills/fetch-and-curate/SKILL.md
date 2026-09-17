---
name: fetch-and-curate
description: Discover new open-access papers with the saved PubMed keyword searches, add them to the queue, and optionally extract one end-to-end
user_invocable: true
---

# /fetch-and-curate — grow the corpus from the saved PubMed searches

The second way into the extraction queue (the first is corpus.csv). This
command runs the committed keyword searches against PubMed and works **only
with open-access papers** — papers whose full text can be legally downloaded
into the public reference cache, so every quote can be checked in CI and no
local PDF is ever needed. Paywalled results are discarded, always.

The user may name a search or a topic ("fetch-and-curate for goblet cells",
"/fetch-and-curate L2_GobCell"); otherwise run all searches.

## Step 1 — Search

The searches live in `conf/pubmed_searches.tsv` (35 searches in 4 layers:
broad endpoint searches, mechanistic searches, measurement-method searches,
and pulmonary-context searches). Run them:

```bash
# All searches, open-access papers only, skipping papers already known:
uv run python scripts/search_pubmed.py --open-access-only --exclude-known

# Or specific searches:
uv run python scripts/search_pubmed.py --search L2_GobCell --search L4_GobCellEnd \
  --open-access-only --exclude-known
```

This writes three files under `data/literature_search/`:
- `run_log.csv` — date, search ID, hit count (the permanent record of runs)
- `raw_retrieval_<date>.csv` — every (paper, search) pair, duplicates kept
- `candidates_<date>.csv` — deduped papers ranked by how many searches found
  them (a paper found by five searches is probably more central than one
  found by one)

## Step 2 — Show the candidates

Read the top of `candidates_<date>.csv`, fetch titles for the top candidates
(`scripts/build_stubs.py` does this when stubbing; for a quick look use the
PubMed esummary API), and present them to the user: title, journal, year,
which searches found it. Let the user choose which to add to the queue —
or, if they asked for a fully automatic run, take the top-ranked paper.

## Step 3 — Add the chosen papers to the queue

Append the chosen papers to `corpus.csv`? **No** — corpus.csv is the
hand-curated primary list. Keyword-search papers get stubs directly:

For each chosen paper, create `stubs/<FirstAuthor>_<year>_PMID<number>.yaml`
by adding a row to a temporary CSV and running the stub builder, or write the
stub with the same fields the builder produces — but set:

```yaml
source: keyword_search
found_by: [L2_GobCell, L4_GobCellEnd]   # the searches that found it
decision: EXTRACT                        # the user just screened it in
```

Then check the queue is still healthy: `just check-stubs`.

Commit new stubs on a branch and PR them (`queue: add N papers from keyword
search <date>`) — stubs are curated content and go through review like
everything else.

## Step 4 — Extract one (optional)

If the user wants a paper extracted now, continue with the **claim-paper**
skill from its Step 1, choosing the new paper. Because the paper is open
access, `just fetch-reference` pulls its full text into the public cache and
CI verifies every quote — the local-PDF step is never needed.
