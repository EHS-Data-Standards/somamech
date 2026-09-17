# Porting the dismech pattern into SOMA — implementation plan & tracker

> **Resume protocol (read first, every session):** This file is the single source
> of truth for standing up the dismech-style curation stack in SOMA. Before doing
> anything, read **Current state**, do the item under **Next action**, then update
> both. Check boxes as you go; a half-done phase is recorded as half-done.
>
> **What's being ported:** the *dismech* operating model — a LinkML schema + YAML
> content, gated by **offline deterministic validators**, curated by an **agentic
> loop** of Claude GitHub workflows backed by bot GitHub Apps and optional
> deep-research providers. SOMA already has the schema substrate; this port adds
> the validation gates, the agentic loop, and (optionally) research providers.

---

## Current state

> **REFRAMED 2026-09-14 (branch `somamech`):** the work queue is **publications
> to extract**, not diseases/EEPs. A paper-extraction pipeline was implemented
> (see the new section directly below). The EEP/AOP rebranding phases further
> down remain valid future work but are not the active track.

### Paper-extraction pipeline — what is DONE (2026-09-14)

- **Schema** (`src/soma/schema/`): `evidence.yaml` module — `EvidenceItem`
  (reference/reference_title/snippet/supports/evidence_source/explanation)
  with the `implements:` annotations that activate linkml-reference-validator;
  `evidence` attached to Assay, AssayOutputMeasurement, KeyEvent,
  KeyEventRelationship; `source_publication` on Container; term-checking
  enums (CellTypeTerm etc.) with bindings on cell_type / exposure_agent /
  anatomical_origin / model_species / unit slots. ChemicalEntityReference now
  also allows ENVO (PM2.5 is ENVO:01000415, not a CHEBI term — the validator
  caught the long-standing CHEBI:74481 mislabel and it is fixed in all data).
- **Validation stack**: linkml-term-validator + linkml-reference-validator in
  dev deps (Python floor now 3.10); `conf/oak_config.yaml`,
  `conf/reference_validator_config.yaml`; wrapper scripts in `scripts/`;
  recipes `validate-file`, `validate-all`, `verify-snippets`,
  `check-duplicate-keys`, `check-stubs`, `fetch-reference`,
  `extract-paper-text`, and `qc` (green offline); CI `qc` job + oak-cache
  action added to `.github/workflows/main.yaml`. Negative test committed:
  a doctored quote fails validation (tests/test_evidence_validation.py).
- **Queue**: `corpus.csv` (seeded with the 2 already-extracted papers) →
  `scripts/build_stubs.py` → `stubs/` (2 seed stubs, real PubMed metadata);
  stub schema `publication_stub.yaml`; `fetch-claims` / `next-unclaimed`
  recipes; `conf/pubmed_searches.tsv` (the 35 L1–L4 searches) +
  `scripts/search_pubmed.py` (open-access filter, dedupe, ranking).
- **Skills**: `/claim-paper` (claim issue → extract → verify → PR),
  `/fetch-and-curate` (keyword search, open-access only),
  `extraction-pr-review` (review checklist); `pdf-to-yaml` updated to require
  source_publication + evidence blocks and output to `kb/publications/`.
- **Workflows**: `claude.yml` (@claude responder, trusted-author gate),
  `claude-code-review.yml` (reviews via extraction-pr-review skill, verifies
  the agent actually ran), `agent-config.yaml` + resolve-agent-config action.
- **Copyright posture**: `references_cache/` holds only fetcher-produced
  abstracts/OA full text; `tests/publications/`, `examples/pdfs/` and
  `references_cache_local/` are gitignored (the 59 local PDFs are NOT the
  corpus and never get committed).

### Paper-extraction pipeline — manual setup still needed (user actions)

- [ ] Add the real `corpus.csv` publication list when available, then
      `just build-stubs`.
