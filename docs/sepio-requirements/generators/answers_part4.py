"""SOMA answers for the PROV sheet (sheet7).

Columns: G=[F1] current, H=[F2] desired, I=[F5] examples, J=[F6] explanation.
Rows: 2-11 Evidence Item, 13-20 Semantic Alignment, 22-26 Evidence Interpretation,
28-34 Assertion, 36-41 Encoding, 43-49 Retrieval. Rows 12/21/27/35/42 are blank
separators in the template and are left untouched.
"""

PROV = "xl/worksheets/sheet7.xml"

# The recurring desired-state justification for extraction provenance. The project
# demonstrably has this information outside the canonical data.
_EXTRACTION_SUPPORT = (
    "Desired-state support: EXISTING_PROJECT_CAPABILITY_NOT_IN_CANONICAL_EXPORT — "
    "S03 (.claude/skills/claim-paper/SKILL.md, the extraction procedure an AI agent follows), "
    "S04 (.claude/skills/extraction-pr-review/SKILL.md, the review checklist applied to every "
    "extraction pull request), S10 (somamech README.md, which states that the majority of "
    "repository content is AI-generated and that a human name on a commit denotes direction and "
    "review rather than authorship), and S12 (git history and pull-request records, which identify "
    "the extraction and the reviewing human for every file). The project knows all of this and a "
    "consumer of a kb/publications file can read none of it."
)

