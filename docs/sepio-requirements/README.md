# SEPIO requirements collection — SOMA

SOMA's submission to the [SEPIO](https://github.com/sepio-framework/sepio-linkml) consortium's
Evidence, Provenance and Confidence (EPC) requirements collection.

SEPIO's process is requirements-first: it does not want SOMA mapped to SEPIO yet. It wants a
reviewed statement of what SOMA represents now and what it should support, from which the modelling
group builds a covering model and LinkML-Map transformations in a separate workflow. Accordingly,
the Requirement → SEPIO Mapping Registry was not used, and the workbook's `SEPIO Mapping Summary`
columns are untouched.

- **Run** `SOMA-20261109-R01`, prepared 2026-11-09
- **Upstream** `sepio-framework/sepio-linkml` @ `main`, `docs/requirements-collection/`
  (forms sha256 `22e6c85a…`, guidance sha256 `8a39ffdb…`)
- **Read against** `soma-schema` 0.2.4 and the 41 files in `kb/publications/` at `somamech` `d8f40d9`
- **Status** agent-prepared first pass — **a draft until the project representative validates it**

## Deliverables

| Deliverable | File |
|---|---|
| Scope statement and resource inventory | [`SOMA_Resource_Inventory.md`](SOMA_Resource_Inventory.md) |
| Populated requirements workbook (8 forms, 596 cells) | `SOMA_Requirements_v0.1_20261109_1130.xlsx` |
| Requirements Review Memo (12 sections) + source-access status | [`SOMA_Requirements_Review_Memo_v0.1_20261109_1130.md`](SOMA_Requirements_Review_Memo_v0.1_20261109_1130.md) |
| Project feedback log (14 observations) | `SOMA_Requirements_Feedback_Log_v0.1_20261109_1130.xlsx` |

Both workbooks are generated, not hand-edited. See [`generators/`](generators/).

The feedback log is a project-run observation log, not a change request: it records difficulties
and ambiguities met while completing the forms, for a separate consolidation step. Agent columns
A–V are populated; W–AD (master linkage, consolidation, governance, implementation, validation) are
left blank for the consortium.

## Regenerating the workbooks

Answers live in Python data structures, so a revision after representative review is an edit to a
data structure rather than a hand edit to a spreadsheet cell.

```sh
# fetch the blank templates from sepio-linkml first, then:
uv run --with openpyxl python -I docs/sepio-requirements/generators/build_workbook.py \
    /path/to/Requirements_Collection_Forms.xlsx \
    docs/sepio-requirements/SOMA_Requirements_v0.1_20261109_1130.xlsx

uv run --with openpyxl python -I docs/sepio-requirements/generators/build_feedback.py \
    /path/to/Feedback_Log_Template.xlsx
```

`build_workbook.py` runs the completeness and consistency checks that SEPIO's rule 41 and guidance
section IV require, and exits non-zero on any problem: required `Y`/`N`/`M` columns complete and
using exact labels, EIT conditional columns populated and drawn from their controlled vocabularies,
required CT and PO fields present, every row where current differs from desired naming a
desired-state support type or carrying a human-review flag, and the `SEPIO Mapping Summary` columns
unchanged from the template.

`xlsx_cells.py` writes cells by editing the sheet XML inside the template's own zip container and
copying every other part byte-for-byte. This is required by rules 36–40 of
`REQUIREMENTS_FORM_PROMPT.md`: the template carries Excel Tables, drawings, VML drawings and legacy
comments that common Python spreadsheet libraries do not round-trip faithfully, and the returned
workbook must open without an Excel repair warning. Current result: **8 of 41 parts changed, 33
byte-identical** — all styles, tables, drawings and comments preserved.

## How SOMA reads in SEPIO's vocabulary

**Claim representation is not uniform.** Measurement, key-event, assay-method and exposure claims
are implicit slot/values and nested objects on parent records. Comparison claims
(`ResponseComparison`) and key-event-relationship claims (`KeyEventRelationship`) *are* genuinely
reified first-class objects with their own identifiers and evidence lists. No graph-edge
representation exists in the canonical data.

**Evidence item and interpretation are one flat object.** `EvidenceItem` holds the quote, the cited
publication and title, the article section, the figure or table label, the direction of support and
a curator explanation. Nothing groups items into arguments. This is an intentional implementation
preference — the extraction agents emit it, the validators check it, and the DuckDB builder, pooled
workbook and review site all read it.

**The claim types do not share one evidence model.** Five share a flat per-item profile with
direction only; key-event-relationship claims need a categorical weight-of-evidence judgement over
a *group* of evidence items, drawn from the OECD AOP framework. A SEPIO-based representation needs
both, selected per claim type. This is the most important structural finding for the modelling
group.

**The canonical data carries no provenance beyond the cited publication.** `Container` has exactly
one provenance slot, `source_publication`. There is no agent, date, model, method or version field
anywhere in 41 files. Hence the dominant pattern of this submission:

| Form | Current Y/N/M | Desired Y/N/M |
|---|---|---|
| Claim Representation Structure | 3/2/0 | 3/1/1 |
| Reified Claim Semantics | 3/1/0 | 3/1/0 |
| Evidence Item Types | 9/11/0 | 9/11/0 |
| Evidence Interpretation | 9/3/0 | 9/0/3 |
| Provenance Types | 8/34/1 | 24/9/10 |
| **Total** | **32/51/1** | **48/22/14** |

Everything the project knows about how a file came to exist — which agent and model, which
extraction-skill version, which human directed and reviewed it, on what date, against a full-text
or abstract-only cached copy, verified or not — lives in skills, receipts, CI configuration and
pull-request history, and none of it is readable from the data. Closing that gap is the project's
leading desired-state requirement and is a `soma` schema change independent of SEPIO.

## Open questions for the project representative

Listed in full in §6 of the Review Memo, in descending order of value. In brief: how far the
desired per-file provenance block should reach across SEPIO's provenance levels; whether
`EI.CUSTOM.001` (verbatim quoted source passage) is the right call or should fold into `FREE_TEXT`
on the content rows; whether evidence grouping and stacking should be adopted for AOP claims;
whether any confidence value should be represented at all, given that the asserting agent is
usually an AI agent; whether measurement claims should be reified; whether six claim types or four;
and the representative and submission boundary.

Fourteen rows across the workbook are marked `M` pending those decisions, which is the mechanism
the guidance prescribes — a partially completed workbook with clearly marked unknowns is preferable
to a fully populated one containing inferred requirements.

## Highest-priority feedback to the consortium

1. **No provenance area for mechanical verification of an evidence item against a stored source
   copy.** This is SOMA's central trust mechanism, enforced corpus-wide in CI, and it is
   inexpressible in the current forms. `PROV.SA.REVIEW` covers human review of an alignment;
   `PROV.EI.QUALITY` covers the rigour of the source study. Neither covers "this quote was checked
   word-for-word against a cached copy of the cited publication by this tool on this date, and the
   copy was full text."
2. **The five provenance levels cannot be declared coincident.** In a single-pass AI curation
   workflow, semantic alignment, interpretation, assertion and encoding are one activity by one
   agent at one time, so about sixteen rows want the same three values with no way to say so. This
   will recur for every AI-assisted curation project in the consortium.
3. **No within-source locus provenance.** SOMA records which section of a publication a quote came
   from and which figure or table reports the data, and treats the distinction as load-bearing. The
   guidance's own worked example cites "the location of the passage in the text" as an input to
   interpretation, but no form row collects it.
4. **No evidence item type names a quoted source passage**, so a literature-extraction project's
   primary evidence unit has to be a custom row.
