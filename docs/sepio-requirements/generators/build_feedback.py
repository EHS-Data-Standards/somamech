"""Build the SOMA project feedback log from SEPIO's Feedback_Log_Template.xlsx.

Usage:
    python build_feedback.py <blank Feedback_Log_Template.xlsx> [output .xlsx]

The template is SEPIO's own, from
https://github.com/sepio-framework/sepio-linkml/tree/main/docs/requirements-collection

Re-runnable: edit OBSERVATIONS and re-run to regenerate the workbook. Only the
agent-owned columns A-V are written; the governance columns W-AD are left blank
for the consortium's consolidation step, per the template's Agent Instructions.
"""
from copy import copy
from pathlib import Path
import sys

import openpyxl
from openpyxl.styles import Alignment

DEFAULT_OUT = (
    Path(__file__).resolve().parents[1] / "SOMA_Requirements_Feedback_Log_v0.1_20261109_1130.xlsx"
)

PROJECT = "SOMA / somamech (EHS-Data-Standards)"
RUN = "SOMA-20261109-R01"
FORMS_V = "Requirements_Collection_Forms.xlsx @ sepio-linkml main (sha256 22e6c85a...)"
GUIDE_V = "Requirements_Instructions_and_Guidance_for_AI.md (sha256 8a39ffdb...); QUICK_START + RESOURCE_INVENTORY_GUIDANCE same commit"
AGENT = "Claude Code (Opus 5), directed by S. Moxon"
DATE = "2026-11-09"

