"""SOMA answers for the EIT sheet (Evidence Item Types), rows 2-21.

Columns: F=[F1] current, G=[F2] desired, H=[F3] location, I=[F4] local form,
J=[F5] addressability, K=[F6] attributes, L=[F7] specific kinds,
M=[F8] examples, N=[F9] explanation, O=[F10] claim types.
"""

EIT = "xl/worksheets/sheet5.xml"

_rows = {
    # ---------------------------------------------------- Individual Data Items
    2: dict(  # EI.DATA.EXPERIMENTAL_OBSERVATIONAL
        f1="Y", f2="Y",
        loc="LOCAL;EXTERNAL",
        form="FREE_TEXT;STRUCTURED_CONTENT",
        addr="YES",
        attrs="Measured value; unit (UO term id and label); central tendency (mean, median, "
              "geometric mean); sample size; variability type with value or bounds (standard "
              "deviation, standard error, 95% confidence interval, range, interquartile range); "
              "value qualifier preserving a censored report such as \"<0.05\" rather than silently "
              "recording 0.05; the experimental group and the exposure condition the value was "
              "measured under.",
        kinds="Ciliary beat frequency; ciliary active area; airway surface liquid height; "
              "periciliary layer depth; mucociliary transport rate and directionality; CFTR "
              "chloride current and sweat chloride; reactive oxygen species and lipid "
              "peroxidation readouts; EGFR and downstream kinase phosphorylation; goblet-cell "
              "counts and MUC5AC/MUC5B expression; BALF and sputum differential cell counts and "
              "cytokine concentrations; spirometry (FVC, FEV1, FEV1/FVC); target-gene mRNA levels "
              "as delta-Ct or fold change.",
        ex="Evidence item (E01), all six fields as they appear in the file: reference: "
           "\"PMID:41469766\", reference_title: \"Seasonal impact of PM(2.5) ...\", supports: "
           "SUPPORT, evidence_source: HUMAN_CLINICAL, snippet: \"FEV1/FVC (measured) 90.06+/-6.19 "
           "84.32+/-3.86 0.00\", explanation: \"Table 3 row giving the measured FEV1/FVC values this "
           "assay records for the monsoon and spring visits, with the paired t-test p-value.\" "
           "Note that the table the quote came from is named only inside the explanation prose. "
           "Separately structured value (E02): fvc: {value: \"2.92\", unit: {id: UO:0000099, name: "
           "liter}, central_tendency: mean, sample_size: 33, variability: {variability_type: "
           "standard_deviation, value: \"0.58\"}}.",
        expl="This is the project's core evidence type, and it is represented at two levels at "
             "once, which the modelling group should not conflate. (a) The verbatim quoted passage "
             "reporting the measurement is stored as free text in an evidence item and is machine-"
             "verified word-for-word against a cached copy of the cited publication (S02, S06). "
             "(b) The measured value itself is separately represented as structured content in a "
             "named measurement slot on an output record. The quote is what is verified; the "
             "structured value is what is queried. Nothing currently checks that the structured "
             "value agrees with the quote it sits beside — a gap the project is aware of. "
             "Where a value exists only in a figure, project extraction rules forbid estimating it, "
             "so the output record carries its experimental group, exposure condition and a "
             "described direction but no quantity value, and the figure is named in prose "
             "(see EI.COMPOSITE.FIGURE). See also EI.CUSTOM.001, which records the quoted passage "
             "as the project's unit of evidence representation.",
        ct="C001; C002; C003; C004",
    ),
    3: dict(  # EI.DATA.CLINICAL
        f1="N", f2="N",
        loc="", form="", addr="",
        attrs="", kinds="",
        ex="",
        expl="Current state: the corpus includes measurements taken on human subjects — spirometry, "
             "automated haematology, Papanicolaou sputum cytology — but these are research "
             "measurements collected in panel and cohort studies reported in publications, not "
             "observations recorded in a clinical care context such as a clinical encounter, "
             "laboratory order or pathology report. They are captured under "
             "EI.DATA.EXPERIMENTAL_OBSERVATIONAL to avoid double-counting the same evidence items "
             "in two rows. No project source provides evidence of a requirement to represent "
             "clinical-record evidence items. "
             "FOR HUMAN REVIEW: if the project intends to ingest clinical or real-world data in "
             "future, this row should become Y in the desired-state column.",
        ct="",
    ),
    4: dict(  # EI.DATA.STATISTICAL_METRIC
        f1="Y", f2="Y",
        loc="LOCAL;EXTERNAL",
        form="FREE_TEXT;STRUCTURED_CONTENT",
        addr="YES",
        attrs="Metric value and unit; name of the statistical test applied; p-value; confidence "
              "interval bounds with unit and interval level; dispersion type and value; and "
              "whether the metric was reported by the authors or computed afterwards from "
              "extracted values.",
        kinds="p-values; 95% confidence intervals; standard deviations; standard errors; "
              "interquartile ranges; linear mixed-effects regression beta estimates; absolute "
              "differences; percent changes; fold changes; ratios.",
        ex="E04 — ResponseComparison COMP:ghosh-lf-fev1fvc: change_type: absolute_difference, "
           "change_direction: decreased, change_value: {value: \"-2.62\", unit: {id: UO:0000187, "
           "name: percent}, variability: {variability_type: confidence_interval_95, lower_bound: "
           "\"-3.68\", upper_bound: \"-1.56\"}}, with statistical_test recording the per-10 ug/m3 "
           "scaling of the estimate and derivation: reported_in_paper.",
        expl="Statistical metrics are first-class structured content in the canonical data, not "
             "only quoted text. They are the quantitative core of the comparison claim type (C002), "
             "because papers report changes in many forms and the project normalises them to a "
             "single change value with an uncertainty measure. The statistical_test field is used "
             "to record the scale on which an estimate is expressed, so that a regression "
             "coefficient per unit of exposure is never mistaken for a raw difference between "
             "groups. The dispersion vocabulary distinguishes standard deviation, standard error, "
             "confidence interval and range explicitly, because papers often fail to state which "
             "they report.",
        ct="C002",
    ),
    5: dict(  # EI.DATA.COMPUTATIONAL_PREDICTION
        f1="N", f2="N",
        loc="", form="", addr="", attrs="", kinds="", ex="",
        expl="Current state: direct inspection of the canonical data and schema establishes that no "
             "computational prediction, model output or algorithmic score is represented as an "
             "evidence item (S01, S02). "
             "One point of possible confusion: the project's evidence_source field includes the "
             "value COMPUTATIONAL, but that classifies the kind of study the CITED PUBLICATION "
             "reports — an in silico or modelling study — and is evidence-item generation context "
             "(see PROV.EI.GENERATION_CONTEXT), not a prediction used as an evidence item. "
             "No project source supports a desired-state requirement here.",
        ct="",
    ),
    # ---------------------------------------------------- Composite Evidence Items
    6: dict(  # EI.COMPOSITE.DATA_TABLE
        f1="N", f2="Y",
        loc="LOCAL;EXTERNAL",
        form="STRUCTURED_METADATA",
        addr="NO",
        attrs="DESIRED: the table label exactly as the publication prints it, and the "
              "article-section type indicating that the quote came from a table rather than from "
              "narrative prose.",
        kinds="Publication tables reporting group means with dispersion and p-values across "
              "exposure conditions or study visits; tables of participant characteristics; "
              "tables of regression estimates with confidence intervals.",
        ex="Current state, prose only: the evidence item quoting \"FEV1/FVC (measured) "
           "90.06+/-6.19 84.32+/-3.86 0.00\" names its table inside its explanation text — \"Table 3 "
           "row giving the measured FEV1/FVC values ...\" — and in no other field (E01). "
           "Desired (ILLUSTRATIVE, from S13): a figure_reference field carrying \"Table 3\" and an "
           "article_section field carrying `table`.",
        expl="Current state: a publication table is named only inside free-text explanation and "
             "description prose, where it cannot be queried. Direct inspection of all 40 canonical "
             "files returns zero occurrences of any structured table or section field, and the "
             "pinned schema release does not define one (S01, S02). So this is N, not Y. "
             "Desired-state support: EXPLICIT_FUTURE_REQUIREMENT — S13 (soma repository main "
             "branch, commit 45b4af56 'Add figure and section provenance to evidence and outputs', "
             "which adds `article_section` and `figure_reference` slots to EvidenceItem after the "
             "pinned 0.2.4 release and is not yet adopted by any canonical file). "
             "The project regards the distinction as load-bearing rather than cosmetic: that "
             "unreleased slot's own documentation states that a value quoted from Results carries "
             "more weight than one quoted from a Methods sentence about how a reagent was stored. "
             "No table structure or content would be stored; the relevant row is quoted verbatim in "
             "the evidence item and the individual values are structured separately as "
             "measurements, so the table is addressable only as part of its evidence item.",
        ct="C001; C002",
    ),
    7: dict(  # EI.COMPOSITE.DATASET
        f1="N", f2="N",
        loc="", form="", addr="", attrs="", kinds="", ex="",
        expl="Current state: direct inspection establishes that no external dataset or data "
             "repository accession is represented as an evidence item (S01, S02). The project "
             "extracts from publication text and figures, not from deposited datasets, and no "
             "project source supports a desired-state requirement here.",
        ct="",
    ),
    8: dict(  # EI.COMPOSITE.FIGURE
        f1="N", f2="Y",
        loc="LOCAL;EXTERNAL",
        form="STRUCTURED_METADATA",
        addr="NO",
        attrs="DESIRED: the figure label exactly as the publication prints it, including panel "
              "where the paper gives one (for example \"Figure 3B\"), and the article-section type "
              "distinguishing a quote taken from a figure caption from one taken from narrative "
              "prose.",
        kinds="Figures reporting molecular readouts for which the publication gives no numeric "
              "values in the running text — RT-qPCR delta-Ct plots, ELISA bar charts, gel "
              "zymography band intensities, flow-cytometry apoptosis frequencies, "
              "immunocytochemistry mean fluorescence intensities.",
        ex="Current state, prose only: in Container-ghosh2025-pm25-egfr-pi3k-akt.yaml every "
           "molecular readout is reported in Figures 2-4 with no numbers in the running text, and "
           "the file's modelling notes say so in a YAML comment — \"shown in Figs. 2-4 ONLY, with "
           "no numbers in the running text ... those output records carry their experimental group, "
           "the exposure condition ... but no QuantityValue\". The figure is named in a comment and "
           "in description text; no field holds it. "
           "Desired (ILLUSTRATIVE, from S13): a figure_reference field carrying \"Figure 3B\".",
        expl="Current state: this is the project's mechanism for a value it deliberately refuses to "
             "estimate, and it works today by NOT recording a quantity value and describing the "
             "figure in prose. Direct inspection of all 40 canonical files returns zero occurrences "
             "of a structured figure field, and the pinned schema release does not define one "
             "(S01, S02). So this is N, not Y — a reviewer can find the figure only by reading "
             "description or comment text. "
             "Desired-state support: EXPLICIT_FUTURE_REQUIREMENT — S13 (soma main, commit "
             "45b4af56), whose unreleased `figure_reference` slot documentation instructs that the "
             "figure be recorded whenever a quantitative result lives in a figure or chart, even "
             "when no exact value could be read from it, so that a reviewer knows where to look. "
             "That is precisely this project's need and it is built but not released or adopted. "
             "The figure would be referenced by printed label and not stored, so it stays "
             "addressable only through the evidence item that cites it.",
        ct="C001; C002; C003; C004",
    ),
    9: dict(  # EI.COMPOSITE.EXTERNAL_RECORD
        f1="N", f2="N",
        loc="", form="", addr="", attrs="", kinds="", ex="",
        expl="Current state: direct inspection establishes that no externally maintained database "
             "record is treated as an evidence item (S01, S02). The project references PubMed "
             "records, but as the SOURCE publication that contains its evidence items rather than "
             "as the evidence item itself (see EI.DOCUMENT.SCIENTIFIC_PUBLICATION). Ontology terms "
             "from GO, ChEBI, CL, UBERON, MONDO, HPO, UO and ENVO are referenced throughout, but "
             "they are the normalised vocabulary the project aligns its content to, not evidence "
             "for any claim. No project source supports a desired-state requirement here.",
        ct="",
    ),
    10: dict(  # EI.COMPOSITE.STUDY_RESULT
        f1="Y", f2="Y",
        loc="LOCAL",
        form="STRUCTURED_CONTENT",
        addr="YES",
        attrs="Assay identifier, name and description; the protocols followed; the biological "
              "system assayed; the exposure conditions applied; the experimental groups compared; "
              "the Key Event the assay informs on; and the set of output measurement records "
              "grouped under it.",
        kinds="Eleven domain-specific assay types: ciliary function, airway surface liquid, "
              "mucociliary clearance, oxidative stress, CFTR function, EGFR signalling, goblet "
              "cell, BALF/sputum, lung function, FOXJ1, and gene expression.",
        ex="LF:ghosh-pm25-seasonal-spirometry — one spirometry assay from one publication, "
           "grouping two output measurement records (the monsoon baseline visit and the spring "
           "treated visit), each with its own exposure condition, together with the protocol "
           "followed and six evidence items quoting the paper.",
        expl="The project's Assay object performs the grouping function this row describes: it "
             "organises the related measurements of one study around one focus, they are grouped "
             "because they share study provenance and collective evidentiary meaning, and the "
             "assay carries its own evidence list in addition to the evidence on individual "
             "measurements. Assays have stable identifiers and are independently addressable. "
             "Note that evidence attaches at two granularities in the canonical data — to the "
             "assay as a whole and to individual output measurements — which is a genuine project "
             "requirement rather than an inconsistency: some quotes support the study design and "
             "others support one specific number.",
        ct="C001; C005",
    ),
    # ---------------------------------------------------- Prior Claims
    11: dict(  # EI.PRIOR_CLAIM.DIRECT_TEXT
        f1="Y", f2="Y",
        loc="LOCAL;EXTERNAL",
        form="FREE_TEXT",
        addr="YES",
        attrs="The verbatim quote; the cited publication identifier and title; the direction of "
              "support; a curator explanation of how the passage bears on the specific claim it is "
              "attached to. DESIRED ADDITION: the section of the publication the passage came "
              "from, which is currently stated only in prose.",
        kinds="Authors' own statements of a finding that corresponds to the claim being modelled — "
              "typically drawn from the abstract, results or discussion.",
        ex="snippet: \"was a significant reduction in the measured ratio of FEV1/FVC in the men\", "
           "supports: SUPPORT, explanation: \"States the direction and "
           "significance of the FEV1/FVC change between seasons that this assay records.\" "
           "A second example attached to a Key Event Relationship claim: snippet: \"high PM 2.5 may "
           "impact the activation of pro-oncogenic signaling\".",
        expl="Very common in this project. Many evidence items are the authors' own narrative "
             "statement of exactly the proposition the project is modelling, quoted verbatim. "
             "These are represented as free text only: the project stores and verifies the "
             "passage, and does not separately structure the prior claim's own subject, predicate "
             "and object. Each passage is individually addressable because the direction of "
             "support and the curator's explanation attach to the individual quote.",
        ct="C001; C002; C003; C004; C006",
    ),
    12: dict(  # EI.PRIOR_CLAIM.DIRECT_STRUCTURED
        f1="N", f2="N",
        loc="", form="", addr="", attrs="", kinds="", ex="",
        expl="Current state: direct inspection establishes that prior claims are never represented "
             "as structured objects carrying their own subject, predicate and object; they are "
             "always quoted as text (S01, S02). The project extracts from publications rather than "
             "ingesting structured assertions from other knowledgebases, so there is no source of "
             "structured prior claims, and no project source supports a desired-state requirement.",
        ct="",
    ),
    13: dict(  # EI.PRIOR_CLAIM.SUPPORTING_TEXT
        f1="Y", f2="Y",
        loc="LOCAL;EXTERNAL",
        form="FREE_TEXT",
        addr="YES",
        attrs="As for EI.PRIOR_CLAIM.DIRECT_TEXT: verbatim quote, cited publication and title, "
              "direction of support, curator explanation.",
        kinds="Passages reporting a distinct finding interpreted as supporting the target claim — "
              "for example a systemic or mechanistic observation quoted as context for a "
              "physiological claim; a statement of the exposure contrast quoted in support of a "
              "response claim.",
        ex="snippet: \"Hb (g/dl) 13.68+/-1.36 12.95+/-1.28 0.00\" with explanation: \"Table 2 row "
           "giving the hemoglobin values quoted in this assay's description as the systemic "
           "context for the spirometry change.\" Attached to a Key Event Relationship: snippet: "
           "\"These molecular alterations reflected enhanced proliferative and pro-angiogenic "
           "signaling and reduced apoptosis in the airway cells and the leukocytes.\"",
        expl="Also common, and deliberately distinguished from the directly corresponding case by "
             "the curator explanation attached to each item, which states how the passage bears on "
             "the claim. The distinction between a directly corresponding and a merely supporting "
             "passage is currently carried only in that free-text explanation, not in a structured "
             "field — if the modelling group needs that distinction machine-readable it would have "
             "to be added.",
        ct="C001; C002; C003; C004; C006",
    ),
    14: dict(  # EI.PRIOR_CLAIM.SUPPORTING_STRUCTURED
        f1="N", f2="N",
        loc="", form="", addr="", attrs="", kinds="", ex="",
        expl="Current state: as for EI.PRIOR_CLAIM.DIRECT_STRUCTURED, direct inspection "
             "establishes that no structured prior claim of any kind is represented (S01, S02), "
             "and no project source supports a desired-state requirement.",
        ct="",
    ),
    # ---------------------------------------------------- Documents
    15: dict(  # EI.DOCUMENT.SCIENTIFIC_PUBLICATION
        f1="Y", f2="Y",
        loc="LOCAL;EXTERNAL",
        form="STRUCTURED_METADATA",
        addr="YES",
        attrs="PubMed identifier as a CURIE; publication title, copied from the fetched reference "
              "record rather than typed from memory; DOI. "
              "DESIRED ADDITION: whether the committed cached copy of the publication is full text "
              "or abstract only, because that determines what a quote can be verified against.",
        kinds="Primary research articles reporting exposure-response experiments and human panel "
              "or cohort studies; methods papers describing assay techniques; occasional reviews "
              "cited as the source of a mechanistic statement.",
        ex="source_publication: {reference: \"PMID:41469766\", reference_title: \"Seasonal impact of "
           "PM(2.5) on pro-oncogenic drivers among participants of a thermal power plant in "
           "India.\", doi: \"10.1038/s41598-025-33906-7\"}; and on every evidence item, the same "
           "reference and reference_title pair.",
        expl="Every Container names the one publication it was extracted from, and every evidence "
             "item independently carries the cited publication and its title, so each quote is "
             "traceable without relying on the file it sits in. The recorded title is machine-"
             "checked against the real publication title, which is what prevents a quote being "
             "attributed to the wrong paper (S02, S06). "
             "We note the guidance that SEPIO treats documents as sources that CONTAIN evidence "
             "items rather than as evidence items themselves; that matches how this project uses "
             "the publication reference, and the row is marked Y on the understanding that the "
             "requirement is to represent the publication as the source of its evidence items. "
             "Desired-state support for recording cache content type: "
             "EXISTING_PROJECT_CAPABILITY_NOT_IN_CANONICAL_EXPORT — S05 "
             "(verification/PMID_32783621.json records content_type_in_committed_cache: "
             "\"abstract_only\") and S07 (references_cache entries carry a content_type field).",
        ct="C001; C002; C003; C004; C005; C006",
    ),
    16: dict(  # EI.DOCUMENT.REGULATORY
        f1="N", f2="N",
        loc="", form="", addr="", attrs="", kinds="", ex="",
        expl="Current state: direct inspection establishes that no regulatory document is "
             "represented as evidence (S01, S02). The project's claims are mechanistic and "
             "measurement-based rather than regulatory. No project source supports a desired-state "
             "requirement, although the AOP framework the project uses is itself employed in "
             "regulatory contexts, so this could change if the project's use cases broaden.",
        ct="",
    ),
    17: dict(  # EI.DOCUMENT.GUIDELINE
        f1="N", f2="N",
        loc="", form="", addr="", attrs="", kinds="", ex="",
        expl="Current state: no guideline or consensus document is used as evidence FOR a claim "
             "(S01, S02). Published standards are referenced in the canonical data, but in a "
             "different role: a protocol records the standard it followed, as in spirometry_"
             "standard: \"American Thoracic Society (1995) guidelines\". That is a method "
             "specification describing how the measurements later used as evidence were produced, "
             "and it belongs to evidence-item provenance (see PROV.EI.METHODS), not to this row. "
             "Keeping that distinction is deliberate. "
             "Separately, the OECD Adverse Outcome Pathway framework supplies the weight-of-"
             "evidence vocabulary used for C004, but the framework is not cited as an evidence "
             "item either; it is the interpretation specification (see PROV.INTERP.METHODS).",
        ct="",
    ),
    # ---------------------------------------------------- Images
    18: dict(  # EI.IMAGE.PHOTOGRAPH
        f1="N", f2="N",
        loc="", form="", addr="", attrs="", kinds="", ex="",
        expl="Current state: direct inspection establishes no photographic evidence item (S01, "
             "S02), and no project source supports a desired-state requirement.",
        ct="",
    ),
    19: dict(  # EI.IMAGE.MEDICAL
        f1="N", f2="N",
        loc="", form="", addr="", attrs="", kinds="", ex="",
        expl="Current state: direct inspection establishes no medical imaging evidence item (S01, "
             "S02), and no project source supports a desired-state requirement. The project's "
             "human-subject readouts are spirometry, haematology and sputum cytology rather than "
             "imaging.",
        ct="",
    ),
    20: dict(  # EI.IMAGE.SCIENTIFIC_INSTRUMENT
        f1="N", f2="N",
        loc="", form="", addr="", attrs="", kinds="", ex="",
        expl="Current state: instrument-generated images are the underlying data for many assays "
             "in the corpus — fluorescence and electron microscopy, gel zymography, Western blots, "
             "high-speed video microscopy of ciliary beat — but direct inspection establishes that "
             "no image is represented as an evidence item (S01, S02). Where the result lives only "
             "in such an image, the project records the figure that reports it rather than the "
             "image, which is handled by EI.COMPOSITE.FIGURE above. "
             "The project's documented rule supports referencing the figure, not representing the "
             "image, so this row is marked N in the desired-state column rather than Y. "
             "FOR HUMAN REVIEW: if the project later wants to store or link instrument images, "
             "this would become a genuine requirement.",
        ct="",
    ),
    # ---------------------------------------------------- Custom
    21: dict(  # EI.CUSTOM.001
        name="Verbatim Quoted Source Passage",
        f1="Y", f2="Y",
        loc="LOCAL;EXTERNAL",
        form="FREE_TEXT",
        addr="YES",
        attrs="CURRENT, all six fields of the object: the exact quote, reproduced word-for-word "
              "from the cited publication; the cited publication identifier and title; the kind of "
              "study the cited publication reports; the direction of support; and a curator "
              "explanation of how the passage bears on the specific claim it is attached to. "
              "DESIRED ADDITIONS, neither present today: (a) the locus of the passage within the "
              "publication — the section it came from and the figure or table label where the "
              "underlying data sits — which is currently stated only in prose inside the "
              "explanation; and (b) the verification state of the quote — which tool checked it, "
              "against which cached copy of the publication, whether that copy was full text or "
              "abstract only, on what date, and with what outcome.",
        kinds="Quoted table rows reporting group values; quoted sentences stating a finding; "
              "quoted figure captions; quoted methods sentences establishing a dose or condition.",
        ex="E01 — one evidence item in full, exactly as it appears in the file: {reference: "
           "\"PMID:41469766\", reference_title: \"Seasonal impact of PM(2.5) on pro-oncogenic "
           "drivers among participants of a thermal power plant in India.\", supports: SUPPORT, "
           "evidence_source: HUMAN_CLINICAL, snippet: \"FEV1/FVC (measured) 90.06+/-6.19 "
           "84.32+/-3.86 0.00\", explanation: \"Table 3 row giving the measured FEV1/FVC values "
           "this assay records for the monsoon and spring visits, with the paired t-test "
           "p-value.\"} Note that \"Table 3\" reaches the data only as English inside the "
           "explanation.",
        expl="ADDED BY THE PROJECT as a custom row, because the verbatim quoted passage is this "
             "project's actual unit of evidence representation and addressability, and it "
             "cross-cuts the content-based rows above. "
             "One SOMA evidence item is one quoted passage. What that passage REPORTS may be a "
             "measurement (EI.DATA.EXPERIMENTAL_OBSERVATIONAL), a statistical metric "
             "(EI.DATA.STATISTICAL_METRIC), or the authors' own claim (EI.PRIOR_CLAIM.DIRECT_TEXT "
             "or EI.PRIOR_CLAIM.SUPPORTING_TEXT) — those rows are marked Y for that reason, "
             "following the guidance that a single evidence item may correspond to more than one "
             "category. But the passage is what carries an identifier's worth of metadata, what "
             "the direction of support attaches to, and what is machine-verified; so the project "
             "needs it representable in its own right and not only as a free-text rendering of "
             "some other evidence type. "
             "The passage is also where the project's within-publication locus belongs. Today that "
             "locus exists only as English inside the explanation field ('Table 3 row giving ...'), "
             "so it cannot be queried; the soma main branch has added structured section and figure "
             "slots for it (S13) but they are unreleased and unused. "
             "What makes this item type distinctive in this project is that it is VERIFIABLE: the "
             "quote must appear word-for-word in a cached copy of the cited publication, and CI "
             "checks this across the whole corpus on every run (S02, S06). Where a publisher "
             "blocks full-text caching, a committed receipt of per-snippet SHA-256 hashes proves a "
             "local full-text check passed and makes any later edit to the quote a hard failure "
             "(S05). "
             "FOR HUMAN REVIEW: the project representative should confirm whether this is best "
             "reported as a distinct evidence item type or instead expressed purely as the "
             "FREE_TEXT representation form of the content rows above. We report it separately "
             "because the verification requirement attaches to the passage rather than to the "
             "content it reports.",
        ct="C001; C002; C003; C004; C005; C006",
    ),
}

eit = {}
for row, r in _rows.items():
    if r.get("name"):
        eit[f"C{row}"] = r["name"]
    eit[f"F{row}"] = r["f1"]
    eit[f"G{row}"] = r["f2"]
    eit[f"H{row}"] = r["loc"]
    eit[f"I{row}"] = r["form"]
    eit[f"J{row}"] = r["addr"]
    eit[f"K{row}"] = r["attrs"]
    eit[f"L{row}"] = r["kinds"]
    eit[f"M{row}"] = r["ex"]
    eit[f"N{row}"] = r["expl"]
    eit[f"O{row}"] = r["ct"]

SHEETS = {EIT: eit}
