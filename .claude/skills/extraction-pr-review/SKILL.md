---
name: extraction-pr-review
description: Review checklist for a paper-extraction PR (a new kb/publications/ file with evidence quotes). Used by the automatic PR review workflow and for local self-review before opening a PR.
---

# Reviewing a paper-extraction PR

An extraction PR adds one `kb/publications/Container-*.yaml` file (plus its
reference cache entries and term cache rows, minus its stub). The review's
job is to answer one question: **does this file faithfully record what the
paper actually reports?**

## What to check, in order of importance

### 1. The evidence is real (most important)

- Every `reference:` PMID resolves to a real paper, and `references_cache/`
  contains its entry — added by `just fetch-reference`, never hand-written.
  A hand-written cache entry defeats the entire check and is an automatic
  request-changes.
- Every `snippet:` is an exact quote. Run the check rather than eyeballing:
  `just validate-all` (CI does this too). A snippet the checker can't verify
  (paper not in the public cache) should be explained by the PR's quote
  verification summary — the extractor verified it locally against the PDF.
- Every `reference_title:` matches the title in the cache file's frontmatter.
  The known failure mode is specific: correct PMID, verified snippet,
  invented title — an agent quotes accurately and then writes the title from
  memory. Compare against `head -5 references_cache/PMID_<n>.md`.
- `evidence_source` classifies the cited study itself (IN_VITRO for cell
  culture work, MODEL_ORGANISM for mice, HUMAN_CLINICAL for cohorts), not
  who did the extraction.

### 2. The numbers are the paper's numbers

- Spot-check extracted values against the quoted snippets and, where the
  full text is cached, against the paper. No value should exist that the
  paper doesn't state — figure-eyeballed values and unit conversions the
  paper didn't do are hallucinations.
- Sample sizes, p-values, and units should match the paper exactly.

### 3. The ontology terms are right

- Term IDs exist and labels match the ontology (the term validator checks
  this mechanically; CI runs it). What it can't check: whether the term is
  the RIGHT one. A real CURIE with a matching label can still be the wrong
  concept — check that cell types, chemicals, anatomy, and units actually
  mean what the paper means.
- Prefer the most specific correct term (e.g. the specific airway epithelial
  cell type over "epithelial cell") when the paper supports it.

### 4. The file is complete and well-formed

- `source_publication:` names the paper the file came from.
- Every assay links to a key event (`informs_on_key_event`), a study subject,
  and its exposure conditions where the paper reports them.
- The PR contains exactly one paper: its kb file, only ITS cache entries,
  only ITS term rows, and its stub deleted. Another paper's files in the
  diff means a careless `git add` — ask for it to be trimmed.
- The PR body carries `Closes #<claim issue>` so merging releases the claim.

## Severity, and what to do

- 🔴 **Must fix**: fabricated or unverifiable evidence, hand-written cache
  entries, wrong numbers, hallucinated values, failing validation.
- 🟡 **Should fix**: wrong-concept ontology terms, wrong evidence_source,
  invented titles, missing source_publication, extra files in the PR.
- 🔵 **Suggestion**: more specific terms, extra evidence quotes, style.

With any 🔴 or 🟡 findings, request changes. With only 🔵 or nothing,
approve. Be specific: name the assay ID, the snippet, the term — a reviewer
comment the author can act on without guessing.
