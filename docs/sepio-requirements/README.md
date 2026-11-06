# SEPIO requirements collection — SOMA

Working state for SOMA's submission to the [SEPIO](https://github.com/sepio-framework/sepio-linkml)
consortium's Evidence, Provenance and Confidence (EPC) requirements collection.

SEPIO's process is requirements-first: it does not want SOMA mapped to SEPIO yet. It wants a reviewed
statement of what SOMA represents now and what it should support, from which the modelers build a covering
model and LinkML-Map transformations in a separate workflow.

- **Run** `SOMA-20261105-R01`, drafted 2026-11-05
- **Upstream** `sepio-framework/sepio-linkml` @ `main`, `docs/requirements-collection/`
  (forms sha256 `22e6c85a…`, guidance sha256 `8a39ffdb…`)
- **Read against** `soma-schema` 0.2.4 and the 41 files in `kb/publications/`

## Deliverables

| # | Deliverable | Status | Location |
|---|---|---|---|
| 1 | Scope statement | decided, not yet written up | this file, below |
| 2 | Resource inventory | not started | `SOMA_Resource_Inventory.md` |
| 3 | Requirements workbook (8 forms) | not started | `SOMA_Requirements_v0.1_<date>_<time>.xlsx` |
| 4 | Project feedback log | drafted, 10 observations | `SOMA_Feedback_v0.1_20261105.xlsx` |

A Requirements Review Memo accompanies the workbook, stating the scope, the sources and versions used, the
conclusions, the open questions and worked examples.

The feedback log is a project-run observation log, not a change request: it records difficulties and
ambiguities met while completing the forms, for a separate consolidation step. Agent columns A–V are
populated; W–AD (master linkage, consolidation, governance, implementation, validation) are deliberately left
blank for the consortium. It was generated from SEPIO's `Feedback_Log_Template.xlsx` with the three
instruction sheets intact.

## How SOMA looks in SEPIO's vocabulary

Two features of the schema drive nearly every answer.

**There is no reified claim.** Evidence attaches to four classes — `Assay`, `AssayOutputMeasurement`,
`KeyEvent` and `KeyEventRelationship` — and in three of those four the proposition is implicit in the parent
record plus its slot values. "Under 45.28 µg/m³ ambient PM2.5, measured FEV1/FVC in this cohort fell to
84.32%" is a claim a reader can extract, but no object in the file states it. Only `KeyEventRelationship` is
natively subject–predicate–object.

**Evidence item and interpretation are one flat object.** `EvidenceItem` holds both the quoted passage and the
judgement about it, and nothing groups items into arguments. SEPIO's own mapping registry records this shape
as a gap whose transform is "not automatic".

### Field-level reading

| SOMA field | Nearest SEPIO target | Status |
|---|---|---|
| `reference` | `InformationEntity.sources` | maps |
| `reference_title` | `dcterms:title` | maps |
| `snippet` | `Statement.statementText` *or* `DataItem` | ambiguous — see Q4 |
| `supports` | `EvidenceLine.directionOfEvidenceProvided` | carrier differs |
| `explanation` | `EvidenceLine` (description) | carrier differs |
| `evidence_source` | `PROV.EI.GENERATION_CONTEXT` | SEPIO gap |
| `article_section` | — none — | SEPIO gap |
| `figure_reference` | — none — | SEPIO gap |
| `KeyEventRelationship.evidence_support` | `EvidenceLine.strengthOfEvidenceProvided` | carrier differs |
| `KeyEventRelationship.quantitative_understanding` | — none — | SEPIO gap |

### The provenance that exists but is not in the data

`Container` has exactly one provenance slot, `source_publication`. No agent, no date, no model, no method, no
version. Everything about how a file came to exist lives outside it: in git history, in pull-request records,
in the `claim-paper` skill definition, and in `verification/*.json` receipts that record the validator used,
the date, whether the cached source was full text or abstract only, and a SHA-256 per snippet. There are 3
such receipts for 41 files.