# A-V, in sheet column order; A-G and the date are filled in automatically.
OBSERVATIONS = [
    dict(
        id="OBS-001",
        stage="Requirements elicitation",
        component="SEPIO LinkML model",
        other="Requirements forms",
        reqs="EINT.FLAT_COLLAPSE; EINT.REQUIRED; EINT.DIRECTION",
        category="Model coverage gap",
        finding=(
            "SOMA's evidence model is exactly the flat shape EINT.FLAT_COLLAPSE describes, and the mapping "
            "registry already records it as a SEPIO gap. One EvidenceItem object carries both the evidence "
            "item content (snippet, the verbatim quote) and the interpretation of it (supports: "
            "SUPPORT/REFUTE/NO_EVIDENCE, explanation). There is no EvidenceLine-like object anywhere in the "
            "schema, and nothing groups items into arguments. So the project's F1 answer is a flat collapse, "
            "and the registry's own note says the transform to InformationEntity + EvidenceLine is "
            "'not automatic'."
        ),
        evidence=(
            "soma/src/soma/schema/evidence.yaml, class EvidenceItem, slots: reference, reference_title, "
            "supports, evidence_source, snippet, explanation, article_section, figure_reference. "
            "Registry summary for EINT.FLAT_COLLAPSE: 'Current SEPIO gap - no native single object that "
            "collapses Evidence Item content and EvidenceLine interpretation.'"
        ),
        suggestion=(
            "Confirms the gap from a second, independent project. Worth deciding whether SEPIO offers a "
            "sanctioned flat profile (e.g. a FlatEvidenceAssertion class, or a documented pattern where an "
            "EvidenceLine with exactly one evidence item is the canonical encoding of the flat form) rather "
            "than leaving each project to invent its own transform. A LinkML-Map recipe for the 1-item "
            "EvidenceLine case shipped with SEPIO would make this mechanical."
        ),
        entry="Observed challenge",
        applicability="Potentially cross-project",
        priority="High",
        confidence="High",
        impact=(
            "Decides whether SOMA's ~41 kb files can round-trip through SEPIO without an EvidenceLine "
            "explosion: the corpus has thousands of evidence items, each currently one object."
        ),
        source="soma repo: src/soma/schema/evidence.yaml (lines 48-68)",
        related="OBS-005",
    ),
    dict(
        id="OBS-002",
        stage="Requirements elicitation",
        component="Requirements forms",
        other="Requirements guidance",
        reqs="EI.DATA.EXPERIMENTAL_OBSERVATIONAL; EI.COMPOSITE.DATA_TABLE; EI.PRIOR_CLAIM.DIRECT_TEXT; EI.PRIOR_CLAIM.SUPPORTING_TEXT",
        category="Ambiguous definition",
        finding=(
            "No evidence item type names a verbatim quoted source passage, which is this project's unit of "
            "evidence representation and addressability. The two text-passage rows "
            "(EI.PRIOR_CLAIM.DIRECT_TEXT, EI.PRIOR_CLAIM.SUPPORTING_TEXT) are both scoped to passages "
            "reporting a prior CLAIM. A quoted table row reporting numbers is not a prior claim, and it is "
            "also not cleanly a Data Item when what the project stores and verifies is the text rather than "
            "the parsed value. "
            "CORRECTED FROM AN EARLIER DRAFT OF THIS LOG: the guidance does resolve how to ANSWER this. The "
            "EIT preamble states that one evidence item may correspond to several categories and instructs "
            "the respondent to select all applicable types and explain the overlap, and the F4 FREE_TEXT "
            "option is defined with an example that is almost exactly this project's case. So the form is "
            "answerable. The residual issue is narrower and still real: a project whose primary evidence unit "
            "is the quoted passage must introduce it as a custom row (we used EI.CUSTOM.001), which costs the "
            "cross-project comparability the predefined taxonomy exists to provide."
        ),
        evidence=(
            "Real evidence item from kb/publications/Container-ghosh2025-pm25-egfr-pi3k-akt.yaml: "
            "snippet: 'FEV1/FVC (measured) 90.06+/-6.19 84.32+/-3.86 0.00', article_section: table, "
            "explanation: 'Table 3 row giving the measured FEV1/FVC values ... with the paired t-test p-value.' "
            "That one string carries two group means, two SDs and a p-value, quoted out of a table, as text."
        ),
        suggestion=(
            "Consider adding a predefined evidence item type for a quoted source passage, distinct from the "
            "data it reports and from prior-claim passages, since any project doing literature extraction "
            "will need it. Alternatively, state a disambiguation rule in the guidance: classify by what the "
            "project stores, verifies and addresses, not by what the passage is about. Either way, the "
            "guidance's existing allowance for multiple selections plus FREE_TEXT should be referenced "
            "directly from the EIT form rows, not only in the preamble, because an agent reading row by row "
            "can miss it."
        ),
        entry="Suggested enhancement",
        applicability="Potentially cross-project",
        priority="Medium",
        confidence="High",
        impact=(
            "Does not block form completion. Costs comparability: this project's primary evidence item type "
            "is reported as EI.CUSTOM.001 and so will not align with any other project's rows without manual "
            "reconciliation."
        ),
        source="forms: 'EIT 5-Evidence Item Type Form' rows A11-A14 vs A2; somamech: kb/publications/*.yaml",
        related="OBS-003",
    ),
    dict(
        id="OBS-003",
        stage="Requirements elicitation",
        component="SEPIO LinkML model",
        other="Mapping registry",
        reqs="PROV.EI.RETRIEVAL_SOURCE; EI.COMPOSITE.FIGURE",
        category="Provenance granularity",
        finding=(
            "There is no provenance type for WHERE INSIDE a source document an evidence item was taken from. "
            "SOMA records this on every evidence item and treats it as load-bearing for how much the evidence "
            "counts: article_section (abstract/methods/results/discussion/figure_caption/table/supplementary) "
            "and figure_reference (e.g. 'Figure 3B', 'Table 2'). The schema's own comment states the point - a "
            "dose quoted from Methods storage boilerplate is weaker provenance than one quoted from Results. "
            "PROV.EI.RETRIEVAL_SOURCE maps to InformationEntity.sources but identifies the document, not the "
            "locus within it."
        ),
        evidence=(
            "soma evidence.yaml slots article_section (range ArticleSectionEnum, 9 values) and figure_reference. "
            "Example: snippet 'FEV1/FVC (measured) 90.06+/-6.19 84.32+/-3.86 0.00' with article_section: table. "
            "No PROV row in the form, and no registry target, corresponds to either slot."
        ),
        suggestion=(
            "Add a within-source locus to evidence item provenance (section type plus a source-labelled "
            "figure/table reference). This is also the practical substitute for EI.COMPOSITE.FIGURE when a "
            "value lives only in a chart: SOMA deliberately records no number but names the figure so a "
            "reviewer can find it."
        ),
        entry="Suggested enhancement",
        applicability="Potentially cross-project",
        priority="Medium",
        confidence="High",
        impact=(
            "Without it, the section/figure qualifiers are dropped on transform, and the project loses the "
            "distinction it uses to weigh evidence."
        ),
        source="soma repo: src/soma/schema/evidence.yaml (lines 135-151, 197-235)",
        related="OBS-002",
    ),
    dict(
        id="OBS-004",
        stage="Requirements elicitation",
        component="Requirements forms",
        other="SEPIO LinkML model; Requirements guidance",
        reqs="PROV.SA.REVIEW; PROV.EI.QUALITY; PROV.EI.METHODS",
        category="Missing requirement",
        finding=(
            "No provenance type covers mechanical verification of an evidence item against a stored copy of "
            "its source. SOMA's central quality control is exactly that: a validator checks that every snippet "
            "appears word-for-word in a cached copy of the cited publication and that reference_title matches "
            "the real title, which converts 'verify the extraction' from a judgment call into a machine check. "
            "PROV.SA.REVIEW is the nearest row but is about a human reviewing an automated semantic alignment "
            "(who approved it, what they changed), not an automated verbatim-quote check. PROV.EI.QUALITY is "
            "about the scientific rigour of the underlying study, not whether the quote was faithfully copied."
        ),
        evidence=(
            "soma evidence.yaml: snippet 'implements: linkml:excerpt', reference 'implements: "
            "linkml:authoritative_reference', reference_title 'implements: dcterms:title'; "
            "somamech: 'just verify-snippets' (linkml-reference-validator) and verification/PMID_32783621.json "
            "recording verified_with, verified_date: 2026-09-28, content_type_in_committed_cache: abstract_only, "
            "and 15 snippet_sha256 hashes."
        ),
        suggestion=(
            "Add a verification/faithfulness provenance area distinct from both human review and intrinsic "
            "information quality: what was checked, by what tool and version, against what copy of the source, "
            "when, with what outcome. For AI-extracted knowledge this is the provenance a consumer most wants, "
            "and it is cheap to represent."
        ),
        entry="Observed challenge",
        applicability="Potentially cross-project",
        priority="High",
        confidence="High",
        impact=(
            "This is the project's main trust signal. If the requirements forms cannot express it, the covering "
            "model will not carry it, and SOMA's chief advantage over an unverified extraction becomes invisible "
            "downstream."
        ),
        source="somamech: verification/*.json, justfile verify-snippets; soma: src/soma/schema/evidence.yaml",
        related="OBS-008",
    ),
    dict(
        id="OBS-005",
        stage="Requirements elicitation",
        component="Mapping registry",
        other="SEPIO LinkML model",
        reqs="EINT.CATEGORICAL_STRENGTH; EINT.REQUIRED; PROV.ASSERTION.CONFIDENCE_CATEGORY",
        category="Mapping mismatch",
        finding=(
            "SOMA carries categorical evidence strength on the CLAIM, not on an evidence line. "
            "KeyEventRelationship has evidence_support (strong/moderate/weak/not_specified) and "
            "quantitative_understanding (high/moderate/low/not_specified) as slots of the relationship itself, "
            "alongside its evidence list. The registry maps EINT.CATEGORICAL_STRENGTH to "
            "EvidenceLine.strengthOfEvidenceProvided, so a literal reading of F1 would say 'not represented', "
            "which is wrong: the project represents the concept, on a different carrier. "
            "PROV.ASSERTION.CONFIDENCE_CATEGORY (Statement.strength) is arguably the better target, but these "
            "are OECD AOP weight-of-evidence calls about a relationship, not a curator's confidence in a claim."
        ),
        evidence=(
            "soma aop_framework.yaml, KeyEventRelationship slots: upstream_event, downstream_event, "
            "relationship_type, evidence_support, quantitative_understanding, evidence. "
            "EvidenceSupportEnum: strong/moderate/weak/not_specified. "
            "QuantitativeUnderstandingEnum: high/moderate/low/not_specified."
        ),
        suggestion=(
            "The strength questions need a carrier axis the way EIT has a location axis: is strength asserted "
            "per evidence line, per claim, or both? Otherwise F1 answers conflate 'we do not do this' with "
            "'we do this somewhere else'. Also worth noting that domain frameworks (OECD AOP) supply their own "
            "fixed strength vocabularies, so an extensible enum matters more than SEPIO's own scale."
        ),
        entry="Observed challenge",
        applicability="Potentially cross-project",
        priority="Medium",
        confidence="High",
        impact="Affects F1 accuracy on three EINT rows and the choice of covering-model carrier for strength.",
        source="soma repo: src/soma/schema/aop_framework.yaml (KeyEventRelationship; EvidenceSupportEnum)",
        related="OBS-001",
    ),
    dict(
        id="OBS-006",
        stage="Requirements elicitation",
        component="Requirements forms",
        other="Requirements guidance",
        reqs="C001+ (Claim Type Form); CS.PARENT_SLOT_VALUE; CS.NESTED_OBJECT",
        category="Workflow / usability",
        finding=(
            "The Claim Type form asks for subject category, object category and relationship type per claim "
            "type, which presupposes claims shaped like SPO associations. SOMA has no reified claim object at "
            "all: evidence attaches to four parent classes (Assay, AssayOutputMeasurement, KeyEvent, "
            "KeyEventRelationship), and in three of those four the 'claim' is implicit in the parent record "
            "plus its slot values - e.g. 'in this assay, under this exposure condition, this measurement had "
            "this value'. Only KeyEventRelationship is natively SPO-shaped. Enumerating claim types therefore "
            "requires inventing the claims first, which is a modeling act the forms treat as a reporting act."
        ),
        evidence=(
            "Classes carrying the evidence slot (grep of soma schema): assay_base.yaml Assay, "
            "assay_base.yaml AssayOutputMeasurement, aop_framework.yaml KeyEvent, "
            "aop_framework.yaml KeyEventRelationship. Container (tree_root) carries only source_publication "
            "plus collections; no claim class exists."
        ),
        suggestion=(
            "Add guidance for projects whose claims are implicit (CS.PARENT_SLOT_VALUE / CS.NESTED_OBJECT): "
            "state that claim types should be enumerated as the propositions a consumer could extract, name "
            "the parent record and slot that imply each one, and flag that the subject/relationship columns "
            "may be reconstructions rather than fields that exist. An illustrative measurement-shaped claim "
            "type in the examples would help; both current examples are association-shaped."
        ),
        entry="Observed challenge",
        applicability="Potentially cross-project",
        priority="Medium",
        confidence="High",
        impact=(
            "Gates every downstream form: EIT F10, EINT F4 and the whole Claim-Evidence Matrix key off claim "
            "type IDs that are a judgment call for this project."
        ),
        source="forms: 'CT 2-Claim Type Form'; soma repo: schema class/slot inventory",
        related="OBS-007",
    ),
    dict(
        id="OBS-007",
        stage="Inventory and scope",
        component="Resource inventory / scope",
        other="Requirements forms; Requirements guidance",
        reqs="PROV.SA.* (all); PROV.ASSERTION.* (all); PROV.ENCODING.* (all); PROV.RETRIEVAL.* (all)",
        category="Source evidence / scope",
        finding=(
            "The canonical data files carry no agent, date, method or version provenance of any kind. "
            "Container's only provenance slot is source_publication (PMID, title, DOI). Everything about who "
            "or what produced the file - which AI agent and model, the extraction skill and its version, the "
            "human who directed and reviewed it, when, and against which cached copy of the paper - lives "
            "outside the YAML, in git history, pull-request records, the claim-paper skill definition and the "
            "verification receipts. So F1 is N across roughly thirty PROV rows while the project demonstrably "
            "HAS the information, which is the EXISTING_PROJECT_CAPABILITY_NOT_IN_CANONICAL_EXPORT case for F2. "
            "The repository is explicit that the content is AI-generated and that a human name on a commit "
            "means direction and review, not authorship - precisely the distinction the PROV form wants, "
            "recorded nowhere a data consumer can read it."
        ),
        evidence=(
            "soma soma.yaml Container slots: source_publication, key_events, key_event_relationships, "
            "adverse_outcome_pathways, response_comparisons, 11 assay collections, protocols. No agent, date, "
            "version or method slot. somamech README: 'A person's name on a commit, pull request, issue, or "
            "knowledge-base entry does not mean that person authored the content themselves.' "
            "Extraction provenance exists as: .claude/skills claim-paper, git history, PR records, "
            "verification/*.json."
        ),
        suggestion=(
            "Two things. (1) The forms would benefit from asking, per provenance level, where the information "
            "lives now (in the data / in the repository but not the data / not captured), because "
            "'N' plus a desired-state support type compresses a distinction the modelers will want. "
            "(2) For this project the finding is actionable in its own right: a per-file provenance block is "
            "the single largest EPC gap, and it is a schema change in the soma repo rather than a SEPIO issue."
        ),
        entry="Observed challenge",
        applicability="Potentially cross-project",
        priority="High",
        confidence="High",
        impact=(
            "Determines the scope choice. A minimal scope (canonical YAML only) yields an almost empty "
            "provenance requirement set and would badly understate the project; a maximal scope is needed for "
            "the PROV forms to be meaningful."
        ),
        source="soma repo: src/soma/schema/soma.yaml (Container, lines 60-96); somamech README.md",
        related="OBS-004; OBS-008",
    ),
    dict(
        id="OBS-008",
        stage="Requirements elicitation",
        component="Requirements forms",
        other="Requirements guidance",
        reqs="PROV.EI.* / PROV.SA.* / PROV.INTERP.* / PROV.ASSERTION.* / PROV.ENCODING.* (Agent, Methods, Date rows)",
        category="Provenance granularity",
        finding=(
            "The five provenance levels cannot be declared coincident, which inflates the form for any "
            "single-pass AI curation workflow. SEPIO's levels assume distinct activities with potentially "
            "distinct agents, methods and dates. In this project one AI agent, in one activity, at one time, "
            "performs the semantic alignment, the evidence interpretation, the assertion and the encoding; a "
            "human then reviews the result. Filling Agent, Method Types, Specific Methods and Date across the "
            "alignment, interpretation, assertion and encoding levels therefore means answering roughly "
            "sixteen rows that all want the same three values, with no way to say so once."
        ),
        evidence=(
            "PROV rows answered with the same desired-state value and substantially the same justification: "
            "PROV.SA.AGENT, PROV.INTERP.AGENT, PROV.ASSERTION.AGENT (and PROV.ENCODING.AGENT, marked M "
            "precisely because encoding is not a separate activity here); PROV.SA.DATE, PROV.INTERP.DATE, "
            "PROV.ASSERTION.DATE, PROV.ENCODING.DATE. The project's own workflow: the claim-paper extraction "
            "skill produces the structured record, its ontology groundings, its evidence quotes and its "
            "direction-of-support judgements in a single pass, and writes the YAML file directly - there is no "
            "separate exporter step."
        ),
        suggestion=(
            "Add a way to declare that two or more provenance levels coincide for a given project - either a "
            "single row per level asking 'is this level distinct from the previous one for your project?', or "
            "guidance instructing agents to answer the first applicable level and cross-reference the rest. "
            "This will recur for every AI-assisted curation project in the consortium, and it affects "
            "modelling directly: a covering model that provisions independent Contribution objects per level "
            "would be heavier than such a workflow warrants."
        ),
        entry="Observed challenge",
        applicability="Potentially cross-project",
        priority="High",
        confidence="High",
        impact=(
            "Affects roughly sixteen PROV rows for this project and would affect any project whose curation is "
            "a single automated pass. Risks the modelling group reading four independent provenance "
            "requirements where there is one."
        ),
        source="forms: 'PROV 7-Provenance Types Form'; guidance Section II (Five Levels of Claim Provenance); "
               "somamech: .claude/skills/claim-paper/SKILL.md",
        related="OBS-007; OBS-011",
    ),
    dict(
        id="OBS-009",
        stage="Requirements elicitation",
        component="SEPIO LinkML model",
        other="Mapping registry",
        reqs="PROV.EI.GENERATION_CONTEXT",
        category="Model coverage gap",
        finding=(
            "PROV.EI.GENERATION_CONTEXT is a requirement this project already implements as a required "
            "single-term field, and the registry records no single SEPIO slot for it. Every SOMA evidence item "
            "carries evidence_source with values HUMAN_CLINICAL, MODEL_ORGANISM, IN_VITRO, COMPUTATIONAL, OTHER "
            "- the kind of study the cited publication reports. The schema also pins down a subtlety the form "
            "does not: the value classifies the paper, not the agent doing the extraction."
        ),
        evidence=(
            "soma evidence.yaml slot evidence_source, range EvidenceSourceEnum (5 values), with the comment "
            "'classify the paper, not the person doing the extraction'. Registry summary for "
            "PROV.EI.GENERATION_CONTEXT: 'Partial SEPIO coverage - no single slot for "
            "study/experiment/model-system generation context.' In use on every evidence item in all 41 kb files."
        ),
        suggestion=(
            "Independent second-project confirmation that this gap is worth closing with a first-class slot "
            "rather than a typed Activity, since projects use it as a cheap required categorical. Consider also "
            "stating in the description whose context is being classified - the source study's, not the "
            "extracting agent's - which is ambiguous as written."
        ),
        entry="Observed challenge",
        applicability="Potentially cross-project",
        priority="Medium",
        confidence="High",
        impact="A high-use, low-cost field that would otherwise transform into a verbose Activity pattern.",
        source="soma repo: src/soma/schema/evidence.yaml (lines 114-118, 237-261)",
        related="",
    ),
    dict(
        id="OBS-010",
        stage="Requirements elicitation",
        component="Requirements forms",
        other="SEPIO LinkML model",
        reqs="EINT.DIRECTION",
        category="Response options",
        finding=(
            "The project's direction vocabulary has a third value that is not 'neutral'. SOMA's "
            "EvidenceItemSupportEnum is SUPPORT / REFUTE / NO_EVIDENCE, where NO_EVIDENCE means the cited "
            "publication turned out not to contain evidence relevant to the claim. That is a statement about "
            "relevance, or about a failed retrieval, not about evidence that bears on the claim without "
            "favouring either side. The form's illustrative vocabulary (Supports, Disputes, Neutral) invites "
            "mapping NO_EVIDENCE onto Neutral, which would assert that a non-finding is a balanced finding."
        ),
        evidence=(
            "soma evidence.yaml EvidenceItemSupportEnum: SUPPORT ('supports the claim'), REFUTE "
            "('contradicts the claim'), NO_EVIDENCE ('The cited publication turned out not to contain evidence "
            "relevant to the claim'). Form EINT.DIRECTION example response: 'prefer a terminology to capture "
            "directions like Supports, Disputes, Neutral'."
        ),
        suggestion=(
            "Ask explicitly whether the project needs to distinguish 'neutral/equivocal evidence' from "
            "'no relevant evidence found', and whether the latter is direction or relevance. A negative "
            "retrieval result is useful to record and easy to lose in a direction enum."
        ),
        entry="Suggested enhancement",
        applicability="Potentially cross-project",
        priority="Medium",
        confidence="Medium",
        impact="Small but silent: a wrong mapping here changes the meaning of recorded evidence.",
        source="soma repo: src/soma/schema/evidence.yaml (lines 180-195); forms: EINT row A3",
        related="",
    ),
    dict(
        id="OBS-011",
        stage="Requirements elicitation",
        component="Requirements forms",
        other="Requirements guidance",
        reqs="EIT F5 (Individual Addressability Needed?); EI.DATA.EXPERIMENTAL_OBSERVATIONAL; EI.CUSTOM.001",
        category="Ambiguous definition",
        finding=(
            "EIT F5 (individual addressability) cannot be answered honestly when the addressable unit sits at "
            "a different granularity from the evidence item type being assessed. In this project an individual "
            "measurement is NOT separately addressable - it is a named slot on an output record with no "
            "identifier of its own - but the quoted passage that reports it IS addressable, and carries the "
            "direction of support, the article section and the curator's explanation. Answering F5 per row "
            "forces a choice that misreports one or the other: YES overstates the measurement's status, NO "
            "hides that the project does attach interpretation metadata at a specific granularity."
        ),
        evidence=(
            "soma schema: AssayOutputMeasurement has an id, but the individual measured values within it are "
            "named slots (fvc, fev1, fev1_fvc_ratio) carrying inline QuantityValue objects with no identifiers. "
            "EvidenceItem has no id slot either, yet it is the object that direction and explanation attach to. "
            "So neither the measurement nor the passage has a literal identifier, while the passage is "
            "nonetheless the de facto unit of judgement. This is part of why EI.CUSTOM.001 was added for this "
            "project."
        ),
        suggestion=(
            "Split F5 into 'must this item be individually identified?' and 'must metadata be attachable to "
            "this item specifically?'. The two come apart whenever a project attaches interpretation to an "
            "object it does not mint identifiers for, which is common in document-derived data. Alternatively, "
            "add a short note to F5 telling respondents to answer for the granularity at which the project "
            "attaches provenance and interpretation, and to say so in F9."
        ),
        entry="Observed challenge",
        applicability="Potentially cross-project",
        priority="Medium",
        confidence="High",
        impact=(
            "Affects every EIT row the project marked LOCAL, and the answer feeds directly into whether a "
            "covering model needs first-class identified evidence objects."
        ),
        source="forms: 'EIT 5-Evidence Item Type Form' column J; soma repo: src/soma/schema/evidence.yaml, "
               "assay_base.yaml",
        related="OBS-002",
    ),
    dict(
        id="OBS-012",
        stage="Requirements elicitation",
        component="Requirements forms",
        other="Collection workflow",
        reqs="CEM 8 (Claim-Evidence Matrix)",
        category="Workflow / usability",
        finding=(
            "The Claim-Evidence Matrix cannot be completed in place for a project with more than five evidence "
            "item types or six claim types, and enlarging it conflicts with the workbook-handling rules. The "
            "CEM sheet's illustrative example is bound to an Excel Table whose range is A3:F9, giving five "
            "evidence columns and six claim rows. This project reports six claim types and nine evidence item "
            "types marked Y, so the matrix does not fit. Extending the table range would alter template "
            "structure, which rules 36-40 of the form prompt instruct the agent not to do, and rule 39 says to "
            "stop and report rather than rebuild."
        ),
        evidence=(
            "xl/tables/table7.xml ref=\"A3:F9\" bound to the CEM worksheet. Completed SOMA forms: 6 claim "
            "types (C001-C006) and 9 evidence item types with F2=Y. Resolution adopted: the SOMA matrix was "
            "written below the template's example starting at row 12, outside the table range, clearly "
            "labelled, and the deviation was declared in the Review Memo."
        ),
        suggestion=(
            "Either size the CEM table generously as the other six form tables already are (CT is A1:AB70, "
            "EIT A1:AH30, PROV A1:AE55 - all with ample spare rows, which made those sheets straightforward "
            "to populate safely), or state in the guidance that the CEM is expected to be delivered as a "
            "separate generated artifact rather than filled in place. The sheet's own note says the matrix "
            "will be generated automatically, which suggests the second option is the intent; if so, saying "
            "so in REQUIREMENTS_FORM_PROMPT.md deliverable list would remove the ambiguity."
        ),
        entry="Observed challenge",
        applicability="Potentially cross-project",
        priority="Medium",
        confidence="High",
        impact=(
            "Any project with a moderately rich evidence profile hits this. Agents may respond by silently "
            "resizing the table, which is exactly what the formatting-preservation rules exist to prevent."
        ),
        source="forms: 'CEM 8-Claim-Evidence Matrix For', xl/tables/table7.xml; "
               "REQUIREMENTS_FORM_PROMPT.md rules 36-40",
        related="",
    ),
    dict(
        id="OBS-013",
        stage="Requirements elicitation",
        component="Requirements forms",
        other="",
        reqs="C001-C006 (Claim Type Form); guidance 'How to Define / Distinguish Claim Types'",
        category="Response options",
        finding=(
            "The Claim Type form has no structured way to record that several claim types share one "
            "evidence/provenance profile. The guidance is clear that claim types should be split only where "
            "EPC requirements materially differ, and that the minimum number needed should be used. But a "
            "project representative may have good organisational reasons to enumerate more - and this project "
            "did, reporting six claim types where four would have exposed the same EPC differences. The only "
            "place to record that five of the six share one profile and one differs is free text in the "
            "Evidence/Provenance Notes and Additional Notes columns, which a downstream registry cannot read."
        ),
        evidence=(
            "This project's completed CT form: C001, C002, C003, C005 and C006 share one evidence profile "
            "(flat per-item evidence, direction only, no strength); C004 requires a grouped, strength-bearing "
            "profile. That distinction is the single most important structural finding for the modelling "
            "group, and it is currently stated only in prose in CT column H, EINT.DISTINCT_MODELS F3, and the "
            "Review Memo."
        ),
        suggestion=(
            "Add an optional 'EPC profile group' column to the Claim Type form - a short free label that "
            "respondents reuse across rows sharing one profile. It costs one column, needs no controlled "
            "vocabulary, and would let the mapping stage see profile partitioning directly rather than "
            "inferring it from EINT.DISTINCT_MODELS plus prose."
        ),
        entry="Suggested enhancement",
        applicability="Potentially cross-project",
        priority="Medium",
        confidence="Medium",
        impact=(
            "Determines whether the modelling group correctly reads one covering model with a profile split "
            "versus six uniform claim types."
        ),
        source="forms: 'CT 2-Claim Type Form'; guidance lines 69-71, 313-333",
        related="OBS-006",
    ),
    dict(
        id="OBS-014",
        stage="Requirements elicitation",
        component="Requirements forms",
        other="Requirements guidance",
        reqs="EIT F3; EIT F4; EIT F5; EIT F6",
        category="Other",
        finding=(
            "POSITIVE PATTERN, recorded so it is not lost in a future revision. The EIT form's decomposition "
            "of evidence representation into four separate questions - where does the item live (F3), what "
            "local representation form is needed (F4), must individual instances be addressable (F5), and "
            "what intrinsic attributes must it carry (F6) - was the most productive part of this exercise. It "
            "forced the project to articulate a distinction it had never written down: that a quoted passage "
            "and the measurement it reports are represented at different levels, one as verified free text and "
            "one as structured content, and that nothing currently checks the two agree."
        ),
        evidence=(
            "The distinction surfaced while answering F4 for EI.DATA.EXPERIMENTAL_OBSERVATIONAL "
            "(FREE_TEXT;STRUCTURED_CONTENT) and is now recorded in that row's F9 explanation. It is a real "
            "gap in the project's own verification story that the requirements exercise exposed, independent "
            "of any SEPIO mapping. The guidance's summary line - 'where does it live? -> what representation "
            "is needed? -> must it be first-class/addressable? -> what properties must it carry?' - is an "
            "unusually clear framing."
        ),
        suggestion=(
            "Retain this decomposition, and consider applying the same four-way split to the EINT form, which "
            "currently mixes 'do you need this?' with 'at what granularity?' and 'by what criteria?' across "
            "rows that are harder to answer independently (EINT.GRANULARITY and EINT.GROUPING in particular)."
        ),
        entry="Positive pattern to retain",
        applicability="Potentially cross-project",
        priority="Low",
        confidence="High",
        impact=(
            "None negative. Noted because revisions that consolidate these four questions back into one would "
            "lose the distinction that made them useful."
        ),
        source="forms: 'EIT 5-Evidence Item Type Form' columns H-K; guidance lines 550-624",
        related="OBS-002; OBS-011",
    ),
]