- [ ] Create labels: `claim`, `extraction`, `curation` (`gh label create ...`).
- [ ] Add Actions secret `ANTHROPIC_API_KEY` (or `CLAUDE_CODE_OAUTH_TOKEN`).
- [ ] Optional now, required for bot identity: create the writer GitHub App,
      install it, add `SOMA_AGENT_APP_ID` + `SOMA_AGENT_PRIVATE_KEY` secrets
      (the review workflow falls back to the Actions token until then).
- [ ] Branch protection on `main`: require review, dismiss stale reviews,
      require the `qc` check.
- [ ] First real dry run: `/claim-paper` on one open-access paper end-to-end.

### Deviations from the approved plan (deliberate)

- The three already-extracted papers stay in `tests/data/valid/` instead of
  moving to `kb/publications/` now: the Excel-converter tests reference them
  by path, and they don't yet carry full evidence coverage. They are seeded
  in `corpus.csv`, so the normal `/claim-paper` flow will promote them
  properly (full evidence blocks) as the first claims.

---

## Original port plan (EEP track — future work below this line)

- **Repo:** `EHS-Data-Standards/soma` (`../soma`, copier/LinkML scaffold)
- **Domain:** environmental toxicology & exposure biology
- **Native data model:** AOP-centric — `aop_framework.yaml` already defines
  `MolecularInitiatingEvent` → `KeyEvent` → `KeyEventRelationship` → `AdverseOutcome`
  → `AdverseOutcomePathway`, plus `stressors`, `target_molecule`, and OECD-style
  `EvidenceSupportEnum` / `QuantitativeUnderstandingEnum`. `assay_base.yaml` +
  `assay_microschemas.yaml` model assays that inform Key Events.
- **Atomic curated entity:** one YAML per **Exposure–Effect Pathway (EEP)** — the way
  dismech is one file per Disease. The AOP event chain is the *internal* model; "AOP" is
  not the product brand. Kept internally: `MolecularInitiatingEvent`, `KeyEvent`,
  `KeyEventRelationship`, `AdverseOutcome`. Renamed (output only): the top-level container
  `AdverseOutcomePathway` → `ExposureEffectPathway`.
- **Ontologies already bound (prefixes):** OBI, CHEBI, ENVO, PATO, UO, GO, CL,
  UBERON, HP, ECTO. `aopwiki_id` exists as a free-text slot.
- **Substrate:** [x] scaffold · [x] domain schema (AOP + assays) · [x] example content
  under `examples/` · [x] `ontology_grounding_report.tsv` started.
- **Greenfield (not started):** exact-quote evidence model · term/reference validators
  · `conf/oak_config.yaml` · committed caches · custom offline gates · all agentic
  workflows (`.github/workflows/` has only deploy-docs / pypi-publish / main).

### Next action
> Atomic entity + naming are locked (below). The remaining section-0 items are
> schema-detail decisions that can be made inside Phase A. **Start Phase A.**

### Decisions locked
- Domain = environmental toxicology & exposure biology. ✓
- Product/entity name = **Exposure–Effect Pathway (EEP)**. Internal event classes
  (MIE/KE/KER/AO) unchanged; only the top-level container class is renamed. AOP-Wiki
  stays a *cross-reference and import source*, never the product brand. ✓
- Agents self-merge? `<DECIDE — default: NO to start; review-assist only, humans merge>`.

---

## 0. Decisions to lock

- [x] **Atomic curated entity — LOCKED: one YAML per Exposure–Effect Pathway (EEP).**
      Internal chain stays MIE→KE→KER→AO; assays attach to Key Events. This is what `kb/`
      holds and what the foreign-key/causal checks resolve against.
- [x] **Where curated content lives — LOCKED:** `kb/pathways/*.yaml`. Keep `examples/` as
      illustrative; `kb/` is the validated corpus.
- [ ] **Exact-quote evidence model.** Adopt dismech's `EvidenceItem`
      (`reference` / `supports` / `evidence_source` / `snippet` / `explanation`). This is
      **orthogonal to** the existing `evidence_support` WoE enum — the enum grades a KER's
      weight of evidence (OECD tiers), the EvidenceItem attaches a *citable exact quote* to
      a specific claim. Both stay.
