"""SOMA answers for PO, CT, CRS, RCS sheets.

Source IDs are defined in SOMA_Resource_Inventory.md:
  S01 kb/publications/*.yaml (41 files) @ somamech d8f40d9   CURRENT_STATE_CANONICAL
  S02 soma-schema 0.2.4 schema sources                        CURRENT_STATE_CANONICAL_COMPANION
  S03 .claude/skills/claim-paper/SKILL.md                     DESIRED_STATE_SUPPORT
  S04 .claude/skills/extraction-pr-review/SKILL.md            DESIRED_STATE_SUPPORT
  S05 verification/*.json + scripts/snippet_receipts.py       DESIRED_STATE_SUPPORT
  S06 project.justfile QC recipes + .github/workflows/main.yaml DESIRED_STATE_SUPPORT
  S07 references_cache/*.md                                   DESIRED_STATE_SUPPORT
  S08 scripts/soma_duckdb.py + README DuckDB section          DESIRED_STATE_SUPPORT
  S09 scripts/build_site.py + scripts/site_templates/         DESIRED_STATE_SUPPORT
  S10 somamech README.md (AI-generated content notice)        DESIRED_STATE_SUPPORT
  S11 ontology_grounding_report.tsv + run_term_validator.sh   DESIRED_STATE_SUPPORT
  S12 git history and pull-request records                    DESIRED_STATE_SUPPORT
"""

PO = "xl/worksheets/sheet1.xml"
CT = "xl/worksheets/sheet2.xml"
CRS = "xl/worksheets/sheet3.xml"
RCS = "xl/worksheets/sheet4.xml"

# ---------------------------------------------------------------- PO (vertical)
po = {
    "B1": "SOMA (Standardized Outcome Measurement and Assay model) — schema repository "
          "EHS-Data-Standards/soma; knowledge base and tooling repository "
          "EHS-Data-Standards/somamech",
    "B2": "Sierra Taylor Moxon (Lawrence Berkeley National Laboratory). "
          "TO CONFIRM: whether additional project representatives should be named, and "
          "whether this submission should cover both repositories or be split into two.",
    "B3": "SOMA is a LinkML schema and knowledge base for environmental health sciences (EHS) "
          "airway-biology outcomes research. It represents assays, measurements, exposure "
          "conditions, experimental protocols and Adverse Outcome Pathway (AOP) Key Events for "
          "respiratory outcomes: ciliary function, airway surface liquid, mucociliary clearance, "
          "oxidative stress, CFTR ion-channel function, EGFR signalling, mucin biology, "
          "BALF/sputum inflammatory markers, spirometry and target-gene expression. "
          "The knowledge base is built one publication at a time: an AI extraction agent, "
          "directed and reviewed by a human contributor, reads an open-access paper and emits one "
          "Container YAML file per paper (41 files at the time of this review), in which every "
          "claim-bearing object carries evidence items that quote the source publication verbatim. "
          "Entities are grounded to GO, ChEBI, CL, UBERON, MONDO, HPO, UO, ENVO and OBI. "
          "Primary users are EHS outcomes researchers and AOP developers; generated products "
          "include a DuckDB database, TSV dumps, a pooled Excel workbook and a per-paper review "
          "site. Note that the repository states explicitly that the majority of its content is "
          "AI-generated and that a human name on a commit denotes direction and review rather "
          "than authorship (S10).",
    "B4": "The project's central requirement is that a consumer can verify any extracted value "
          "against the publication it came from. Each evidence item carries an exact quote, the "
          "cited PMID, the publication title, the article section the quote came from, and the "
          "figure or table that reports the underlying data. Two of these fields are machine-"
          "checked in CI across the whole corpus: the quote must appear word-for-word in a cached "
          "copy of the cited publication, and the recorded title must match the real publication "
          "title (S02, S06). Where a publisher blocks full-text caching, a committed receipt of "
          "snippet hashes proves a local full-text check passed and detects any later edit to the "
          "quote (S05). "
          "Because the knowledge base is AI-generated, the project's most important unmet need is "
          "provenance of the extraction itself: which agent and model produced a file, under which "
          "extraction-skill version, directed and reviewed by which human, on what date, against a "
          "full-text or abstract-only cached copy, and with what verification outcome. None of that "
          "is currently represented in the canonical data (S01, S02); all of it exists elsewhere in "
          "the project (S03, S04, S05, S12). A secondary need is AOP weight-of-evidence: Key Event "
          "Relationship claims carry a categorical evidence-strength judgement that is currently "
          "asserted on the claim with no link to the evidence items that justify it.",
}

