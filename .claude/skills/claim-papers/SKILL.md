---
name: claim-papers
description: Claim and extract several papers in parallel (one sub-agent, one git worktree, one claim issue, one PR per paper)
user_invocable: true
---

# /claim-papers N — extract several papers at once

Batch version of **claim-paper**: N papers (default 3, max 8), each handled
by its own sub-agent in its own git worktree, producing its own claim issue
and its own one-paper PR. The claim issues are what keep parallel agents
(and parallel humans) from colliding — file ALL of them before dispatching
ANY agent.

If the user gave a number, use it; cap at 8. Papers marked `EXTRACT` in
their stubs come before `UNDECIDED` ones.

## Step 1 — Pick and verify N papers (in the main checkout)

```bash
just fetch-claims
just next-unclaimed <N+3>     # a few spares in case verification drops some
```

For each candidate, run the same three-surface check as claim-paper Step 1
(kb/ on origin/main, open claim issues, open PRs) and keep the first N that
are genuinely free.

## Step 2 — File ALL claim issues first

Create the N claim issues one after another (claim-paper Step 2 format:
`Extract <short title> (PMID:NNNNNNNN)`, labels `claim,extraction`,
assigned). Only when all N exist do the locks cover every paper — an agent
dispatched before its claim exists is racing anyone else who runs
`next-unclaimed` in that window.

Record the (paper, stub, claim issue number, pdf_filename) list — each
agent gets exactly one entry.

## Step 3 — One worktree per agent, then dispatch

Each sub-agent works in its own git worktree. This is non-negotiable: in
dismech's production run, parallel agents given only a branch name wrote
their files into the parent checkout — branches ended up empty and recovery
required surgery. The worktree makes that impossible.

Give every sub-agent instructions to do the following, filling in its
specific paper:

1. Create the worktree and prove you are in it before writing anything:
   ```bash
   git fetch origin main
   git worktree add ../soma-wt-<key> -b extract/<key> origin/main
   cd ../soma-wt-<key>
   pwd    # MUST print .../soma-wt-<key> — stop if it doesn't
   ```
2. Follow the **claim-paper** skill from its Step 3 (fetch reference →
   extract with quoted evidence → verify → PR), entirely inside the
   worktree. The claim issue already exists — do not file another; put
   `Closes #<its number>` in the PR body.
3. Obey the claim-paper rules that matter most in parallel:
   - **Key Event blocks are copied verbatim from origin/main, never
     re-authored** — two agents wording the same KE differently is the one
     collision the ID check cannot auto-merge. Grep `kb/` *and*
     `tests/data/valid/`: `kb/publications/` starts out empty, and several IDs
     have more than one wording on main. See claim-paper Step 4 for which
     variant to pick.
   - **Quotes must verify against the committed `references_cache/`**, which
     is what CI checks. A quote read out of a local PDF passes
     `verify-snippets` and fails CI. See claim-paper Step 5.
   - One paper, one PR; add only YOUR paper's kb file, reference cache
     entries, term cache rows, and stub deletion.
   - Write scratch files inside your own worktree. The session scratchpad is
     shared between parallel agents, so a fixed name there gets clobbered.
4. Report back: branch name, PR URL, and the quote-verification summary.

Dispatch all N sub-agents in parallel.

## Step 4 — Audit the results (back in the main checkout)

Sub-agent reports of success are not evidence. For each paper:

```bash
git fetch origin
git log origin/main..origin/extract/<key> --oneline   # empty = stranded work
gh issue view <claim#> --json closedByPullRequestsReferences
```

The issue-view check is the reliable way to confirm a PR is linked — a text
search like `gh pr list --search "closes #N"` free-text-matches unrelated
numbers (dismech matched `ORPHA:2704` against issue #2704 in production).

For any agent whose branch is empty or whose PR is missing: its work is
stranded in the worktree — inspect `../soma-wt-<key>`, commit/push what is
there, or close its claim issue so the paper returns to the queue.

## Step 5 — Clean up worktrees

After each PR is open (not merged — the branch must live on):

```bash
git worktree remove ../soma-wt-<key>
git worktree prune
```

## While the PRs are in review

Merges land one at a time, and branch protection requires each PR to be up
to date with main — so after each merge, the next PR needs its branch
updated (use GitHub's update-branch button or `gh api`; never rebase) and
CI re-runs the whole-repo checks against the new main. Shared-file overlaps
(two PRs adding rows to the same `cache/*/terms.csv`) surface here as
ordinary merge updates, and a KE-wording clash surfaces as a
`check-entity-ids` failure on the later PR — fix it by copying the block
that is now on main.