- [ ] **Reference namespaces + fetchers.** At minimum PMID + DOI. High-value structured
      sources for this domain: **AOP-Wiki** (`aop.events` KE/KER/AOP records — there is an
      `aop-wiki-cli` + skill already), **EPA CompTox** (DTXSID), **CTD** (chemical–gene–
      disease), **ECOTOX**, **PubChem** (CID). Each citable ID type needs a fetcher writing
      a deterministic `references_cache/<ID>.md`.
- [ ] **Ontologies to add + OAK adapters.** Have OBI/CHEBI/ENVO/PATO/UO/GO/CL/UBERON/HP/
      ECTO. Consider adding: **AOP-Wiki event IDs** (bind `aopwiki_id`), **MONDO** (adverse
      outcomes that are diseases), **NCBITaxon** (test species), **XCO** (experimental
      conditions), **ExO** (bundled with ECTO), **NCIT/DTXSID** for chemicals. Map each →
      `ols:<name>` (no local build) or `sqlite:obo:<name>` in a new `conf/oak_config.yaml`.
- [ ] **Dynamic enums (`reachable_from`).** Decide which slots get term-validated against a
      root: `biological_process`→GO, `occurs_in_cell_type`→CL, `occurs_in_anatomy`→UBERON,
      stressor/chemical→CHEBI, exposure→ECTO, adverse outcome→MONDO/HP. Add `meaning:` +
      dynamic enum bindings so `linkml-term-validator` can check them.
- [ ] **Self-merge?** If agents will merge their own PRs, the two-App writer/reviewer split
      (Phase E) is mandatory. For a standards repo starting out, default to **review-assist
      + human merge** (one writer App), add the reviewer App when curation volume grows.

---

## Phase A — schema: de-brand the output + add the dismech evidence/term machinery
*SOMA's internal event graph (MIE→KE→KER→AO) already maps onto dismech's pathograph. This
phase rebrands the curated product to **Exposure–Effect Pathway**, then adds the two things
the validators need: exact-quote evidence, and ontology-checkable term bindings.*

- [ ] Add an `EvidenceItem` class and hang `evidence[]` on Key Events, KERs, and any
      claim-bearing assay result. Keep the existing `evidence_support` WoE enum.
- [ ] Add ontology-bound descriptor pattern (`term: {id, label}` + free-text `preferred_term`,
      `label` == canonical ontology label) wherever a term is asserted.
- [ ] Add `reachable_from` dynamic enums for each term-validated slot (section 0).
- [ ] Add the reference-namespace prefixes (PMID, DOI, aop.events, DTXSID, …) to `soma.yaml`.
- [ ] **Rename the output class** `AdverseOutcomePathway` → `ExposureEffectPathway` (product
      de-brand). Leave `MolecularInitiatingEvent` / `KeyEvent` / `KeyEventRelationship` /
      `AdverseOutcome` untouched — they stay AOP-Wiki-aligned so crosswalks are clean.
- [ ] **Make AOP-Wiki a cross-reference, not the identity.** Replace the free-text
      `aopwiki_id` with a `mappings:` slot carrying entries like
      `{id: aop.events:AOP:1, predicate: skos:closeMatch}` (alongside CTD / CompTox /
      PubChem xrefs). AOP-Wiki becomes an import source + crosswalk, like PubMed — not the brand.
- [ ] Add intra-file foreign-key refs where the graph points at its own nodes (KER
      `upstream_event`/`downstream_event` already do this — formalize the `<kind>#<name>` or
      bare-name convention so the checks in Phase B can enforce it).
- **Done when:** a hand-written AOP entry in `kb/` passes `linkml-validate` **and**
  `linkml-term-validator`.

## Phase B — deterministic validation stack + committed caches
*The load-bearing phase. `just qc` must be green and network-free.*

- [ ] Add deps: `linkml-term-validator`, `linkml-reference-validator` (see dismech
      `pyproject.toml`); bump `oaklib`.
