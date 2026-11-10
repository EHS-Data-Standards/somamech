# SOMA Resource Inventory / Evidence Package

Prepared for the SEPIO consortium's Evidence, Provenance and Confidence (EPC) requirements
collection, following `RESOURCE_INVENTORY_GUIDANCE.md`.

- **Project:** SOMA — schema repository `EHS-Data-Standards/soma`; knowledge base and tooling
  repository `EHS-Data-Standards/somamech`
- **Run:** `SOMA-20261109-R01`
- **Prepared:** 2026-11-09
- **Prepared by:** AI requirements agent (Claude Code), directed by Sierra Taylor Moxon (LBNL)
- **Status:** drafted by agent; **awaiting project representative review**

> Both repositories state that the majority of their content is AI-generated and that a human name
> on a commit, pull request or knowledge-base entry denotes direction and review rather than
> authorship. This inventory was likewise drafted by an agent and needs human confirmation.

## 1. Selected scope statement

> The project is the SOMA native knowledge model and its per-publication Container YAML knowledge
> base. Current-state requirements must reflect what the canonical `kb/publications/*.yaml` files
> and the installed `soma-schema` release actually represent. Desired-state requirements may be
> informed by the broader SOMA project evidence base: the extraction and review skill definitions,
> the snippet-verification receipts and tooling, the committed reference cache, the generated
> query and review products, and the repository's own documentation of its AI-assisted curation
> workflow. Upstream publication sources (PubMed/PMC), external ontologies, and the generated
> DuckDB/TSV/workbook export products are out of scope as canonical current-state sources, except
> where explicitly cited below as desired-state support.

This is the **maximal** scope option from `RESOURCE_INVENTORY_GUIDANCE.md`, selected by the project
representative on 2026-11-05.

**Why maximal rather than minimal.** The canonical YAML carries exactly one provenance slot
(`source_publication`). Under a minimal scope the project would answer "no" to roughly thirty
provenance rows for which it demonstrably has the information, recorded in skills, receipts, CI
configuration and pull-request history. A minimal scope would have been accurate and badly
misleading.

**A third scope was considered and set aside.** SOMA has two legitimate products: the YAML
knowledge base and the generated DuckDB/TSV/Excel exports, which flatten evidence differently. If
the consortium cares about the queryable product, that deserves its own scope and a separate
requirements pass. It is not part of this submission.

## 2. Current-state canonical source set

These, and only these, controlled the F1 / current-state column.

| Source ID | Name | Type | Location | Version | Role |
|---|---|---|---|---|---|
| **S01** | SOMA publication knowledge base | Canonical dataset, 41 YAML files | `somamech:kb/publications/*.yaml` | commit `d8f40d9` (branch `main`), retrieved 2026-11-05 | `CURRENT_STATE_CANONICAL` |
| **S02** | soma-schema LinkML schema | Schema source | `soma:src/soma/schema/{soma,evidence,assay_base,aop_framework,assay_microschemas,publication_stub}.yaml` | `soma-schema` 0.2.4 (installed release) | `CURRENT_STATE_CANONICAL_COMPANION` |

S02 is designated a canonical companion because the YAML data files cannot be interpreted without
the schema that defines their slots, enums and validation annotations. Together S01 and S02 are the
data product and its data dictionary.

**Key observed facts.**

- `Container` (the tree root) carries `source_publication` plus entity collections. It has no
  agent, date, model, method or version slot of any kind.
- Four classes carry an `evidence` list: `Assay`, `AssayOutputMeasurement`, `KeyEvent`,
  `KeyEventRelationship`.
- `EvidenceItem` has eight slots: `reference`, `reference_title`, `supports`, `evidence_source`,
  `snippet`, `explanation`, `article_section`, `figure_reference`.
- `snippet` declares `implements: linkml:excerpt`; `reference` declares
  `implements: linkml:authoritative_reference`; `reference_title` declares `implements: dcterms:title`.
  These annotations are what make the quote and title machine-checkable.
- Direction vocabulary: `SUPPORT` (1312 uses), `REFUTE` (23), `NO_EVIDENCE` (1). One item has an
  empty value; the slot is not required.
- `KeyEventRelationship` carries `evidence_support` (strong/moderate/weak/not_specified) and
  `quantitative_understanding` (high/moderate/low/not_specified) as slots on the relationship.
- `ResponseComparison` carries `derivation` (`reported_in_paper`, 400 uses / `computed`),
  `p_value`, `statistical_test`, and a `change_value` with `confidence_interval_95` bounds.
- No slot anywhere carries an epistemic confidence value. The only `confidence_interval_*` fields
  are statistical dispersion on measurements.

## 3. Desired-state evidence set

Used only for the F2 / desired-state column, with the support type recorded in each form's
explanation field.