_rows = {
    # =========================================================== Evidence Item Provenance
    2: dict(  # PROV.EI.AGENT
        f1="N", f2="N",
        ex="Not represented. The cited publication identifies its own authors: "
           "reference: \"PMID:41469766\" with reference_title.",
        expl="Current state: direct inspection establishes no author or laboratory field anywhere "
             "in the canonical data or schema (S01, S02). The agents that generated the "
             "measurements used as evidence are the authors of the cited publication, and the "
             "project identifies them indirectly by citing the publication rather than "
             "representing them. No project source supports a requirement to represent study "
             "authors or laboratories as agents.",
    ),
    3: dict(  # PROV.EI.METHOD_TYPES
        f1="Y", f2="Y",
        ex="protocol_type: SpirometryProtocol; protocol_type: MolecularAssayProtocol; "
           "detection_method: \"indirect ELISA, TMB substrate, absorbance at 450 nm\"; "
           "detection_method: \"automated hematology analyzer (Erma PCE-210)\". "
           "Also, on every evidence item: evidence_source: HUMAN_CLINICAL.",
        expl="Represented, at two levels. The schema has a typed protocol hierarchy — "
             "ImagingProtocol, MolecularAssayProtocol, StainingProtocol, SpirometryProtocol — and "
             "each protocol records a detection_method and, where relevant, a "
             "normalization_method (S02). This is a required capability for the project: an "
             "exposure-response measurement is not interpretable without knowing the kind of assay "
             "that produced it.",
    ),
    4: dict(  # PROV.EI.METHODS
        f1="Y", f2="Y",
        ex="PROTOCOL:ghosh-spirometry-001 — name: \"PC spirometry per American Thoracic Society "
           "guidelines\", spirometry_standard: \"American Thoracic Society (1995) guidelines\", "
           "equipment_required: [\"PC spirometer (SP260, Schiller, Barr, Switzerland)\"]. "
           "PROTOCOL:ghosh-elisa-* — antibodies_used: [\"HIF-1alpha (Abclonal A22041, 1:2000)\"], "
           "platform: \"Infinite 200 PRO microplate reader (Tecan)\", normalization_method: "
           "\"per-well total protein\".",
        expl="Strongly represented and one of the project's most developed provenance areas. "
             "Protocols are first-class objects with stable identifiers, referenced by the assays "
             "that follow them, and they record the published standard followed, the instrument "
             "platform, the antibodies and reagents, the equipment and the normalisation method. "
             "The project deliberately creates one protocol identifier per distinct method — for "
             "example one per qPCR target, because each target has its own primer pair — so that "
             "one identifier denotes one protocol. Note that a published guideline referenced here "
             "is a method specification, not a guideline evidence item "
             "(see EI.DOCUMENT.GUIDELINE).",
    ),
    5: dict(  # PROV.EI.RESOURCES
        f1="Y", f2="Y",
        ex="antibodies_used: [\"HIF-1alpha (Abclonal A22041, 1:2000)\"]; equipment_required: "
           "[\"Automated hematology analyzer (Erma PCE-210, Saitama, Japan)\"]; platform: "
           "\"Infinite 200 PRO microplate reader (Tecan, Maennedorf, Zurich, Switzerland)\". "
           "Model systems are represented by dedicated classes for cellular systems, human and "
           "animal subjects and study populations.",
        expl="Represented. Reagents, antibodies with dilutions, instruments, equipment and "
             "biological model systems — cell cultures, air-liquid interface cultures, animal "
             "strains, human cohorts — are all captured, the first group as protocol attributes "
             "and the last through the StudySubject class hierarchy (S02). Resource detail is "
             "required because reagent and model-system differences are a principal source of "
             "disagreement between airway-biology studies.",
    ),
    6: dict(  # PROV.EI.EXECUTION
        f1="Y", f2="Y",
        ex="Protocol description: \"Hematological parameters - total count (TC), differential count "
           "(DC), erythrocyte sedimentation rate (ESR) and hemoglobin (Hb) - measured on an "
           "automated hematology analyzer (Erma PCE-210, Saitama, Japan) in anticoagulated whole "
           "blood collected in K2EDTA vacutainers.\"",
        expl="Represented, but as narrative free text rather than as structured execution steps. "
             "Protocol and assay description fields carry what was done, in what order, on what "
             "material; there is no structured representation of tasks, inputs and outputs. "
             "The project considers the narrative form adequate for its use cases and does not "
             "require structured execution provenance for the SOURCE study's activities, since the "
             "authoritative account of those activities is the publication itself. "
             "Reported as Y on the basis that the information is captured, with the caveat that it "
             "is unstructured.",
    ),
    7: dict(  # PROV.EI.DATE
        f1="N", f2="M",
        ex="Not represented as a field. Present in narrative text only: an assay description "
           "records sampling \"once in Aug 2021 (monsoon, lower PM2.5) and once in Mar 2022 "
           "(spring, higher PM2.5)\".",
        expl="Current state: direct inspection establishes no date field for when the source "
             "measurement was made (S01, S02); sampling dates appear only inside description prose "
             "where they cannot be queried. "
             "Desired state recorded as M. Measurement dates matter in this domain, because "
             "ambient exposure varies seasonally and the exposure contrast in a panel study is "
             "often defined by when samples were taken — the example above is exactly that case. "
             "But no project source states a requirement to represent them structurally, so this "
             "is flagged for the representative rather than asserted.",
    ),
    8: dict(  # PROV.EI.LOCATION
        f1="N", f2="M",
        ex="Not represented as a field. Present in narrative text only: \"33 asymptomatic adult "
           "male employees ... of a thermal power plant in Bankura district, West Bengal, India "
           "(23.46414 N, 87.13182 E)\".",
        expl="Current state: direct inspection establishes no structured slot for the physical, "
             "organisational or environmental context in which an evidence item was generated "
             "(S01, S02). Geographic and setting information, including coordinates, appears in "
             "description prose. "
             "Desired state recorded as M. Location is substantive rather than incidental for "
             "environmental health: ambient exposure is place-specific, and the generalisability of "
             "a finding depends on where the cohort lived. The project has not stated a structured "
             "requirement, so this is flagged for review. Note also the separate culture-condition "
             "sense of this question (temperature, CO2, hypoxia), which the project likewise "
             "records only in protocol prose.",
    ),
    9: dict(  # PROV.EI.RETRIEVAL_SOURCE
        f1="Y", f2="Y",
        ex="On every evidence item: reference: \"PMID:41469766\" with reference_title: \"Seasonal "
           "impact of PM(2.5) on pro-oncogenic drivers among participants of a thermal power plant "
           "in India.\"",
        expl="Represented, and required. Every evidence item names the publication its content was "
             "retrieved from, as a PubMed CURIE constrained by pattern, and carries that "
             "publication's title copied from the fetched reference record rather than typed from "
             "memory. The title is machine-checked against the real publication title, which is "
             "what prevents a quote being attributed to the wrong paper (S02, S06). "
             "DESIRED ADDITION: the project also wants to record which COPY of the publication the "
             "content was retrieved from and whether that copy was full text or abstract only, "
             "because that determines what a quote can be checked against. "
             "Desired-state support: EXISTING_PROJECT_CAPABILITY_NOT_IN_CANONICAL_EXPORT — S05 and "
             "S07 record this today outside the canonical data.",
    ),
    10: dict(  # PROV.EI.QUALITY
        f1="N", f2="M",
        ex="Not represented as a quality field. The nearest existing signal is article_section, "
           "which distinguishes a value quoted from results from one quoted from methods.",
        expl="Current state: direct inspection establishes no information-quality or study-rigour "
             "field (S01, S02). "
             "Desired state recorded as M, with a documented partial basis. The project already "
             "operates a reliability distinction that is quality-adjacent: the schema states that "
             "recording the article section makes provenance reviewable, because a dose or "
             "response value quoted from Results carries more weight than one quoted from a "
             "Methods sentence about how a compound was stored, and instructs that Results-cited "
             "values be preferred when both exist (S02). That is a judgement about the reliability "
             "of the reported information, expressed through locus rather than through a quality "
             "grade. Desired-state support: DOCUMENTED_MODEL_INTENT — S02 (evidence.yaml slot "
             "documentation for article_section). Whether the project wants an explicit quality "
             "grade in addition is unresolved and flagged for review.",
    ),
    11: dict(  # PROV.EI.GENERATION_CONTEXT
        f1="Y", f2="Y",
        ex="evidence_source: HUMAN_CLINICAL on every evidence item in the example file. "
           "Permissible values: HUMAN_CLINICAL (patients, cohorts, case reports, trials, "
           "epidemiology), MODEL_ORGANISM (in vivo animal evidence), IN_VITRO (cell culture, "
           "air-liquid interface cultures, organoids, tissue slices, biochemical assays), "
           "COMPUTATIONAL (in silico or modelling studies, even when they use clinical data as "
           "input), OTHER.",
        expl="Represented on every single evidence item in the corpus, as a required categorical, "
             "and one of the project's most-used provenance fields. "
             "ONE IMPORTANT SEMANTIC POINT: the value classifies the kind of study THE CITED "
             "PUBLICATION reports, not the agent that performed the extraction. The schema states "
             "this explicitly — 'classify the paper, not the person doing the extraction' (S02) — "
             "and the distinction matters for this project because every file is AI-extracted, so "
             "an extraction-centred reading of this field would make every value identical and "
             "useless. "
             "The project uses this classification as the primary axis along which evidence of "
             "different kinds would be weighed differently if grouped arguments are adopted "
             "(see EINT.GROUPING).",
    ),
    # =========================================================== Semantic Alignment Provenance
    13: dict(  # PROV.SA.AGENT
        f1="N", f2="Y",
        ex="Not represented. Illustrative future value: an agent identifier and model version for "
           "the AI extraction agent that read the publication and produced the structured record, "
           "together with the human who directed and reviewed it.",
        expl="Current state: direct inspection establishes that the canonical data contains no "
             "agent information of any kind. The Container root has exactly one provenance slot, "
             "source_publication; there is no agent, date, model, method or version field anywhere "
             "(S01, S02). " + _EXTRACTION_SUPPORT + " "
             "This is the project's highest-priority desired-state requirement. Because the "
             "knowledge base is AI-generated from literature, semantic alignment is not an "
             "implicit human cognitive step that needs no documentation — it is the central "
             "activity, performed by a software agent, and the project needs it auditable.",
    ),
    14: dict(  # PROV.SA.METHOD_TYPES
        f1="N", f2="Y",
        ex="Not represented. The alignment method types actually used are: LLM-based extraction "
           "from publication text, ontology grounding of entity mentions to GO, ChEBI, CL, UBERON, "
           "MONDO, HPO, UO, ENVO and OBI terms, and validation of each term reference against the "
           "ontology's own label.",
        expl="Current state: the RESULTS of alignment are everywhere in the canonical data — every "
             "ontology term reference is an id and label pair — but the canonical data records "
             "nothing about how the alignment was performed (S01, S02). "
             "Desired-state support: EXISTING_PROJECT_CAPABILITY_NOT_IN_CANONICAL_EXPORT — S11 "
             "(ontology_grounding_report.tsv and scripts/run_term_validator.sh, the grounding and "
             "term-validation tooling) and S03 (the extraction skill, which specifies how entities "
             "are to be grounded). The project wants the kind of alignment method recorded so that "
             "a consumer can distinguish an automatically grounded term from a hand-checked one.",
    ),
    15: dict(  # PROV.SA.METHODS
        f1="N", f2="Y",
        ex="Not represented. The specific method specifications that exist today are the "
           "claim-paper extraction skill and the term validator invocation used in continuous "
           "integration, each of which is versioned in the repository.",
        expl="Current state: no method specification is referenced from the canonical data "
             "(S01, S02). " + _EXTRACTION_SUPPORT + " "
             "The project's extraction procedure is a written, versioned specification that an "
             "agent follows, which is exactly the kind of identifiable method specification this "
             "row asks about; it is simply not cited from the records it produces. Recording the "
             "specification and its version is what would let the project explain why two files "
             "extracted months apart differ in style or completeness.",
    ),
    16: dict(  # PROV.SA.EXECUTION
        f1="N", f2="M",
        ex="Not represented.",
        expl="Current state: no execution detail for alignment is represented (S01, S02). "
             "Desired state recorded as M. Step-level alignment provenance — the source string "
             "recognised, the candidate terms considered, the term chosen, the normalisation "
             "applied — is the most granular form of this requirement, and the project has not "
             "established that it needs that granularity as opposed to recording the agent, the "
             "method and the date. The project's provisional view is that agent, method and date "
             "are required and per-step execution traces are not, but the representative has not "
             "confirmed this. Flagged for human review.",
    ),
    17: dict(  # PROV.SA.DATE
        f1="N", f2="Y",
        ex="Not represented in the canonical data. Recorded outside it: a verification receipt "
           "carries verified_date: \"2026-09-28\", and the git history and pull request for each "
           "file carry its extraction date.",
        expl="Current state: direct inspection establishes no date field (S01, S02). "
             "Desired-state support: EXISTING_PROJECT_CAPABILITY_NOT_IN_CANONICAL_EXPORT — S05 "
             "(verification/PMID_*.json, which record verified_date) and S12 (git history and "
             "pull-request records). An extraction date is needed to interpret a record against "
             "the state of the schema, the extraction skill and the cached source at the time it "
             "was made.",
    ),
    18: dict(  # PROV.SA.CONFIDENCE_CATEGORY
        f1="N", f2="M",
        ex="Not represented. No confidence value of any kind exists in the canonical data; the "
           "only numeric uncertainty values are statistical properties of the measurements "
           "themselves.",
        expl="Current state: direct inspection establishes no categorical confidence for alignment "
             "(S01, S02). The project's grounding report (S11) records whether a schema enum value "
             "is already grounded, needs a custom term, or has close candidate terms, but it "
             "carries no confidence value and concerns schema enum grounding rather than per-record "
             "entity alignment. "
             "Desired state recorded as M and flagged for human review. The project's provisional "
             "view is that this should be N: a confidence value self-reported by the same AI agent "
             "that performed the grounding is not evidence a consumer should weigh, and the project "
             "prefers mechanical verification over claimed confidence wherever a check is possible. "
             "Marked M rather than N only because the representative has not confirmed, and "
             "because there may be genuinely ambiguous groundings in the corpus that would have "
             "been worth flagging.",
    ),
    19: dict(  # PROV.SA.CONFIDENCE_SCORE
        f1="N", f2="M",
        ex="Not represented.",
        expl="Current state and reasoning are the same as PROV.SA.CONFIDENCE_CATEGORY: no numeric "
             "alignment confidence exists in the canonical data (S01, S02), and the project's "
             "provisional view is that a model-reported score should not be introduced. "
             "FLAGGED FOR HUMAN REVIEW: desired state is UNRESOLVED and recorded as M pending the "
             "representative's decision; no project source provides affirmative evidence for this "
             "capability, so it is marked M rather than Y. If any confidence representation is "
             "adopted, the project would prefer a small categorical vocabulary over a numeric "
             "score, to avoid implying precision the agent does not have.",
    ),
    20: dict(  # PROV.SA.REVIEW
        f1="N", f2="Y",
        ex="Not represented in the canonical data. Recorded outside it: every extraction reaches "
           "the knowledge base through a pull request reviewed against a written checklist, and "
           "the pull-request record identifies the reviewing human and the outcome.",
        expl="Current state: direct inspection establishes that the canonical data records nothing "
             "about human review (S01, S02). "
             "Desired-state support: EXISTING_PROJECT_CAPABILITY_NOT_IN_CANONICAL_EXPORT — S04 "
             "(the extraction-pr-review checklist applied to every extraction pull request), S12 "
             "(pull-request records identifying the reviewer and the approval), and S10 (the "
             "README's statement that human contributors direct, review and approve the work while "
             "the content is written by AI). "
             "This is a high-value requirement for this project specifically. The repository is "
             "explicit that a human name on a commit means direction and review rather than "
             "authorship — precisely the distinction this row draws — and a data consumer currently "
             "has no way to tell whether a given record was reviewed, by whom, or whether the "
             "reviewer changed anything.",
    ),
    # =========================================================== Evidence Interpretation Provenance
    22: dict(  # PROV.INTERP.AGENT
        f1="N", f2="Y",
        ex="Not represented. The interpretation recorded in each evidence item — its supports "
           "value and its explanation — was produced by the AI extraction agent and reviewed by a "
           "human, neither of whom is identified in the data.",
        expl="Current state: direct inspection establishes no agent for the interpretation "
             "(S01, S02). " + _EXTRACTION_SUPPORT + " "
             "Because the project's evidence items fuse content with interpretation "
             "(see EINT.FLAT_COLLAPSE), the agent that judged a quote to support a claim is the "
             "same agent that extracted it. The project nonetheless wants the interpreting agent "
             "recorded, because a direction of support is a judgement a consumer may wish to "
             "discount or re-derive.",
    ),
    23: dict(  # PROV.INTERP.METHOD_TYPES
        f1="N", f2="Y",
        ex="Not represented. The method type in use is LLM-assisted evidence interpretation "
           "followed by human review, for the five claim types that record direction only; and "
           "guideline-based categorical assessment drawn from the OECD AOP framework for Key Event "
           "Relationship claims.",
        expl="Current state: no interpretation method type is represented (S01, S02). "
             "Desired-state support: EXISTING_PROJECT_CAPABILITY_NOT_IN_CANONICAL_EXPORT — S03 and "
             "S04. The project has two materially different interpretation approaches, aligned with "
             "the two evidence profiles reported in EINT.DISTINCT_MODELS, and wants them "
             "distinguishable in the data rather than inferred from the claim type.",
    ),
    24: dict(  # PROV.INTERP.METHODS
        f1="N", f2="Y",
        ex="Not represented. The specific specifications in use are the claim-paper extraction "
           "skill, which instructs how evidence quotes are selected and how direction of support "
           "is assigned, and the OECD AOP weight-of-evidence framework, which supplies the "
           "strength vocabulary for Key Event Relationship claims.",
        expl="Current state: no interpretation specification is cited from the canonical data "
             "(S01, S02). "
             "Desired-state support: EXISTING_PROJECT_CAPABILITY_NOT_IN_CANONICAL_EXPORT — S03, "
             "S04; and DOCUMENTED_MODEL_INTENT — S02, whose evidence-support and "
             "quantitative-understanding vocabularies are taken from the OECD AOP framework, "
             "making that framework the de facto interpretation specification for C004 without "
             "being cited as such.",
    ),
    25: dict(  # PROV.INTERP.DATE
        f1="N", f2="Y",
        ex="Not represented in the canonical data; available from git history and pull-request "
           "records for every file.",
        expl="Current state: no date is represented (S01, S02). "
             "Desired-state support: EXISTING_PROJECT_CAPABILITY_NOT_IN_CANONICAL_EXPORT — S12. "
             "In this project the interpretation date and the extraction date coincide, because "
             "both are performed in one pass by the same agent; the project would expect to record "
             "them once rather than separately, and notes that a model expecting independent dates "
             "per provenance level would be heavier than the workflow warrants.",
    ),
    26: dict(  # PROV.INTERP.LOCATION
        f1="N", f2="N",
        ex="Not represented.",
        expl="Current state: direct inspection establishes no location or context for the "
             "interpretation activity (S01, S02). No project source supports a desired-state "
             "requirement. The interpretation is performed in an automated pipeline rather than at "
             "a review board or panel meeting, so the organisational-context sense of this "
             "question does not apply, and the computational-environment sense is adequately "
             "covered by recording the agent and the method version.",
    ),
    # =========================================================== Assertion Provenance
    28: dict(  # PROV.ASSERTION.AGENT
        f1="N", f2="Y",
        ex="Not represented. Illustrative future value: the AI extraction agent and model that "
           "generated the record, plus the human contributor who directed and approved it.",
        expl="Current state: direct inspection establishes no asserting agent (S01, S02). "
             + _EXTRACTION_SUPPORT + " "
             "For this project the asserting agent, the interpreting agent and the aligning agent "
             "are the same agent acting in one pass, with a human reviewer approving the result. "
             "The project would want that recorded once with the roles distinguished, rather than "
             "repeated at each provenance level.",
    ),
    29: dict(  # PROV.ASSERTION.METHOD_TYPES
        f1="Y", f2="Y",
        ex="derivation: reported_in_paper — used 400 times across the corpus; the alternative "
           "permissible value is computed, meaning the value was calculated from extracted control "
           "and treated values rather than stated by the authors.",
        expl="Partially represented, and this is a genuine and easily overlooked Y. For comparison "
             "claims (C002) the canonical data records how the asserted value was arrived at: "
             "derivation distinguishes a change reported directly in the publication from one "
             "computed afterwards from extracted values (S02). That is an assertion-method "
             "distinction, represented in the data, and the project regards it as more informative "
             "than a confidence score would be, because it tells a consumer whether the number is "
             "the authors' or the project's. "
             "No equivalent distinction is recorded for the other five claim types, where the "
             "assertion method is uniformly AI extraction with human review and is not stated. "
             "Desired: retain derivation and record the general assertion method type for all claim "
             "types. Desired-state support: EXISTING_PROJECT_CAPABILITY_NOT_IN_CANONICAL_EXPORT — "
             "S03, S10.",
    ),
    30: dict(  # PROV.ASSERTION.METHODS
        f1="N", f2="Y",
        ex="Not represented. The specification in use is the versioned claim-paper extraction "
           "skill together with the extraction-pr-review checklist that gates every merge.",
        expl="Current state: no assertion specification is cited from the canonical data "
             "(S01, S02). "
             "Desired-state support: EXISTING_PROJECT_CAPABILITY_NOT_IN_CANONICAL_EXPORT — S03, "
             "S04, S06. The project's extraction and review procedure is a documented decision "
             "procedure with hard gates: schema validation, ontology term validation and verbatim "
             "quote verification must all pass before a record enters the knowledge base. Citing "
             "that procedure and its version from the record is what would let a consumer know "
             "which gates a given record actually passed.",
    ),
    31: dict(  # PROV.ASSERTION.DATE
        f1="N", f2="Y",
        ex="Not represented in the canonical data; available from git history and pull-request "
           "records.",
        expl="Current state: no date is represented (S01, S02). "
             "Desired-state support: EXISTING_PROJECT_CAPABILITY_NOT_IN_CANONICAL_EXPORT — S12. "
             "As with interpretation date, assertion date coincides with extraction date in this "
             "workflow.",
    ),
    32: dict(  # PROV.ASSERTION.LOCATION
        f1="N", f2="N",
        ex="Not represented.",
        expl="Current state: direct inspection establishes no location or organisational context "
             "for the assertion (S01, S02). No project source supports a desired-state "
             "requirement. There is no review committee, panel meeting or curation venue whose "
             "identity would add information; the relevant context is the agent and the procedure, "
             "which are covered by the agent and method rows above.",
    ),
    33: dict(  # PROV.ASSERTION.CONFIDENCE_CATEGORY
        f1="N", f2="M",
        ex="Not represented.",
        expl="Current state: direct inspection establishes no confidence in the asserted claim "
             "(S01, S02). Note the three things the project keeps distinct and that should not be "
             "read as assertion confidence: the statistical uncertainty of a measurement (standard "
             "deviations, confidence intervals, p-values), the AOP weight of evidence on C004 "
             "(EINT.CATEGORICAL_STRENGTH), and the direction of support on an evidence item. "
             "Desired state recorded as M and flagged for human review, for the same reason as "
             "PROV.SA.CONFIDENCE_CATEGORY: the asserting agent is usually an AI agent, so a "
             "confidence value here would largely be model self-report. The project's provisional "
             "view is that derivation (PROV.ASSERTION.METHOD_TYPES) and verifiable quote "
             "provenance serve a consumer better than a claimed confidence, and that this should "
             "be N.",
    ),
    34: dict(  # PROV.ASSERTION.CONFIDENCE_SCORE
        f1="N", f2="N",
        ex="Not represented.",
        expl="Current state: direct inspection establishes no numeric assertion confidence "
             "(S01, S02). No project source supports a desired-state requirement, and the project "
             "positively prefers not to introduce one: a numeric confidence self-reported by an AI "
             "extraction agent would imply a precision the agent cannot justify, and would risk "
             "being consumed as if it were a statistical quantity alongside the genuine p-values "
             "and confidence intervals the project does represent. Marked N rather than M because "
             "the project has a reasoned position against it, not merely an absence of evidence; "
             "the representative should confirm.",
    ),
    # =========================================================== Encoding Provenance
    36: dict(  # PROV.ENCODING.AGENT
        f1="N", f2="M",
        ex="Not represented. The encoding agent is the same AI extraction agent that produced the "
           "content, writing a Container YAML file directly.",
        expl="Current state: no encoding agent is represented (S01, S02). "
             "Desired state recorded as M. In this project encoding is not a separate activity "
             "performed by a separate exporter: the extraction agent writes the YAML file itself, "
             "so encoding provenance largely collapses into assertion provenance, and recording it "
             "separately would duplicate PROV.ASSERTION.AGENT. The project's provisional view is "
             "that the encoding level is not needed for the canonical YAML. It would become "
             "relevant for the generated DuckDB, TSV and workbook products (S08), which ARE "
             "produced by separate named tools, if those products come into scope. Flagged for "
             "human review together with the other encoding rows.",
    ),
    37: dict(  # PROV.ENCODING.METHOD_TYPES
        f1="N", f2="N",
        ex="Not represented.",
        expl="Current state: no encoding method type is represented (S01, S02). No project source "
             "supports a desired-state requirement for the canonical YAML, for the reason given in "
             "PROV.ENCODING.AGENT: the record is hand-authored by the extraction agent in its final "
             "form rather than serialised from an intermediate representation, so there is no "
             "transformation method to record.",
    ),
    38: dict(  # PROV.ENCODING.METHODS
        f1="N", f2="N",
        ex="Not represented.",
        expl="Current state: no encoding specification is represented (S01, S02), and none applies: "
             "the LinkML schema itself is the specification the file conforms to, and conformance is "
             "enforced by validation rather than recorded as provenance. No project source supports "
             "a desired-state requirement.",
    ),
    39: dict(  # PROV.ENCODING.DATE
        f1="N", f2="M",
        ex="Not represented in the canonical data; available from git history.",
        expl="Current state: no encoding date is represented (S01, S02). "
             "Desired state recorded as M, and in this workflow it would be the same date as "
             "extraction, interpretation and assertion. The project would expect one date rather "
             "than four. Flagged for review as part of deciding how far the desired per-file "
             "provenance block should reach across SEPIO's provenance levels.",
    ),
    40: dict(  # PROV.ENCODING.SYSTEM
        f1="N", f2="M",
        ex="Not represented inside the file. Recorded outside it: a verification receipt names the "
           "file it attests to, as kb_file: "
           "\"kb/publications/Container-lkhagvadorj2020-prenatal-smoke-areg-egfr.yaml\".",
        expl="Current state: a canonical file does not identify itself; there is no record "
             "identifier, path or containing-system field (S01, S02). The file's identity is its "
             "path in the repository, which is outside the data. "
             "Desired state recorded as M, with a note that the project has a concrete reason to "
             "want it: the knowledge base deliberately keys records on the source FILE rather than "
             "on the cited publication, because two files may legitimately cite the same paper and "
             "keying on the publication would either collide or silently merge their entities "
             "(S08). A self-identifying record would make that keying explicit rather than "
             "implicit in the file system. Desired-state support: "
             "EXISTING_PROJECT_CAPABILITY_NOT_IN_CANONICAL_EXPORT — S05, S08.",
    ),
    41: dict(  # PROV.ENCODING.VERSION
        f1="N", f2="Y",
        ex="Not represented in the file. Pinned outside it: the project depends on a specific "
           "schema release, soma-schema 0.2.4, pinned in the repository's dependency "
           "specification.",
        expl="Current state: a canonical file does not record which version of the schema it was "
             "authored against (S01, S02). "
             "Desired-state support: EXISTING_PROJECT_CAPABILITY_NOT_IN_CANONICAL_EXPORT — S01 and "
             "S02: the project already pins an exact schema version and treats schema upgrades as "
             "deliberate, coordinated changes, but a file carries no record of the version it was "
             "written for. This is the one encoding-level row the project is confident about, "
             "because the schema evolves and a consumer reading an exported record needs to know "
             "which vocabulary and slot set it was built against.",
    ),
    # =========================================================== Retrieval Provenance
    43: dict(  # PROV.RETRIEVAL.AGENT
        f1="N", f2="Y",
        ex="Not represented. The retrieval agents in use are the project's PubMed search and "
           "reference-fetching scripts, and the reference validator that populates and reads the "
           "committed reference cache.",
        expl="Current state: no retrieval agent is represented (S01, S02). "
             "Desired-state support: EXISTING_PROJECT_CAPABILITY_NOT_IN_CANONICAL_EXPORT — S05, "
             "S06, S07. Retrieval in this project means fetching the publication text that quotes "
             "are later verified against, which makes it unusually consequential: the identity and "
             "behaviour of the fetching tool determines what text exists to check a quote against.",
    ),
    44: dict(  # PROV.RETRIEVAL.SOURCE_SYSTEM
        f1="Y", f2="Y",
        ex="reference: \"PMID:41469766\" — the PMID prefix identifies PubMed as the source system "
           "as well as identifying the record within it.",
        expl="Represented implicitly rather than as a dedicated field. The reference is constrained "
             "by pattern to a PubMed CURIE, so the source system is determined by the identifier "
             "scheme; there is no separate source-system slot. The project retrieves from PubMed "
             "and PubMed Central only, so the single-valued case is adequate today. "
             "Reported as Y on the basis that the system is unambiguously identified, with the "
             "caveat that a consumer must infer it from the CURIE prefix.",
    ),
    45: dict(  # PROV.RETRIEVAL.SOURCE_ROLE
        f1="N", f2="N",
        ex="Not represented.",
        expl="Current state: no source-role distinction is represented (S01, S02). The question "
             "does not arise for this project: there is one source type, the primary publication, "
             "retrieved from PubMed, and no aggregator chain. The project does not ingest from "
             "other knowledgebases, so primary-versus-aggregator has no referent here. No project "
             "source supports a desired-state requirement.",
    ),
    46: dict(  # PROV.RETRIEVAL.TARGET_SYSTEM
        f1="N", f2="N",
        ex="Not represented.",
        expl="Current state: not represented (S01, S02). The target system is the knowledge base "
             "itself, so recording it inside its own records would be uninformative. If the "
             "generated DuckDB, TSV or workbook products came into scope, or if the knowledge base "
             "were ingested downstream, this would become relevant; it is not relevant for the "
             "canonical YAML. No project source supports a desired-state requirement.",
    ),
    47: dict(  # PROV.RETRIEVAL.TARGET_ROLE
        f1="N", f2="N",
        ex="Not represented.",
        expl="Current state: not represented (S01, S02), and not applicable for the same reason as "
             "PROV.RETRIEVAL.TARGET_SYSTEM. No project source supports a desired-state requirement.",
    ),
    48: dict(  # PROV.RETRIEVAL.DATE
        f1="N", f2="Y",
        ex="Not represented in the canonical data. Recorded outside it: a verification receipt "
           "carries content_type_in_committed_cache: \"abstract_only\" and verified_date: "
           "\"2026-09-28\"; and a reference-cache entry records a content_type for each cached "
           "publication.",
        expl="Current state: direct inspection establishes no retrieval date and no record of what "
             "was retrieved (S01, S02). "
             "Desired-state support: EXISTING_PROJECT_CAPABILITY_NOT_IN_CANONICAL_EXPORT — S05 "
             "(verification/PMID_*.json) and S07 (references_cache entries carrying a content_type). "
             "This is a HIGH-VALUE requirement for this project and the clearest case in the "
             "retrieval level. Whether the committed cached copy of a publication is full text or "
             "abstract only materially changes what a quote can be verified against, and it varies "
             "from paper to paper depending on whether the publisher permits automated full-text "
             "retrieval. A consumer reading a record today cannot tell which situation applies. "
             "The project wants the cached copy's content type and retrieval date represented "
             "alongside the quote they bear on.",
    ),
    49: dict(  # PROV.RETRIEVAL.ORIGINAL_NAMES_IDS
        f1="M", f2="Y",
        ex="Partially present: the snippet preserves the publication's own wording verbatim — "
           "snippet: \"FEV1/FVC (measured) 90.06+/-6.19 84.32+/-3.86 0.00\" — while the structured "
           "record expresses the same quantity as fev1_fvc_ratio with unit UO:0000187. There is no "
           "field linking the source string to the normalised term or slot it was mapped to.",
        expl="Current state recorded as M because the answer is genuinely partial. The project "
             "preserves the source representation better than most, since every evidence item "
             "holds the publication's own words verbatim and that text is machine-checked against "
             "the publication (S02, S06). But there is no structured link from a source mention to "
             "the normalised term or measurement slot it was aligned to: the quote and the "
             "structured value sit side by side with no recorded correspondence between them. "
             "Desired-state support: EXISTING_PROJECT_CAPABILITY_NOT_IN_CANONICAL_EXPORT — S11 "
             "(the grounding tooling and report). The project wants that correspondence "
             "representable, because it is what would allow a grounding decision to be audited, "
             "and it is also the missing link that currently prevents any check that a structured "
             "value agrees with the passage quoted beside it.",
    ),
}

prov = {}
for row, r in _rows.items():
    prov[f"G{row}"] = r["f1"]
    prov[f"H{row}"] = r["f2"]
    prov[f"I{row}"] = r["ex"]
    prov[f"J{row}"] = r["expl"]

SHEETS = {PROV: prov}