- [ ] Create `conf/oak_config.yaml` (ontology prefix → OAK adapter).
- [ ] Create `references_cache/` + a `just fetch-reference <ID>` recipe. **Never hand-write
      cache files.** Create `cache/<prefix>/terms.csv` + `cache/enums/*.csv`, populated by
      the term validator.
- [ ] Port the custom offline gates from dismech: duplicate-YAML-key check, entity-ref /
      causal-target foreign-key check, enum-value check, cache-integrity check. Run them
      **whole-repo, ungated** in CI (merge-of-two-green-PRs bugs escape path-gated checks).
- [ ] Add a `just qc` recipe bundling schema + term + reference + structural checks.
- **Done when:** `just qc` passes offline on a clean checkout, and CI runs it.

## Phase C — seed content + backlog queue
- [ ] Hand-curate 5–10 real Exposure–Effect Pathways into `kb/pathways/` (respiratory-tox
      examples already exist under `examples/` — ASL height, cilia beat, MCC, oxidative
      stress, lung function — good first candidates). Stress-tests the schema against reality.
- [ ] Build `stubs/` (one file per intended-but-uncurated EEP) + a `check-stubs` gate.
- [ ] Set up `claim`-issue coordination (issue title carries the AOP-Wiki / canonical ID).
- **Done when:** entries + stub queue validate and a `claim` issue can be filed.

## Phase D — rendering & export
- [ ] Port/adapt the Jinja2 HTML renderer for AOP pages. **Keep generated pages out of
      curation PRs** — a separate bot workflow regenerates them.
- [ ] Optional graph export (the AOP network is a natural KGX / CX2 / NDEx graph).
- [ ] Add a `generate-pages` bot lane (its own `auto/` PR). `deploy-docs.yaml` already exists
      — extend rather than duplicate.
- **Done when:** pages build in a bot PR, not a content PR.

## Phase E — GitHub authorization layer
- [ ] Create the GitHub App(s):
  - **Writer** (`contents:write`, `pull_requests:write`, `issues:write`) — authors curation
    PRs, commits, comments.
  - **Reviewer** (`pull_requests:write`, `contents:read`) — *only if agents self-merge*;
    separate identity so an agent never approves its own work.
- [ ] Install on the repo; store App ID + PEM as the secrets in the table below.
- [ ] Branch protection on `main`: require review, enable **`dismiss_stale_reviews`**, require
      the Phase-B checks as status gates. Merge queue optional.