| Source ID | Name | Location | Desired-state support type | Informs |
|---|---|---|---|---|
| **S03** | Paper-extraction skill | `somamech:.claude/skills/claim-paper/SKILL.md` | `EXISTING_PROJECT_CAPABILITY_NOT_IN_CANONICAL_EXPORT` | Semantic alignment, interpretation and assertion provenance |
| **S04** | Extraction PR review checklist | `somamech:.claude/skills/extraction-pr-review/SKILL.md` | `EXISTING_PROJECT_CAPABILITY_NOT_IN_CANONICAL_EXPORT` | Human review / validation status |
| **S05** | Snippet verification receipts and tooling | `somamech:verification/*.json`, `scripts/snippet_receipts.py` | `EXISTING_PROJECT_CAPABILITY_NOT_IN_CANONICAL_EXPORT` | Verification state, cache content type, retrieval date |
| **S06** | QC recipes and CI configuration | `somamech:project.justfile` (`validate-all`, `check-receipts`, `qc`), `.github/workflows/main.yaml` | `EXISTING_PROJECT_CAPABILITY_NOT_IN_CANONICAL_EXPORT` | What is mechanically enforced, and over what scope |
| **S07** | Committed reference cache | `somamech:references_cache/*.md` | `EXISTING_PROJECT_CAPABILITY_NOT_IN_CANONICAL_EXPORT` | Retrieval provenance; per-paper cache content type |
| **S08** | DuckDB / TSV query products | `somamech:scripts/soma_duckdb.py`, `README.md` query section | `EXISTING_PROJECT_CAPABILITY_NOT_IN_CANONICAL_EXPORT` | Edge-shaped access; record keying rationale |
| **S09** | Per-paper review site | `somamech:scripts/build_site.py`, `scripts/site_templates/` | `DOCUMENTED_MODEL_INTENT` | Which evidence fields are surfaced to a human reader |
| **S10** | Repository AI-generated content notice | `somamech:README.md` | `DOCUMENTED_MODEL_INTENT` | That content is AI-authored and humans direct and review |
| **S11** | Ontology grounding tooling and report | `somamech:ontology_grounding_report.tsv`, `scripts/run_term_validator.sh`, `scripts/generate_ontology_mappings.py` | `EXISTING_PROJECT_CAPABILITY_NOT_IN_CANONICAL_EXPORT` | Semantic alignment method types and specifications |
| **S12** | Git history and pull-request records | `somamech` repository history | `EXISTING_PROJECT_CAPABILITY_NOT_IN_CANONICAL_EXPORT` | Agent, date and reviewer for every file |

### Sources considered and excluded

| Source | Why excluded |
|---|---|
| PubMed / PubMed Central | Upstream publication source. Provides the content SOMA quotes, not evidence of SOMA's own requirements. `CONTEXT_ONLY`. |
| GO, ChEBI, CL, UBERON, MONDO, HPO, UO, ENVO, OBI | External terminological artifacts. SOMA aligns to them; they are not evidence of SOMA's EPC requirements. `CONTEXT_ONLY`. |
| `corpus.csv` and the paper queue | Work-management state (which papers are claimed or extracted). Says nothing about evidence representation. `CONTEXT_ONLY`. |
| Generated `exports/` artifacts | Gitignored, rebuilt on demand, never hand-edited. Their builders (S08) are cited instead. |

## 4. Representative examples

| Example ID | State | Source | Requirement pattern demonstrated |
|---|---|---|---|
| **E01** | Current | S01 — `Container-ghosh2025-pm25-egfr-pi3k-akt.yaml`, evidence item on `LF:ghosh-pm25-seasonal-spirometry` | A verbatim quoted table row as the unit of evidence, carrying direction, article section, figure label and curator explanation — content and interpretation fused in one object |
| **E02** | Current | S01 — same file, `LF:...-output-spring` | A measurement claim as an implicit slot/value on a parent record, with a nested `QuantityValue` carrying unit, central tendency, sample size and variability |
| **E03** | Current | S01 — same file, `KER:ghosh-pi3k-akt-to-suppressed-apoptosis` | A reified subject-predicate-object claim with a categorical weight-of-evidence judgement asserted on the claim rather than on an interpreted argument |
| **E04** | Current | S01 — same file, `COMP:ghosh-lf-fev1fvc` | A reified comparison claim with structured statistical metrics, a 95% confidence interval, and `derivation` recording that the value was reported by the authors |
| **E05** | Desired | S05 — `verification/PMID_32783621.json` | Verification provenance: tool, date, cache content type (`abstract_only`) and per-snippet SHA-256 hashes — recorded outside the canonical data |
| **E06** | Current | S01 — same file, `EXPOSURE:ghosh-pm25-spring` | An exposure condition grounded to an ontology term (`ENVO:01000415`) with concentration and duration, as the context that makes a measurement claim interpretable |

`Container-ghosh2025-pm25-egfr-pi3k-akt.yaml` was chosen as the primary example file because it is a
deliberately hard case: its molecular results appear only in figures, so by project rule those
output records carry no quantity values at all, which exercises the figure-reference mechanism and
the distinction between a described direction and a measured value.

## 5. Conflicts, gaps and access notes

- **No conflicts found between S01 and S02.** The schema and the data agree; CI enforces that.
- **Scope boundary requiring care.** S05, S06, S07 and S12 describe real, enforced project
  capabilities that are *absent from the canonical data*. The temptation to mark the corresponding
  provenance rows as current must be resisted: they are desired-state support only. This was the
  single largest source of potential F1 error in this review.
- **One data observation for project follow-up.** One evidence item in the corpus has an empty
  `supports` value. The slot is not required by the schema, so this is not a validation failure,
  but it is likely an extraction oversight.
- **Access.** All sources are public and were retrieved directly. No human upload was required.
- **Moving-source caveat.** Both repositories were read at `main` rather than at a pinned release.
  The `somamech` commit SHA is recorded above; `soma` was read via the installed `soma-schema`
  0.2.4 release, which is version-pinned.
