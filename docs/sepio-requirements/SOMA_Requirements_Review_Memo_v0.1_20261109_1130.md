# SOMA Requirements Review Memo

**Project:** SOMA — `EHS-Data-Standards/soma` (schema) and `EHS-Data-Standards/somamech`
(knowledge base and tooling)
**Version:** v0.1 · **Date:** 2026-11-09 1130 · **Run:** `SOMA-20261109-R01`
**Workbook:** `SOMA_Requirements_v0.1_20261109_1130.xlsx`
**Prepared by:** AI requirements agent (Claude Code), directed by Sierra Taylor Moxon (LBNL)

> **This is an agent-prepared first pass and remains a draft until the project representative
> validates it.** Section 6 lists the answers that most need human confirmation.

---

## 1. Project scope used

> The project is the SOMA native knowledge model and its per-publication Container YAML knowledge
> base. Current-state requirements reflect what the canonical `kb/publications/*.yaml` files and the
> installed `soma-schema` release actually represent. Desired-state requirements may be informed by
> the broader SOMA project evidence base: the extraction and review skill definitions, the
> snippet-verification receipts and tooling, the committed reference cache, the generated query and
> review products, and the repository's own documentation of its AI-assisted curation workflow.
> Upstream publication sources (PubMed/PMC), external ontologies, and the generated
> DuckDB/TSV/workbook export products are out of scope as canonical current-state sources, except
> where explicitly cited as desired-state support.

This is the **maximal** scope from `RESOURCE_INVENTORY_GUIDANCE.md`, selected by the project
representative on 2026-11-05.

**Current-state canonical source set:** S01, S02 (see §3).
**Desired-state evidence set:** S03–S12 (see §4).

## 2. Requirements-workflow materials used

All retrieved directly from `sepio-framework/sepio-linkml` at `main` on 2026-11-05:

- `Requirements_Collection_Forms.xlsx` (SHA-256 `22e6c85a…`) — populated as the template
- `Requirements_Instructions_and_Guidance_for_AI.md` (SHA-256 `8a39ffdb…`)
- `REQUIREMENTS_FORM_PROMPT.md`, `RESOURCE_INVENTORY_PROMPT.md`,
  `RESOURCE_INVENTORY_GUIDANCE.md`, `QUICK_START.md`, `Requirements_Collection_Overview.md`,
  `CONTENTS.md`
- `examples/example_scope_statement.md`, `examples/example_completed_requirements_review.md`
- `Feedback_Log_Template.xlsx` (SHA-256 `73a85a29…`) — used for the accompanying feedback log

The Requirement → SEPIO Mapping Registry was **not** used, per rule 33. The workbook's
`SEPIO Mapping Summary` columns were not edited and were not used to decide any answer; this was
verified programmatically after population (all five mapping columns are byte-identical to the
template).

## 3. Sources used for current-state (F1) requirements

| ID | Source | Version / retrieval |
|---|---|---|
| **S01** | `somamech:kb/publications/*.yaml` — 41 Container files | commit `d8f40d9`, branch `main`, retrieved 2026-11-05 |
| **S02** | `soma:src/soma/schema/*.yaml` — `soma`, `evidence`, `assay_base`, `aop_framework`, `assay_microschemas`, `publication_stub` | `soma-schema` 0.2.4 (pinned, installed release) |

**S02 is an explicitly designated canonical companion artifact.** The YAML data files cannot be
interpreted without the schema that defines their slots, enumerations and validation annotations;
together they are the data product and its data dictionary. No capability was marked current on the
basis of the schema alone where the data does not use it — every F1 `Y` was checked against actual
records.

## 4. Sources used for desired-state (F2) requirements

Grouped by support type.

**`EXISTING_PROJECT_CAPABILITY_NOT_IN_CANONICAL_EXPORT`** — the project captures or enforces this
today, outside the canonical data:

- **S03** `.claude/skills/claim-paper/SKILL.md` — the extraction procedure an AI agent follows
- **S04** `.claude/skills/extraction-pr-review/SKILL.md` — the review checklist gating every PR
- **S05** `verification/*.json` and `scripts/snippet_receipts.py` — verification receipts recording
  tool, date, cache content type and per-snippet SHA-256 hashes
- **S06** `project.justfile` (`validate-all`, `check-receipts`, `qc`) and
  `.github/workflows/main.yaml` — what is mechanically enforced, repository-wide, on every run
