"""SOMA first-pass Claim-Evidence Matrix (CEM, sheet8).

The template's own illustrative example occupies A1:G9 and is bound to Excel
Table_7 (ref A3:F9). The SOMA matrix needs nine evidence-type columns rather
than five, so rather than resize that table (which rules 36-40 discourage) the
SOMA matrix is written below it, starting at row 12, clearly labelled. Rows
preserve the Claim Type reference ID and columns preserve the Evidence Item
Requirement ID, as the guidance requires.
"""

CEM = "xl/worksheets/sheet8.xml"

_EVIDENCE_COLS = [
    ("B", "EI.DATA.EXPERIMENTAL_OBSERVATIONAL", "Experimental / Observational Data Items"),
    ("C", "EI.DATA.STATISTICAL_METRIC", "Statistical Metrics"),
    ("D", "EI.COMPOSITE.DATA_TABLE", "Data Tables"),
    ("E", "EI.COMPOSITE.FIGURE", "Figures"),
    ("F", "EI.COMPOSITE.STUDY_RESULT", "Study Result Objects"),
    ("G", "EI.PRIOR_CLAIM.DIRECT_TEXT", "Directly Corresponding Prior Claim - Text"),
    ("H", "EI.PRIOR_CLAIM.SUPPORTING_TEXT", "Supporting Prior Claim - Text"),
    ("I", "EI.DOCUMENT.SCIENTIFIC_PUBLICATION", "Scientific Publications"),
    ("J", "EI.CUSTOM.001", "Verbatim Quoted Source Passage"),
]

# Which evidence item types are actually used, or expected to be used, for each
# claim type. Derived from the completed EIT form's F10 column and from direct
# inspection of the canonical files - not from general biomedical expectation.
_MARKS = {
    "C001": "B D E F G H I J".split(),
    "C002": "B C D E G H I J".split(),
    "C003": "B E G H I J".split(),
    "C004": "B E G H I J".split(),
    "C005": "F I J".split(),
    "C006": "G H I J".split(),
}

_CLAIM_NAMES = {
    "C001": "Exposure-Response Measurement",
    "C002": "Exposure-Response Comparison",
    "C003": "Key Event Occurrence",
    "C004": "Key Event Relationship (AOP causal linkage)",
    "C005": "Assay Method Claim",
    "C006": "Exposure Condition Claim",
}

_NOTES = {
    "C005": "Evidence is cited for the assay as a whole (Study Result) rather than for the "
            "protocol independently; see EIT F10 and the Review Memo.",
    "C006": "Exposure conditions are evidenced by quoted passages stating the agent, "
            "concentration and duration; no separate measurement evidence item is cited for "
            "the exposure itself.",
}

cem = {}

cem["A12"] = (
    "SOMA FIRST-PASS CLAIM-EVIDENCE MATRIX (added by the requirements agent; the block above is "
    "the template's own illustrative example and has been left unchanged). Rows are Claim Type "
    "reference IDs from the CT form; columns are Evidence Item Requirement IDs from the EIT form. "
    "An X marks an evidence type that is used, or is expected to be used, as evidence for that "
    "claim type. Evidence item types marked N in the EIT form are omitted as columns. "
    "Derived from the completed CT and EIT forms and from direct inspection of the canonical "
    "files, not from general biomedical expectation. PROVISIONAL - requires human review."
)

cem["A13"] = "Claim Type (reference ID / descriptor)"
for col, req_id, name in _EVIDENCE_COLS:
    cem[f"{col}13"] = f"{req_id}\n({name})"
cem["K13"] = "Requirement ID (generated)"
cem["L13"] = "Notes"

for i, (cid, name) in enumerate(_CLAIM_NAMES.items()):
    row = 14 + i
    cem[f"A{row}"] = f"{cid} - {name}"
    for col, _req, _n in _EVIDENCE_COLS:
        cem[f"{col}{row}"] = "X" if col in _MARKS[cid] else ""
    cem[f"K{row}"] = f"MATRIX.{cid}"
    cem[f"L{row}"] = _NOTES.get(cid, "")

cem["A21"] = (
    "FLAGGED FOR HUMAN REVIEW: (1) EI.CUSTOM.001 is marked for every claim type because the "
    "verbatim quoted passage is the project's unit of evidence representation and therefore "
    "cross-cuts the content-based columns; if the project decides that passage is better expressed "
    "as the FREE_TEXT representation form of the content columns, this column should be removed. "
    "(2) C005 and C006 largely duplicate C001's evidence profile, which is expected given the "
    "representative's decision to report six claim types rather than four. (3) The two prior-claim "
    "text columns are distinguished today only by the curator's free-text explanation, not by a "
    "structured field, so the split between them in this matrix reflects curatorial reading rather "
    "than a machine-readable distinction."
)

SHEETS = {CEM: cem}