COLS = "A B C D E F G H I J K L M N O P Q R S T U V".split()


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    template = Path(argv[1])
    out = Path(argv[2]) if len(argv) > 2 else DEFAULT_OUT
    wb = openpyxl.load_workbook(template)
    ws = wb["Project Feedback Log"]

    # Carry the header row's styling down into the data rows.
    hdr = {c.column_letter: c for c in ws[1]}

    for i, o in enumerate(OBSERVATIONS):
        r = 2 + i
        vals = {
            "A": f"{RUN.rsplit('-', 1)[0]}-{o['id']}",
            "B": DATE,
            "C": PROJECT,
            "D": f"{RUN} / {DATE}",
            "E": FORMS_V,
            "F": GUIDE_V,
            "G": AGENT,
            "H": o["stage"],
            "I": o["component"],
            "J": o["other"],
            "K": o["reqs"],
            "L": o["category"],
            "M": o["finding"],
            "N": o["evidence"],
            "O": o["suggestion"],
            "P": o["entry"],
            "Q": o["applicability"],
            "R": o["priority"],
            "S": o["confidence"],
            "T": o["impact"],
            "U": o["source"],
            "V": o["related"],
        }
        for col in COLS:
            cell = ws[f"{col}{r}"]
            cell.value = vals[col]
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            if col in hdr and hdr[col].border is not None:
                cell.border = copy(hdr[col].border)
        ws.row_dimensions[r].height = 90

    wb.save(out)
    print(f"wrote {out} with {len(OBSERVATIONS)} observations")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