- **S07** `references_cache/*.md` — the committed publication text quotes are verified against,
  carrying a per-paper `content_type`
- **S08** `scripts/soma_duckdb.py` and the README query section — edge-shaped access and the
  rationale for keying records on source file rather than cited publication
- **S11** `ontology_grounding_report.tsv`, `scripts/run_term_validator.sh`,
  `scripts/generate_ontology_mappings.py` — grounding and term-validation tooling
- **S12** git history and pull-request records — agent, date and reviewing human per file

**`DOCUMENTED_MODEL_INTENT`**:

- **S09** `scripts/build_site.py` and `scripts/site_templates/` — which evidence fields the project
  chooses to surface to a human reader
- **S10** `somamech:README.md` — the statement that the majority of content is AI-generated and
  that a human name on a commit denotes direction and review rather than authorship
- **S02** (also used for F2) — slot documentation stating *why* a distinction exists, e.g. that a
  value quoted from Results carries more weight than one quoted from Methods storage boilerplate

**Considered and excluded from desired-state reasoning:** PubMed/PMC (upstream source),
external ontologies (terminological artifacts SOMA aligns to), `corpus.csv` and the paper queue
(work-management state), and the gitignored `exports/` artifacts (their builders are cited instead).
No source was used that the selected scope does not permit.

## 5. High-confidence conclusions

**Claim representation.**

1. SOMA uses three claim representation structures, not one. Measurement, key-event, assay-method
   and exposure claims are **implicit slot/values and nested objects on parent records**; comparison
   claims (`ResponseComparison`) and key-event-relationship claims (`KeyEventRelationship`) are
   **genuinely reified first-class objects** with their own identifiers and their own evidence lists.
   No graph-edge representation exists in the canonical data.
2. Where claims are reified, they carry structured proposition semantics **directly on the claim
   object** using project-specific field names (`upstream_event` / `relationship_type` /
   `downstream_event`; `compared_measurement` / `change_direction` / `change_value`). There is no
   separate Proposition object and the project has no use case for one.
3. Qualifying context is a hard requirement, not an enhancement. An environmental-health
   measurement claim is uninterpretable without its exposure condition and experimental group.

**Evidence.**

4. The project's unit of evidence is the **verbatim quoted source passage**. One `EvidenceItem`
   holds the quote, the cited publication and title, the article section, the figure or table label,
   the direction of support, and a curator explanation — evidence content and evidence
   interpretation fused in a single flat object, with no grouping of items into arguments.
5. That flat form is an **intentional implementation preference** and the project requires it
   preserved for five of its six claim types: the extraction agents emit it, the validators check
   it, and the DuckDB builder, pooled workbook and review site all read it.
6. Nine of twenty inventoried evidence item types are represented; eleven are not. The project
   extracts from publication text and figures, so it represents no datasets, no external database
   records, no structured prior claims, no computational predictions and no images.
7. Statistical metrics are **structured content**, not merely quoted text: p-values, test names,
   confidence-interval bounds and dispersion types are first-class fields.
8. Disputing evidence is genuinely represented, not merely permitted: `REFUTE` occurs 23 times
   across the corpus, alongside 1312 `SUPPORT` and one `NO_EVIDENCE`.
9. `NO_EVIDENCE` is **not** a neutral direction. It records that a source was consulted and found
   not to bear on the claim — a statement about relevance, not about the balance of evidence.

**Evidence interpretation.**

10. The claim types do **not** share one evidence model. Five share a flat per-item profile with
    direction only; key-event-relationship claims need a categorical weight-of-evidence judgement
    over a *group* of evidence items, drawn from the OECD AOP framework. A SEPIO-based
    representation needs both, selected per claim type.
11. Categorical evidence strength is represented, but **on the claim object** rather than on an
    interpreted argument, with no link to the evidence items that justify it. A reading that
    expected strength on a per-argument judgement would wrongly conclude "not represented".

**Provenance.**

12. **The canonical data contains no provenance beyond the cited publication.** `Container` has
    exactly one provenance slot, `source_publication`. There is no agent, date, model, method or
    version field anywhere in 41 files. This produces the dominant pattern of this review: current
    provenance answers are 8 `Y` / 34 `N` / 1 `M`, while desired answers are 24 `Y` / 9 `N` / 10 `M`.