This is the largest finding of the read, and it is a schema change in the
[`soma`](https://github.com/EHS-Data-Standards/soma) repository rather than a SEPIO issue.

## Decisions

### Q1 · Scope — **maximal**

The canonical YAML (`kb/publications/*.yaml`) and the installed `soma-schema` control current-state answers.
The wider repository may inform desired-state answers: the `claim-paper` and `extraction-pr-review` skills,
the `verification/` receipts, the DuckDB export and its `measurement_full` view, the reference cache, and the
corpus re-review epic.

This lets the forms say "we do not store the extracting agent, but we know it and want to" rather than simply
"no". A minimal scope would have answered "no" to roughly thirty provenance rows the project in fact has
answers for.

A third scope was considered and set aside: SOMA has two legitimate products, the YAML knowledge base and the
generated DuckDB/TSV/workbook exports, and the exports flatten evidence differently. Giving them their own
scope stays available if the consortium turns out to care about the queryable product.

### Q2 · Claim types — **six**

Measurement, comparison (`response_comparisons`), key event, key-event relationship, assay-method and
exposure are all reported as claim types in their own right, rather than folding the last two in as qualifying
context. This is the more faithful reading of the file structure: a protocol and an exposure condition each
carry their own asserted content.

The cost lands on the claim–evidence matrix, where assay-method and exposure rows will take much the same
evidence as the claims they contextualise. Note this in the review memo so the modelers do not read the
repetition as an error.

### Q5 · Evidence lines — **both, split by claim type**

The flat `EvidenceItem` must be preserved for measurement and comparison claims: the parsers, the review skill
and the snippet validator all work with it. Evidence lines are wanted for key-event-relationship claims, where
grouping and AOP weight-of-evidence strength are real and currently recorded on the claim with no link to the
items that justify them.

So SOMA needs a profile split rather than one evidence model, which is also the answer to the form's question
about whether different claim types need different evidence models.

### Q6 · Extraction provenance — **into the data, top desired-state priority**

A per-file provenance block covering agent and model, skill and version, human director and reviewer,
extraction date, cache content type, and verification status with tool and date.

Reported as the project's leading desired-state requirement and worth raising as a `soma` repository issue in
its own right, independent of what SEPIO adopts. The repository README already insists that a human name on a
commit means direction and review rather than authorship — exactly the distinction SEPIO's provenance levels
draw, recorded nowhere a data consumer can read it.

## Open questions

| # | Question | Leaning |
|---|---|---|
| Q3 | Reify claims, or keep them implicit and let the transform reconstruct them? | "Maybe", with `KeyEventRelationship` reified first — already SPO-shaped and few in number |
| Q4 | Is a quoted snippet the evidence item, or a pointer to one? | The passage is the item: free text, individually addressable, filed as a custom type. The numbers it reports are already modeled as measurements, so calling it a data item double-counts them |
| Q7 | Does ontology grounding carry per-step confidence? | Agent, method and date yes; per-step confidence no, unless there are genuinely uncertain groundings in the corpus worth flagging |
| Q8 | Project representative, and one submission or two? | One submission covering both repositories, named for the schema, with the inventory marking which repo is canonical for which dimension |

## Feedback observations

Ten observations, recorded while reading the forms against the schema. Full detail, evidence and suggested
improvements are in the workbook; this table is the index.

| ID | Finding | Category | Priority |
|---|---|---|---|
| OBS-001 | SOMA is the flat evidence/interpretation collapse SEPIO records as a gap; the transform to `InformationEntity` + `EvidenceLine` is documented as not automatic | Model coverage gap | High |
| OBS-002 | No evidence item type for a quoted passage reporting a measurement; the two text-passage rows are scoped to prior claims | Ambiguous definition | High |
| OBS-003 | No provenance type for where inside a document a quote came from, which SOMA records and uses to weigh evidence | Provenance granularity | Medium |
| OBS-004 | No provenance type for mechanical verification of a quote against a stored source copy — SOMA's main trust signal | Missing requirement | High |
| OBS-005 | Categorical strength sits on the claim, not an evidence line, so a literal current-state reading would wrongly say "not represented" | Mapping mismatch | Medium |
| OBS-006 | The Claim Type form presupposes subject–predicate–object claims; enumerating implicit claims is a modeling act the form treats as reporting | Workflow / usability | Medium |
| OBS-007 | Canonical files carry no agent, date, method or version provenance at all, producing a systematic no-but-we-have-it pattern across ~30 rows | Source evidence / scope | High |
| OBS-008 | Verification receipts cover 3 of 41 files, so per-item provenance cannot be answered uniformly; the forms have no way to say "partial" | Source evidence / scope | Medium |
| OBS-009 | Second-project confirmation that evidence generation context deserves a first-class slot; SOMA requires it on every item | Model coverage gap | Medium |
| OBS-010 | `NO_EVIDENCE` means "the source turned out not to bear on this claim", which is not neutral evidence and would be lost in a three-value direction enum | Response options | Medium |

## Next steps

1. Write the scope statement into SEPIO's requirements prompt, and build the resource inventory: the two
   repositories, the schema version, the corpus size, and four or five representative examples given IDs. The
   Ghosh 2025 file (`Container-ghosh2025-pm25-egfr-pi3k-akt.yaml`) is a good hard case — its molecular results
   exist only in figures and carry no quantity values at all.
2. Fill the eight forms. Current state from the canonical YAML and schema only; desired state cited to the
   sources the inventory allows.
3. Draft the review memo, flagging the high-priority feedback observations with references.
4. Hand the workbook, memo and feedback log to the consortium, and open the Q6 provenance block as a `soma`
   repository issue.