- [ ] Disable fork PRs (secrets aren't exposed to fork runs); contributors push to `origin`.
- [ ] Create labels: `claim`, `curation`, `low_effort` / `medium_effort` / `high_effort`.
- **Done when:** a manual `claude-code-review` dispatch reviews a test PR under the bot identity.

## Phase F — agentic loop
- [ ] Port interactive `@claude` + `claude-code-review` workflows (`anthropics/claude-code-action@v1`).
- [ ] Add `resolve-agent-config` composite action + `.github/agent-config.yaml` (model per
      workflow) + `.github/cron-profiles.yaml` (cadence). Wire these **before** you have many workflows.
- [ ] Port the curation scanner (effort-tier model matrix) and, if self-merging, the
      PR-shepherd (deterministic merge controller + LLM tending).
- **Done when:** the scanner opens a curation PR that gets reviewed (and, if enabled, merges).

## Phase G — deep-research providers (optional)
- [ ] Add `deep-research-client[...]` to dev deps.
- [ ] Set **one** provider key first (Falcon/FutureHouse or OpenAI), confirm reports arrive as
      **screened leads** — citations verified before any content lands.
- [ ] Build the screening/preflight step before enabling more providers.
- [ ] Keep Biomni opt-in behind an env flag (local code + large data lake).
- **Done when:** a provider report drives a verified-evidence AOP curation PR.

---

## Reference — Actions secrets inventory

| Secret | Purpose | Tier |
|---|---|---|
| `GITHUB_TOKEN` | built-in Actions token | automatic |
| `ANTHROPIC_API_KEY` | core Claude agent (all agentic workflows) | **required** |
| `CLAUDE_CODE_OAUTH_TOKEN` | alt agent auth (Claude subscription) | alt to above |
| `<WRITER>_APP_ID` + `<WRITER>_PRIVATE_KEY` | writer bot GitHub App | **required** |
| `<REVIEWER>_APP_ID` + `<REVIEWER>_PRIVATE_KEY` | reviewer bot GitHub App | required **if agents self-merge** |
| `FUTUREHOUSE_API_KEY` / `EDISON_API_KEY` | Falcon deep research | optional |
| `OPENAI_API_KEY` | OpenScientist provider + embeddings | optional |
| `CBORG_API_KEY` | Anthropic-compatible gateway for cheap triage jobs | optional |
| `LANGFUSE_BASE_URL` / `_PUBLIC_KEY` / `_SECRET_KEY` | agent-run tracing | optional |
| `NDEX_USERNAME` / `NDEX_PASSWORD` | NDEx graph publishing | export only |

## Reference — deep-research providers (all via `deep-research-client`)

| Provider | Key(s) | Note |
|---|---|---|
| FutureHouse / Falcon | `FUTUREHOUSE_API_KEY`, `EDISON_API_KEY` | primary literature research |
| OpenScientist / OpenAI | `OPENAI_API_KEY` | non-NCBI research + embeddings |
| Biomni | `SOMA_ENABLE_BIOMNI=1` (or equiv) + own model key | opt-in; local code + large lake |
| Perplexity / Asta / Kosmos | `<provider>_API_KEY` | additional lenses |

> Providers generate **leads only**. Nothing they emit reaches `kb/` unscreened.

## Reference — external data services (mostly no auth)

Literature: PMID via NCBI E-utilities (optional `NCBI_API_KEY` for rate), DOI via Crossref.
Tox/exposure structured sources: **AOP-Wiki**, **EPA CompTox (DTXSID)**, **CTD**, **ECOTOX**,
**PubChem**. Ontology validation: EBI **OLS** + OBO SQLite builds. Rule to keep: **fetch once
into a committed cache, validate against the cache offline.**

---

## Files worth porting from dismech (`monarch-initiative/dismech`)

- `justfile` recipes: `install`, `qc`, `validate-all`, `fetch-reference`, `validate-terms`,
  `count-verified-snippets`, `normalize-cache`, `check-duplicate-keys`, `check-entity-refs`,
  `check-causal-targets`.
- `conf/oak_config.yaml` — ontology-prefix → adapter map (adapt prefixes to SOMA's set).
- `.github/agent-config.yaml` + `.github/cron-profiles.yaml` + `.github/actions/resolve-agent-config/`.
- `.github/actions/oak-cache/` — ontology build caching.
- Workflows: `claude.yml`, `claude-code-review.yml`, `curation-scanner.yml`,
  `pr-shepherd.yml`, `nightly-kb-sweep.yaml`, `generate-pages.yaml`, `close-fork-prs.yml`.
- The custom check scripts (duplicate-key, entity-ref foreign-key, causal-target,
  enum-value, cache-integrity).

### Domain-specific gold already in dismech's `.claude/skills/` (directly reusable for SOMA)
These tox/AOP skills exist in the dismech repo and are almost verbatim applicable here:
- **`aop-wiki`** — query the AOP-Wiki XML export (AOP/KE/KER lookup, WoE tables) via `aop-wiki-cli`.
- **`mie-ker-capture`** — turn AOP-Wiki Key Events into verified dismech-style causal edges.
- **`ker-evidence-triage`** — judge how much literature evidence a KER actually carries before curating it.
- **`disease-trajectories`** — comorbidity/trajectory mining (if SOMA models outcome sequences).
- Plus the generic curation/evidence skills: `dismech-references`, `dismech-terms`,
  `create-module`, `initiate-new-disorder-creation`.

---

## Companion artifact (design rationale + "what bites you")
https://claude.ai/code/artifact/1f570075-a470-42c6-98d5-ca2e525fb5fb