13. Evidence-*item* provenance — how the source study produced the measurements — is by contrast
    well represented: typed protocols with published standards followed, detection and normalisation
    methods, instruments, antibodies with dilutions, equipment, and model systems.
14. `evidence_source` (human clinical / model organism / in vitro / computational / other) is
    required on every evidence item and classifies **the cited publication's study type, not the
    extracting agent** — a distinction the schema states explicitly and which matters here because
    every file is AI-extracted.
15. `ResponseComparison.derivation` (`reported_in_paper` / `computed`) is a genuine piece of
    **assertion-method provenance already in the data**: it tells a consumer whether a number is the
    authors' or the project's. The project regards this as more informative than a confidence score.
16. The project's central quality control is **mechanical verification of evidence against a stored
    source copy**, enforced corpus-wide in CI: every snippet must appear word-for-word in the
    committed cache, and `reference_title` must match the real publication title. Where a publisher
    blocks full-text caching, `check-receipts` requires a committed receipt of per-snippet SHA-256
    hashes, making a missing receipt or an edited quote a hard failure. **No provenance row in the
    forms can express this**, which is the project's most significant feedback to the consortium.

## 6. Answers requiring human review

Listed in descending order of value.

1. **Should extraction provenance enter the canonical data, and how far should it reach?**
   The representative has decided *yes, as the leading desired-state requirement* (agent, model,
   skill version, human director and reviewer, extraction date, cache content type, verification
   status). What remains unresolved is how far across SEPIO's provenance levels the block should
   extend. `PROV.ENCODING.AGENT`, `.DATE` and `.SYSTEM` are marked `M` for this reason;
   `PROV.ENCODING.VERSION` is marked `Y` because the project already pins a schema version and a
   consumer needs to know which slot set a record was authored against.

2. **Is `EI.CUSTOM.001` (Verbatim Quoted Source Passage) the right call?** We added it because the
   quoted passage is the project's unit of addressability and the thing that is verified, and
   because the verification requirement attaches to the passage rather than to the content it
   reports. But it cross-cuts four content rows that are also marked `Y`. The alternative is to
   drop it and rely on `FREE_TEXT` as the local representation form of those rows. The
   representative should decide; this choice also determines whether the last column of the
   claim-evidence matrix survives.

3. **Should evidence grouping and stacking be adopted for key-event-relationship claims?**
   `EINT.GROUPING` and `EINT.STACKING` are both marked `M`. The project has the ingredients — every
   evidence item is already classified by study kind, and the AOP framework weighs those kinds
   differently — but no project document states the requirement, and the choice between "three
   quotes from one paper as three arguments" and "as three premises of one argument" is unmade.

4. **Should any confidence value be represented at all?** Four rows are marked `M` on this basis:
   `PROV.SA.CONFIDENCE_CATEGORY`, `PROV.SA.CONFIDENCE_SCORE`,
   `PROV.ASSERTION.CONFIDENCE_CATEGORY`, and `EINT.NUMERICAL_STRENGTH`. The project's provisional
   view is that all should be `N`: the asserting and aligning agent is usually an AI agent, so a
   confidence value would largely be model self-report, and the project prefers mechanical
   verification over claimed confidence wherever a check is possible.
   `PROV.ASSERTION.CONFIDENCE_SCORE` is marked `N` outright because the project has a reasoned
   position against it, not merely an absence of evidence.

5. **Should measurement claims (C001) be reified?** `CS.REIFIED_OBJECT` is `Y`/`Y` because two
   claim types already are reified. Whether the most numerous claim type should join them is open:
   reification would allow per-proposition evidence and provenance but would change the file shape
   the extraction agents emit and every generated product consumes. Recorded in
   `CS.REIFIED_OBJECT` F3 as a question, not a requirement.

6. **Six claim types or four?** The representative chose six, reporting assay-method (C005) and
   exposure-condition (C006) claims in their own right. Their evidence and provenance requirements
   are identical to C001, which the guidance would normally treat as grounds for merging. The six
   are reported as directed, with the shared profile stated in each row's notes. If the consortium
   prefers the minimal set, C005 and C006 fold into C001 as qualifying context.

7. **Project representative and submission boundary.** One submission is reported covering both
   repositories, named for the schema. Confirm whether additional representatives should be named
   and whether a split submission is preferred.

