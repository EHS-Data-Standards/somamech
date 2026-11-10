"""SOMA answers for EINT (sheet6) and PROV (sheet7).

EINT columns: E=[F1] current, F=[F2] desired, G=[F3] explanation, H=[F4] examples.
PROV columns: G=[F1] current, H=[F2] desired, I=[F5] examples, J=[F6] explanation.
"""

EINT = "xl/worksheets/sheet6.xml"
PROV = "xl/worksheets/sheet7.xml"

# ------------------------------------------------------------------ EINT rows 2-13
_eint = {
    2: dict(  # EINT.REQUIRED
        f1="Y", f2="Y",
        expl="Yes. Every evidence item in the canonical data carries both a direction of support "
             "and a free-text explanation of how the quoted passage bears on the specific claim it "
             "is attached to. The interpretation is recorded on the same object as the evidence "
             "content rather than as a separate judgement object (see EINT.FLAT_COLLAPSE). "
             "The project needs the direction and the explanation preserved; what it does not "
             "currently capture is WHO made the interpretation and WHEN, which is reported under "
             "Evidence Interpretation Provenance.",
        ex="supports: SUPPORT with explanation: \"Table 3 row giving the measured FEV1/FVC values "
           "this assay records for the monsoon and spring visits, with the paired t-test "
           "p-value.\" (E01)",
    ),
    3: dict(  # EINT.DIRECTION
        f1="Y", f2="Y",
        expl="Yes, with a three-value vocabulary that the project needs preserved as it stands: "
             "SUPPORT (the quoted evidence supports the claim), REFUTE (it contradicts the claim), "
             "and NO_EVIDENCE (the cited publication turned out not to contain evidence relevant "
             "to the claim). "
             "IMPORTANT DISTINCTION: NO_EVIDENCE is not a neutral or equivocal direction. It "
             "records a negative retrieval result — the source was consulted and found not to bear "
             "on the claim — which is a statement about relevance rather than about the balance of "
             "evidence. Mapping it onto a 'neutral' value would assert that a non-finding is a "
             "balanced finding, and the project needs the two kept apart. The project has no "
             "separate value for genuinely equivocal evidence and has not needed one so far. "
             "The vocabulary is explicitly direction-only: the schema states that it says nothing "
             "about how strong the evidence is (S02).",
        ex="Across the 40 canonical files: supports: SUPPORT occurs 1312 times, supports: REFUTE "
           "23 times, supports: NO_EVIDENCE once. (One evidence item has an empty value for this "
           "field; the slot is not required by the schema. Flagged for project follow-up.)",
    ),
    4: dict(  # EINT.CATEGORICAL_STRENGTH
        f1="Y", f2="Y",
        expl="Yes, but only for one claim type and on an unexpected carrier, which the modelling "
             "group should note. Key Event Relationship claims (C004) carry two categorical "
             "judgements drawn from the OECD Adverse Outcome Pathway framework: evidence_support "
             "(strong / moderate / weak / not_specified) and quantitative_understanding of the "
             "response-response relationship (high / moderate / low / not_specified). "
             "These are asserted as slots ON THE CLAIM OBJECT, alongside its list of evidence "
             "items, with no representation of which evidence items justify the judgement. So the "
             "project represents the concept of categorical evidence strength, but not as a "
             "property of an interpreted argument. A reading of this row that expected strength to "
             "sit on a per-item or per-argument judgement would wrongly conclude 'not represented'. "
             "The vocabulary is supplied by the external AOP framework rather than chosen by the "
             "project, so it must remain extensible to that framework's terms rather than being "
             "replaced by a generic scale. "
             "No other claim type carries a strength judgement: for C001, C002, C003, C005 and "
             "C006 the project records direction only.",
        ex="KER:ghosh-pi3k-akt-to-suppressed-apoptosis — relationship_type: \"indirectly leads to\", "
           "evidence_support: moderate, with two evidence items attached but no link from the "
           "strength judgement to either of them (E03).",
    ),
    5: dict(  # EINT.NUMERICAL_STRENGTH
        f1="N", f2="M",
        expl="Current state: direct inspection establishes that no numeric evidence-strength score "
             "exists anywhere in the canonical data or schema (S01, S02). The only numeric "
             "uncertainty values in the project are statistical — p-values, confidence intervals, "
             "standard deviations — which describe the measurements themselves and are not "
             "evidence-strength scores. "
             "Desired state is UNRESOLVED and recorded as M pending the project representative's "
             "decision. No project source provides affirmative evidence of a requirement for "
             "numeric strength, and the AOP framework the project follows supplies a categorical "
             "scale, so a numeric score would be invented precision rather than a recorded "
             "judgement. The project's provisional view is that this should be N; it is marked M "
             "rather than N only because the representative has not yet confirmed it.",
        ex="Not represented. No illustrative future example is offered, because the project does "
           "not want to imply a scale it has not decided on.",
    ),
    6: dict(  # EINT.GRANULARITY
        f1="Y", f2="Y",
        expl="The project's current unit of judgement is the individual quoted passage: each "
             "evidence item carries its own direction of support and its own explanation, and "
             "nothing groups several items into a single argument. So the de facto granularity is "
             "one evidence item, one judgement, repeated as a flat list on the claim-bearing "
             "object. Evidence attaches at two levels of the data — to an assay as a whole and to "
             "individual output measurements within it — but in both cases each item is judged "
             "independently. "
             "Desired state, decided by the project representative, is to keep that per-item "
             "granularity for the measurement, comparison, key-event, assay-method and exposure "
             "claim types (C001, C002, C003, C005, C006), and to add grouped arguments for Key "
             "Event Relationship claims (C004), where a weight-of-evidence judgement is genuinely "
             "made over a set of evidence items rather than over each one separately. The project "
             "therefore needs BOTH granularities supported, partitioned by claim type. "
             "Desired-state support: DOCUMENTED_MODEL_INTENT — S02 (aop_framework.yaml places "
             "evidence_support on KeyEventRelationship alongside its evidence list, which is a "
             "group-level judgement expressed without a group object).",
        ex="Current, per item: six evidence items on LF:ghosh-pm25-seasonal-spirometry, each with "
           "its own supports value and explanation. Desired, grouped (ILLUSTRATIVE, not present in "
           "current data): the two evidence items on "
           "KER:ghosh-pi3k-akt-to-suppressed-apoptosis assessed together as one argument carrying "
           "evidence_support: moderate.",
    ),
    7: dict(  # EINT.GROUPING
        f1="N", f2="M",
        expl="Current state: no grouping criteria exist, because no grouping object exists; "
             "evidence items are an unordered flat list on each claim-bearing object (S01, S02). "
             "Desired state is UNRESOLVED and recorded as M. The project's candidate grouping "
             "criterion is the kind of study the evidence comes from, because the canonical data "
             "already classifies every evidence item that way (evidence_source: HUMAN_CLINICAL / "
             "MODEL_ORGANISM / IN_VITRO / COMPUTATIONAL / OTHER), and because the AOP framework "
             "weighs those kinds of evidence differently. A second candidate is grouping by source "
             "publication, which matters once a Key Event accumulates evidence from several papers. "
             "The project has not decided between them, and the distinction between 'three quotes "
             "from one paper as three independent arguments' and 'as three premises of one "
             "argument' is exactly the open question. Flagged for human review rather than "
             "answered.",
        ex="Not represented. The field that would most plausibly drive grouping is present on "
           "every evidence item today: evidence_source: HUMAN_CLINICAL (E01).",
    ),
    8: dict(  # EINT.CONTRADICTION
        f1="Y", f2="Y",
        expl="Yes, and genuinely used rather than merely permitted. The direction vocabulary "
             "includes REFUTE, and it occurs 23 times across the canonical corpus, so the project "
             "does record evidence that argues against claims it represents. "
             "What the project does NOT have is a framework for combining supporting and disputing "
             "evidence into an overall assessment: there is no rule set defining relative weights, "
             "and no overall direction or strength is computed for a claim from its evidence items. "
             "For C004 a single categorical weight-of-evidence judgement is asserted directly, "
             "without a documented procedure for how contradictory items were weighed to reach it. "
             "The project wants disputing evidence to remain representable, and would want any "
             "future aggregation procedure recorded rather than left implicit.",
        ex="supports: REFUTE occurs 23 times across kb/publications/*.yaml, alongside 1312 "
           "SUPPORT items.",
    ),
    9: dict(  # EINT.STACKING
        f1="N", f2="M",
        expl="Current state: direct inspection establishes no nested or higher-order evidence "
             "assessment; there is no evidence-line object at all, so there is nothing to stack "
             "(S01, S02). "
             "Desired state is UNRESOLVED and recorded as M. Stacking would be the natural way to "
             "express an AOP weight-of-evidence judgement that caps the contribution of a category "
             "of evidence — for example limiting what in-vitro evidence alone can establish about a "
             "causal linkage between key events — and the project's evidence_source classification "
             "provides the categories such a cap would apply to. But no project document states "
             "this as a requirement, and the project has not adopted a scoring framework that would "
             "need it. Depends on the same unresolved decision as EINT.GROUPING; flagged for human "
             "review.",
        ex="Not represented.",
    ),
    10: dict(  # EINT.DISTINCT_MODELS
        f1="Y", f2="Y",
        expl="Yes. The project's claim types do not share one evidence model, and this is the "
             "single most important structural finding of this review for the modelling group. "
             "Five claim types (C001 measurement, C002 comparison, C003 key event, C005 assay "
             "method, C006 exposure condition) share one profile: flat evidence items, each a "
             "verbatim quote with a direction of support and an explanation, judged individually, "
             "with no strength assessment. "
             "One claim type (C004, Key Event Relationship) needs a different profile: a "
             "categorical weight-of-evidence and quantitative-understanding judgement over a GROUP "
             "of evidence items, drawn from the OECD AOP framework, with the grouping and the "
             "judging agent represented. "
             "A SEPIO-based representation therefore needs to support both a lightweight flat form "
             "and a grouped interpreted form, selected per claim type, rather than imposing one "
             "model on all claims. The provenance requirements, by contrast, are uniform across all "
             "six claim types, because every file is produced by the same AI-assisted extraction "
             "workflow.",
        ex="Compare LF:ghosh-pm25-seasonal-spirometry (six flat evidence items, no strength) with "
           "KER:ghosh-pi3k-akt-to-suppressed-apoptosis (two evidence items plus evidence_support: "
           "moderate asserted over them collectively).",
    ),
    11: dict(  # EINT.FLAT_COLLAPSE
        f1="Y", f2="Y",
        expl="Yes, and the project requires the flat form to be preserved for most of its claims. "
             "A single EvidenceItem object carries the evidence content and the interpretation "
             "together: reference and reference_title identify the source, snippet holds the "
             "verbatim passage, evidence_source records the kind of study it came from, "
             "and supports plus explanation record the judgement about it. There is no separate "
             "interpretation object and no provenance tracked separately for the interpretation. "
             "This is an intentional implementation preference, not an accident: the extraction "
             "agents emit this shape, the reference and term validators check it, the DuckDB "
             "builder and the pooled workbook read it, and the per-paper review site renders it "
             "(S03, S06, S08, S09). Replacing it wholesale would require changing all of those. "
             "Desired: preserve the flat form for C001, C002, C003, C005 and C006; support a "
             "separated evidence-item-plus-interpretation form for C004. See EINT.DISTINCT_MODELS.",
        ex="One complete evidence item, showing content and interpretation in one object: "
           "{reference: \"PMID:41469766\", reference_title: \"Seasonal impact of PM(2.5) ...\", "
           "supports: SUPPORT, evidence_source: HUMAN_CLINICAL, snippet: \"FEV1/FVC (measured) "
           "90.06+/-6.19 84.32+/-3.86 0.00\", explanation: \"Table 3 row giving the measured "
           "FEV1/FVC values ...\"} (E01)",
    ),
    12: dict(  # EINT.DIRECT_EVIDENCE
        f1="Y", f2="Y",
        expl="Yes. This is how all evidence is attached in the canonical data: a claim-bearing "
             "object points directly at its evidence items. The four classes that carry an evidence "
             "list are Assay, AssayOutputMeasurement, KeyEvent and KeyEventRelationship (S02). "
             "The project needs this direct linkage preserved, including the direction of support "
             "carried on each item. Note that the project's direct links DO carry a direction, so "
             "this is not a bare citation: it is a lightweight interpretation attached to a direct "
             "link, which is why EINT.FLAT_COLLAPSE is also marked Y.",
        ex="lung_function_assays[0].evidence — a list of six evidence items attached directly to "
           "the assay; and separately, evidence attached to individual output measurement records "
           "within the same assay.",
    ),
    13: dict(  # EINT.SOURCE_ONLY
        f1="Y", f2="Y",
        expl="Yes, at file level. Every Container declares source_publication — the single "
             "publication the whole file was extracted from — as a reference, title and DOI, "
             "without naming any specific evidence item. That is a claim-to-source link "
             "independent of the per-item evidence, and it is what makes each file traceable to "
             "one publication. "
             "The project needs both: the file-level source declaration and the per-item evidence "
             "with its own repeated publication reference. The per-item repetition is deliberate, "
             "so that a quote remains attributable to its source if it is read outside the file "
             "it sits in — which is what the DuckDB and workbook exports do (S08).",
        ex="source_publication: {reference: \"PMID:41469766\", reference_title: \"Seasonal impact of "
           "PM(2.5) on pro-oncogenic drivers among participants of a thermal power plant in "
           "India.\", doi: \"10.1038/s41598-025-33906-7\"}",
    ),
}

eint = {}
for row, r in _eint.items():
    eint[f"E{row}"] = r["f1"]
    eint[f"F{row}"] = r["f2"]
    eint[f"G{row}"] = r["expl"]
    eint[f"H{row}"] = r["ex"]

SHEETS = {EINT: eint}