# ---------------------------------------------------------------- CT (6 claim types)
_ct_rows = [
    dict(
        id="C001",
        desc="Exposure-Response Measurement",
        subj="Biological System (airway epithelial cell culture; human subject; "
             "non-human animal subject; study population)",
        obj="Quantity Value (measured value with unit, central tendency, variability and sample size)",
        rel="has measured value for <named measurement> under <exposure condition>",
        qual="exposure condition (agent, concentration, duration, route); experimental group "
             "(baseline / control / treated); anatomical and cell-type context; sample size; "
             "measurement unit; value qualifier for censored values such as \"<0.05\"",
        ex="In 33 asymptomatic adult male participants of a thermal power plant at the "
           "high-PM2.5 spring visit, measured FEV1/FVC was 84.32 +/- 3.86 percent (n = 33) "
           "[E02; LF:ghosh-pm25-seasonal-spirometry-output-spring].",
        epn="Needs the verbatim source passage reporting the value, the cited publication, the "
            "article section and the figure/table label that reports it, and the direction of "
            "support. Needs the extraction provenance described in the Project Overview form "
            "(agent, model, skill version, human reviewer, date, cache content type, verification "
            "status), none of which is currently in the data. Where a value exists only in a "
            "figure, project rules forbid estimating it, so the record carries the figure "
            "reference and a described direction but no quantity value.",
        note="This is the most numerous claim type in the knowledge base and the one that is NOT "
             "represented as a first-class object: the claim is implicit in an output-measurement "
             "record plus its named measurement slot, its exposure condition and its experimental "
             "group. Shares one evidence/provenance profile with C002, C003, C005 and C006.",
    ),
    dict(
        id="C002",
        desc="Exposure-Response Comparison",
        subj="Exposure Agent (ENVO or ChEBI chemical entity; particulate matter; "
             "gaseous pollutant; smoke)",
        obj="Named Measurement; Biological Process (GO)",
        rel="increases; decreases; does not significantly change",
        qual="change type (absolute difference, percent change, fold change, ratio); statistical "
             "test and p-value; confidence interval; derivation (reported in paper vs computed "
             "from extracted values); control and treated output records compared",
        ex="Every 10 ug/m3 increase in PM2.5 decreased the measured FEV1/FVC ratio by 2.62 "
           "percentage points (95% CI -3.68 to -1.56) [E04; COMP:ghosh-lf-fev1fvc].",
        epn="Same evidence requirements as C001. Additionally needs the statistical metrics "
            "(p-value, test name, confidence interval) represented as structured content, and the "
            "distinction between a change reported by the authors and one computed afterwards from "
            "extracted values — which the canonical data already records.",
        note="Represented as a first-class ResponseComparison object with its own identifier, so "
             "evidence and provenance can attach to the comparison claim directly.",
    ),
    dict(
        id="C003",
        desc="Key Event Occurrence",
        subj="Biological Process (GO); Cell Type (CL); Anatomical Entity (UBERON)",
        obj="Biological Action (increased; decreased; activated; inhibited; impaired; altered)",
        rel="undergoes measurable perturbation at <level of biological organization>",
        qual="level of biological organization (molecular, cellular, tissue, organ, individual, "
             "population); cell type; anatomical site; AOP-Wiki identifier",
        ex="PI3K/AKT pathway activation occurs at the molecular level of biological organization "
           "[KE:ke-pi3k-akt-activation].",
        epn="Same evidence requirements as C001. Key Events are shared vocabulary across papers, "
            "so the same Key Event may accumulate evidence items from several publications; the "
            "project needs each evidence item to remain attributable to its own source.",
        note="Represented as a nested object within the Container, identified by a stable KE "
             "identifier reused across files.",
    ),
    dict(
        id="C004",
        desc="Key Event Relationship (AOP causal linkage)",
        subj="Key Event",
        obj="Key Event",
        rel="directly leads to; indirectly leads to",
        qual="weight of evidence (strong / moderate / weak / not specified); quantitative "
             "understanding of the response-response relationship (high / moderate / low / "
             "not specified)",
        ex="PI3K/AKT pathway activation indirectly leads to suppressed apoptosis; "
           "weight of evidence = moderate [E03; KER:ghosh-pi3k-akt-to-suppressed-apoptosis].",
        epn="This claim type has materially different evidence requirements from the other five. "
            "It carries a categorical weight-of-evidence judgement and a quantitative-understanding "
            "judgement drawn from the OECD AOP framework, and these are currently asserted on the "
            "claim object itself with no representation of which evidence items justify them, nor "
            "of who made the judgement. The project wants grouped evidence arguments for this "
            "claim type, so that strength can be asserted over a set of evidence items rather than "
            "over the relationship as a whole, and so that evidence of different kinds (human "
            "clinical, model organism, in vitro, computational) can be weighed differently as the "
            "AOP framework expects.",
        note="Represented as a first-class KeyEventRelationship object with its own identifier and "
             "explicit upstream event, relationship type and downstream event. This is the only "
             "claim type in the project that is natively subject-predicate-object shaped, and the "
             "only one that needs a distinct evidence-interpretation model.",
    ),
    dict(
        id="C005",
        desc="Assay Method Claim",
        subj="Assay",
        obj="Protocol; Biological System; Key Event",
        rel="follows protocol; was performed on; informs on key event",
        qual="protocol type (imaging, molecular assay, staining, spirometry); detection method; "
             "normalization method; instrument platform; antibodies and reagents used; "
             "published standard followed",
        ex="The spirometry assay followed American Thoracic Society (1995) guidelines on a "
           "Schiller SP260 spirometer and informs on the impaired lung function key event "
           "[LF:ghosh-pm25-seasonal-spirometry; PROTOCOL:ghosh-spirometry-001].",
        epn="Evidence for this claim type is the same verbatim-quote evidence used for C001; the "
            "canonical data does not cite evidence for a protocol independently of the assay that "
            "ran it. The method detail itself is evidence-item provenance rather than an evidence "
            "item: it describes how the measurements used as evidence came to exist.",
        note="Reported as a separate claim type at the project representative's direction. Its "
             "evidence and provenance requirements are the same as C001, so it may reasonably be "
             "merged with C001 in a later revision; the project should confirm. Note that the "
             "published standard a protocol follows (for example the ATS 1995 guideline) is "
             "recorded as a method specification, not as a guideline evidence item.",
    ),
    dict(
        id="C006",
        desc="Exposure Condition Claim",
        subj="Biological System (cell culture; human subject; animal subject; study population)",
        obj="Exposure Agent (ENVO or ChEBI chemical entity)",
        rel="was exposed to",
        qual="concentration and unit; duration; exposure route; exposure regimen; "
             "ambient versus experimental exposure",
        ex="Participants were exposed to ambient fine respirable suspended particulate matter "
           "(ENVO:01000415) at a daily mean of 45.28 ug/m3 during December 2021 to March 2022 "
           "[E06; EXPOSURE:ghosh-pm25-spring].",
        epn="Same evidence requirements as C001. Exposure conditions are the context that makes a "
            "measurement claim interpretable, and in the canonical data an output measurement "
            "references the exposure condition it was measured under.",
        note="Reported as a separate claim type at the project representative's direction. Like "
             "C005 its evidence and provenance requirements match C001, and it may reasonably be "
             "treated as qualifying context on C001 in a later revision.",
    ),
]