8. **Two smaller items.** Whether measurement dates and study locations should be structurally
   represented (`PROV.EI.DATE`, `PROV.EI.LOCATION`, both `M`) — both matter in environmental health,
   where exposure is seasonal and place-specific, but neither is currently a stated requirement.

## 7. Apparent conflicts or missing information

- **No conflicts were found between the canonical data (S01) and the schema (S02).** CI enforces
  their agreement, and direct inspection confirmed it.
- **The principal risk in this review was scope leakage, not conflict.** S05, S06, S07 and S12
  describe real, enforced capabilities that are absent from the canonical data. Every one of them
  was recorded as desired-state support only; none was allowed to raise an F1 answer. This was
  checked explicitly in the consistency pass.
- **One data defect for project follow-up:** one evidence item in the corpus has an empty
  `supports` value. The slot is not required by the schema, so this is not a validation failure, but
  it is likely an extraction oversight.
- **No documented evidence-strength framework exists** for the five non-AOP claim types. The project
  records direction without strength, and no project source describes an intended strength model.
  This is an absence rather than a conflict, and it is reported as such rather than filled in.
- **Missing information the project does not have:** nothing records which agent or model produced
  any given file beyond git history, so the desired-state provenance requirement describes a
  capability to be *built*, not one to be *exported*. We have not assumed a particular agent or
  model identifier.

## 8. Files or resources the agent could not access

None. All ten SEPIO requirements-collection files, both binary workbooks and both project
repositories were retrieved directly and read in full. No human upload was required.

## 9. Form or guidance questions that were difficult to interpret

Summarised here; actionable proposals are in the accompanying feedback log.

1. **The five provenance levels assume distinct activities.** In a single-pass AI extraction
   workflow, semantic alignment, evidence interpretation, assertion and encoding are performed by
   one agent, in one activity, at one time. Filling four levels × agent/method/date produces about
   sixteen rows that all want the same three values, and the forms provide no way to state that the
   levels coincide. We answered each row on its merits and noted the collapse in the explanations.
2. **`EIT` F5 (individual addressability) is ambiguous when the addressable unit sits at a
   different granularity from the item type.** For SOMA an individual measurement is *not*
   separately addressable, but the quoted passage reporting it *is*. Answering per row forces a
   choice that misreports one or the other; this is part of why `EI.CUSTOM.001` was added.
3. **Whether a document is an evidence item.** The guidance states that SEPIO treats documents as
   sources that *contain* evidence items rather than as evidence items themselves, while the form
   presents them as evidence item rows. We marked `EI.DOCUMENT.SCIENTIFIC_PUBLICATION` as `Y` on the
   understanding that the requirement is to represent the publication as the source of its evidence
   items, and said so in the row.
4. **Claim types whose claims are implicit.** The Claim Type form asks for subject category, object
   category and relationship type, which presupposes claims shaped like associations. For SOMA's
   most numerous claim type the proposition is implicit in a parent record plus its slot values, so
   enumerating claim types was a modelling act rather than a reporting act. The guidance's allowance
   for broad categories helped, but the forms have no way to mark a claim type as reconstructed.
5. **The claim-evidence matrix could not be completed in place.** Its Excel Table spans `A3:F9`,
   giving five evidence columns and six claim rows; SOMA needs nine evidence columns. Resizing the
   table conflicts with the formatting-preservation rules, so the SOMA matrix was written below the
   template's example, starting at row 12, clearly labelled.

## 10. Important assumptions made

1. **The schema is a canonical companion, not a separate source.** Required, since the data is
   uninterpretable without it. Stated in the scope.
2. **A capability was marked current only if actual records use it**, not merely because the schema
   permits it. Where a schema slot exists but no record populates it, the row reflects the data.
3. **Narrative free text counts as representation where the information is genuinely captured**
   (e.g. `PROV.EI.EXECUTION` is `Y` because protocol descriptions carry execution detail), but the
   unstructured nature is stated in the explanation. This is a judgement the representative may
   wish to reverse toward `M`.
4. **Generated export products are not canonical.** Their builders were cited as desired-state
   support where they reveal a project interest, never as evidence of current representation.
5. **The project representative is recorded as Sierra Taylor Moxon (LBNL)**, pending confirmation.
6. **`derivation` is assertion-method provenance.** We read `reported_in_paper` / `computed` as a
   statement about how the asserted value was arrived at, which makes
   `PROV.ASSERTION.METHOD_TYPES` an F1 `Y`. An alternative reading treats it as a property of the
   value rather than of the assertion; flagged in that row.