ct = {}
for i, r in enumerate(_ct_rows):
    row = 2 + i
    ct[f"A{row}"] = r["id"]
    ct[f"B{row}"] = r["desc"]
    ct[f"C{row}"] = r["subj"]
    ct[f"D{row}"] = r["obj"]
    ct[f"E{row}"] = r["rel"]
    ct[f"F{row}"] = r["qual"]
    ct[f"G{row}"] = r["ex"]
    ct[f"H{row}"] = r["epn"]
    ct[f"I{row}"] = r["note"]

# ---------------------------------------------------------------- CRS (rows 2-6)
crs = {
    # CS.PARENT_SLOT_VALUE
    "F2": "Y",
    "G2": "Y",
    "H2": "This is the dominant structure in the canonical data and the one used for the project's "
          "most numerous claim type (C001). An output-measurement record supplies the implicit "
          "subject, a named measurement slot supplies the relationship, and a nested QuantityValue "
          "supplies the object: fvc: {value: \"2.92\", unit: {id: UO:0000099, name: liter}, "
          "central_tendency: mean, sample_size: 33} (S01, E02). "
          "The structure must be preserved. The schema is deliberately assay-centric, with "
          "domain-specific assay classes carrying named measurement slots (S02), and the extraction "
          "agents, the LinkML and reference validators, the DuckDB builder and the pooled workbook "
          "all read this shape (S03, S06, S08). A SEPIO-based representation may make the implicit "
          "subject and relationship explicit for exchange, but the project requires the native "
          "named-slot form to remain authoritable. Applies to C001, C003, C005, C006.",
    # CS.NESTED_OBJECT
    "F3": "Y",
    "G3": "Y",
    "H3": "Used throughout the canonical data. Evidence items are a nested list on each "
          "claim-bearing object; QuantityValue, variability, units, exposure conditions, "
          "experimental groups and protocol references are nested structured objects (S01, S02). "
          "May be transformed as long as the nesting that ties a measurement to the exposure "
          "condition and experimental group it was measured under is preserved, because that "
          "context is what makes the measurement claim interpretable. Applies to all claim types.",
    # CS.REIFIED_OBJECT
    "F4": "Y",
    "G4": "Y",
    "H4": "Partially used today, and this is a distinction worth recording carefully. Two claim "
          "types ARE represented as first-class objects with their own identifiers, independently "
          "referenceable and carrying their own evidence lists: ResponseComparison for C002 "
          "(id COMP:ghosh-lf-fev1fvc, referencing the control and treated output records it "
          "compares; E04) and KeyEventRelationship for C004 (id "
          "KER:ghosh-pi3k-akt-to-suppressed-apoptosis, with explicit upstream event, relationship "
          "type and downstream event; E03). Key Events (C003) are nested objects with stable reused "
          "identifiers. The measurement claim C001 is NOT reified. "
          "Desired: continue to support reified claim objects for C002 and C004. "
          "OPEN FOR HUMAN REVIEW: whether C001 measurement claims should also become first-class "
          "claim objects. Reification would let evidence, strength and provenance attach per "
          "proposition, but would change the file shape the extraction agents emit and the "
          "generated products consume, so the project has not decided. Treated here as a "
          "question rather than a requirement.",
    # CS.DIRECT_EDGE
    "F5": "N",
    "G5": "M",
    "H5": "Current state: direct inspection of the canonical YAML and schema establishes no "
          "triple, quad or property-graph edge representation (S01, S02). "
          "Desired-state support: EXISTING_PROJECT_CAPABILITY_NOT_IN_CANONICAL_EXPORT — "
          "S08 (scripts/soma_duckdb.py): the generated DuckDB database exposes a `link` table "
          "holding every entity-to-entity edge, which is how many-to-many relationships such as "
          "follows_protocols are queried. That is a derived query product rather than a statement "
          "of how the project wants its knowledge represented, so this is recorded as M pending "
          "the representative's confirmation rather than as a requirement.",
    # CS.OTHER
    "F6": "N",
    "G6": "N",
    "H6": "No additional claim representation structure beyond the four above is used or required. "
          "The four rows above together describe the canonical data completely.",
}