7. **No agent or model identifier was invented** for the desired-state provenance block. The rows
   describe what must be representable, not a specific value.

## 11. Project observations suggesting improvements to the forms or guidance

Fourteen observations are recorded in
`SOMA_Requirements_Feedback_Log_v0.1_20261109_1130.xlsx` (agent columns A–V; governance columns
W–AD left for the consortium). The highest-priority four:

- **No provenance area for mechanical verification of an evidence item against a stored source
  copy.** This is SOMA's central trust mechanism and it is inexpressible in the current forms.
  `PROV.SA.REVIEW` covers human review of an alignment; `PROV.EI.QUALITY` covers the rigour of the
  source study. Neither covers "this quote was checked word-for-word against a cached copy of the
  cited publication by this tool on this date, and the copy was full text."
- **The five provenance levels cannot be declared coincident.** See §9.1. This will recur for every
  AI-assisted curation project in the consortium.
- **No within-source locus provenance.** SOMA records which section of a publication a quote came
  from and which figure or table reports the underlying data, and treats the distinction as
  load-bearing. The guidance's own worked example mentions "the location of the passage in the text"
  as an input to interpretation, but no form row collects it.
- **No evidence item type names a quoted source passage.** The two text-passage rows are both
  scoped to passages reporting a *prior claim*. A quoted table row reporting numbers is neither a
  prior claim nor cleanly a data item when what the project stores and verifies is the text. The
  guidance's allowance for selecting multiple types and the `FREE_TEXT` representation form together
  make this answerable, but a project's primary evidence unit having to be a custom row costs
  cross-project comparability.

## 12. Representative data examples

### E01 — Current state · one complete evidence item
*Source: S01, `kb/publications/Container-ghosh2025-pm25-egfr-pi3k-akt.yaml`,
`lung_function_assays[0].evidence[0]`*
*Demonstrates: the project's unit of evidence — content and interpretation fused, with
within-source locus.*

```yaml
- reference: "PMID:41469766"
  reference_title: "Seasonal impact of PM(2.5) on pro-oncogenic drivers among participants of a thermal power plant in India."
  supports: SUPPORT
  evidence_source: HUMAN_CLINICAL
  snippet: "FEV1/FVC (measured) 90.06±6.19 84.32±3.86 0.00"
  explanation: "Table 3 row giving the measured FEV1/FVC values this assay records for the monsoon and spring visits, with the paired t-test p-value."
```

### E02 — Current state · an implicit measurement claim
*Source: S01, same file, `LF:ghosh-pm25-seasonal-spirometry-output-spring`*
*Demonstrates: `CS.PARENT_SLOT_VALUE` — the subject is the parent record, the relationship is the
named slot, the object is a nested `QuantityValue`.*

```yaml
- id: "LF:ghosh-pm25-seasonal-spirometry-output-spring"
  experimental_group: treated
  measured_under: "EXPOSURE:ghosh-pm25-spring"
  fvc:
    value: "2.92"
    unit: {id: "UO:0000099", name: "liter"}
    central_tendency: mean
    sample_size: 33
    variability:
      variability_type: standard_deviation
      value: "0.58"
      unit: {id: "UO:0000099", name: "liter"}
```

### E03 — Current state · a reified claim with strength on the claim
*Source: S01, same file, `key_event_relationships[0]`*
*Demonstrates: `CS.REIFIED_OBJECT` + `RCS.STRUCTURED_STATEMENT`, and
`EINT.CATEGORICAL_STRENGTH` asserted on the claim with no link to the items that justify it.*

```yaml
- id: "KER:ghosh-pi3k-akt-to-suppressed-apoptosis"
  name: "PI3K/AKT pathway activation leads to suppressed apoptosis"
  upstream_event: {id: "KE:ke-pi3k-akt-activation", name: "PI3K/AKT pathway activation", biological_action: activated, level_of_biological_organization: molecular}
  downstream_event: {id: "KE:ke-suppressed-apoptosis", name: "Suppressed apoptosis", biological_action: decreased, level_of_biological_organization: cellular}
  relationship_type: "indirectly leads to"
  evidence_support: moderate
  evidence: [ ... two evidence items ... ]
```

### E04 — Current state · structured statistical metrics and assertion method
*Source: S01, same file, `response_comparisons[0]`*
*Demonstrates: `EI.DATA.STATISTICAL_METRIC` as structured content, and
`PROV.ASSERTION.METHOD_TYPES` via `derivation`.*

```yaml
- id: "COMP:ghosh-lf-fev1fvc"
  description: "LMER beta estimate: every 10 ug/m3 increase in PM2.5 decreased the measured FEV1/FVC ratio by 2.62 percentage points."
  compared_measurement: "fev1_fvc_ratio"
  control_output: "LF:ghosh-pm25-seasonal-spirometry-output-monsoon"
  treated_output: "LF:ghosh-pm25-seasonal-spirometry-output-spring"
  change_type: absolute_difference
  change_direction: decreased
  change_value:
    value: "-2.62"
    unit: {id: "UO:0000187", name: "percent"}
    variability:
      variability_type: confidence_interval_95
      lower_bound: "-3.68"
      upper_bound: "-1.56"
  derivation: reported_in_paper
```

### E05 — Desired state · verification provenance, currently outside the canonical data
*Source: S05, `verification/PMID_32783621.json`*
*Demonstrates the provenance the forms cannot express (§11) and the desired cache-content-type
requirement (`PROV.RETRIEVAL.DATE`, `PROV.EI.RETRIEVAL_SOURCE`).*

```json
{
  "reference_id": "PMID:32783621",
  "kb_file": "kb/publications/Container-lkhagvadorj2020-prenatal-smoke-areg-egfr.yaml",
  "content_type_in_committed_cache": "abstract_only",
  "verified_with": "just verify-snippets (linkml-reference-validator, committed + local cache)",
  "verified_date": "2026-09-28",
  "snippet_sha256": ["007536f4...", "051f5889...", "… 15 hashes total"]
}
```

### E06 — Current state · exposure condition as claim context
*Source: S01, same file, `EXPOSURE:ghosh-pm25-spring`*
*Demonstrates `RCS.QUALIFIERS` — the context without which a measurement claim is
uninterpretable — and ontology grounding of the exposure agent.*

```yaml
- id: "EXPOSURE:ghosh-pm25-monsoon"
  name: "Ambient PM2.5 at the thermal power plant during summer-monsoon, Apr 2021-Aug 2021 (daily mean 23.39 ug/m3)"
  exposure_agent:
    id: "ENVO:01000415"
    name: "fine respirable suspended particulate matter"
```

---

## Source-access status

- **Successfully retrieved, directly, without human upload:** all ten files in
  `sepio-framework/sepio-linkml/docs/requirements-collection` at `main`, including both binary
  workbooks (`Requirements_Collection_Forms.xlsx`, `Feedback_Log_Template.xlsx`) and both
  `examples/` documents. The workbook was downloaded as an actual XLSX and populated as the
  template, not reconstructed from a rendered preview.
- **Project sources:** both repositories were read from local working copies of
  `EHS-Data-Standards/somamech` (commit `d8f40d9`) and `EHS-Data-Standards/soma`
  (`soma-schema` 0.2.4).
- **Version pinning:** the SEPIO materials were read from the moving `main` branch; their SHA-256
  hashes are recorded in §2 and in `CONTENTS.md`. `somamech` is identified by commit SHA and
  `soma-schema` by release version, so the project side of this review is reproducible.
- **Attached files used:** none. No fallback human upload was required.
- **Public resources that could not be retrieved:** none.

## Workbook handling

The returned workbook was produced by editing the sheet XML inside the supplied template's own
container and copying every other part byte-for-byte, because the template carries Excel Tables,
drawings, VML drawings and legacy comments that common Python spreadsheet libraries do not
round-trip faithfully. Result: **596 cells written across 8 sheets; 33 of the workbook's 41 parts
are byte-identical to the template**, including all styles, tables, drawings and comments. Only the
eight worksheet parts changed. No row, column, table range, validation rule or style was altered,
no field numbering was changed, and the `AI-Readiness Review Notes` sheet was left untouched. All
five `SEPIO Mapping Summary` columns were verified unchanged after population.

**One deviation from the template layout, declared:** the claim-evidence matrix is written below the
template's illustrative example (from row 12) rather than replacing it, because SOMA needs nine
evidence columns where the example's Excel Table provides five, and resizing that table would have
conflicted with the formatting-preservation requirement.