# ---------------------------------------------------------------- RCS (rows 2-5)
rcs = {
    # RCS.FREE_TEXT
    "F2": "Y",
    "G2": "Y",
    "H2": "The reified claim objects in the canonical data carry a human-readable expression of "
          "what they assert, in their name and description slots. Example: ResponseComparison "
          "COMP:ghosh-lf-fev1fvc has description \"LMER beta estimate: every 10 ug/m3 increase in "
          "PM2.5 decreased the measured FEV1/FVC ratio by 2.62 percentage points.\" and name "
          "\"Association of PM2.5 with the measured FEV1/FVC ratio\"; KeyEventRelationship "
          "KER:ghosh-pi3k-akt-to-suppressed-apoptosis has name \"PI3K/AKT pathway activation leads "
          "to suppressed apoptosis\" (S01, E03, E04). These are load-bearing rather than "
          "decorative: they are what the generated review site renders for a human reader (S09), "
          "and they carry nuance the structured fields cannot, such as the per-10 ug/m3 scaling of "
          "a regression estimate.",
    "I2": "C002; C004",
    # RCS.STRUCTURED_STATEMENT
    "F3": "Y",
    "G3": "Y",
    "H3": "Both reified claim types carry structured proposition semantics in dedicated fields "
          "directly on the claim object, using project-specific field names rather than literal "
          "subject/predicate/object. KeyEventRelationship: upstream_event, relationship_type "
          "(\"indirectly leads to\"), downstream_event. ResponseComparison: compared_measurement, "
          "change_direction (decreased), change_value, change_type (absolute_difference), with "
          "control_output and treated_output identifying the records compared (S01, S02, E03, E04). "
          "The project requires structured semantics on the claim object itself.",
    "I3": "C002; C004",
    # RCS.STRUCTURED_PROPOSITION
    "F4": "N",
    "G4": "N",
    "H4": "Current state: direct inspection establishes no separate Proposition object; the "
          "structured semantics sit directly on the claim object (S01, S02). "
          "No project source provides affirmative evidence of a requirement for a reusable "
          "proposition object held separately from the claim that asserts it. The project has no "
          "use case in which two claims share one proposition: each claim is tied to the single "
          "publication it was extracted from, and the repository deliberately keys records on the "
          "source file rather than the cited publication precisely because two files may "
          "legitimately cite the same paper without their entities being merged (S08). "
          "Not selected, rather than selected because SEPIO offers it.",
    "I4": "",
    # RCS.QUALIFIERS
    "F5": "Y",
    "G5": "Y",
    "H5": "Qualifying information is essential to every claim type in this project and is "
          "represented today. For C002: change_type, statistical_test, p_value, confidence "
          "interval, and derivation (whether the change was reported in the paper or computed from "
          "extracted values). For C004: weight of evidence and quantitative understanding. For "
          "C001/C003/C006: the exposure condition a measurement was taken under, the experimental "
          "group (baseline / control / treated), sample size, central tendency, variability type, "
          "unit, level of biological organization, cell type and anatomical site (S01, S02). "
          "An environmental-health measurement claim is uninterpretable without its exposure "
          "condition and experimental group, so qualifier support is a hard requirement rather "
          "than an enhancement. Qualifiers must be supported on whichever carrier holds the "
          "claim semantics, which for this project is the claim object itself.",
    "I5": "C001; C002; C003; C004; C005; C006",
}

SHEETS = {PO: po, CT: ct, CRS: crs, RCS: rcs}
