"""Data test."""
import os
import glob
import re

import pytest
import yaml
from pathlib import Path

import soma.datamodel.soma
from linkml_runtime.loaders import yaml_loader

DATA_DIR_VALID = Path(__file__).parent / "data" / "valid"
DATA_DIR_INVALID = Path(__file__).parent / "data" / "invalid"

VALID_EXAMPLE_FILES = glob.glob(os.path.join(DATA_DIR_VALID, '*.yaml'))
INVALID_EXAMPLE_FILES = sorted(
    glob.glob(os.path.join(DATA_DIR_INVALID, '*.yaml'))
    + glob.glob(os.path.join(DATA_DIR_INVALID, '*.json'))
)


def test_valid_fixtures_do_not_use_astrocyte_cl_term_for_nasal_epithelium():
    """Regression test for CL:0002603 misuse in nasal-epithelium fixtures."""
    wrong_term = "CL:0002603"
    offenders = [
        Path(filepath).name
        for filepath in VALID_EXAMPLE_FILES
        if wrong_term in Path(filepath).read_text(encoding="utf-8")
    ]
    assert offenders == []


# Regression guard for issue #137: unit CURIEs that fixtures paired with the
# wrong label. The authoritative check is the term validator (`just
# validate-fixtures`, part of `just qc`), which resolves every CURIE against
# the ontology; this fast, offline test pins the exact bad (id, label) pairs
# that were fixed so a copy-paste cannot quietly reintroduce them.
MISMATCHED_UNIT_PAIRS = [
    ("UO:0000024", "nanogram per milliliter"),   # UO:0000024 is nanogram; ng/mL is UO:0000275
    ("UO:0000187", "percent predicted"),          # unit is percent; "predicted" belongs in the description
    ("UO:0000103", "micrometer per second"),      # UO:0000103 is picoliter; um/s has no UO term (UCUM:um/s)
    ("UO:0000063", "nanomole per milligram protein"),  # UO:0000063 is millimolar (UCUM:nmol/mg)
    ("UO:0000190", "ratio"),                      # the UO label is "ratio unit"
    ("UO:0000175", "picogram per milliliter"),    # UO:0000175 is gram per liter; pg/mL is UO:0010070
    ("UO:0000169", "parts per billion"),          # UO:0000169 is parts per million; ppb is UO:0000170
    ("UO:0000189", "count"),                      # the UO label is "count unit"
    ("UO:0000298", "microgram per hour"),         # UO:0000298 is centi (UCUM:ug/h)
    ("UO:0000275", "nanogram per milligram creatinine"),  # UO:0000275 is ng/mL (UCUM:ng/mg)
    ("UO:0000209", "cells per milliliter"),       # UO:0000209 is deciliter; cells/mL is UO:0000201
    ("UO:0000196", "ratio"),                      # UO:0000196 is pH; a dimensionless ratio is UO:0000190
    ("UO:0000098", "milliliter per year"),        # UO:0000098 is milliliter (UCUM:mL/a)
    ("UO:0000022", "microgram"),                  # UO:0000022 is milligram; microgram is UO:0000023
    ("UO:0000019", "centipoise"),                 # UO:0000019 is angstrom (UCUM:cP)
]


@pytest.mark.parametrize("curie,label", MISMATCHED_UNIT_PAIRS)
def test_data_do_not_reuse_mismatched_unit_terms(curie, label):
    """Regression test for the unit ID/label mismatches fixed in issue #137."""
    pattern = re.compile(
        r'id: "%s"\s+name: "%s"' % (re.escape(curie), re.escape(label))
    )
    kb_files = Path(__file__).resolve().parents[1] / "kb"
    data_files = [*VALID_EXAMPLE_FILES, *(str(path) for path in kb_files.rglob("*.yaml"))]
    offenders = [
        Path(filepath).name
        for filepath in data_files
        if pattern.search(Path(filepath).read_text(encoding="utf-8"))
    ]
    assert offenders == []


def test_data_do_not_use_hel_cell_line_term_for_calu3():
    """Regression test for CLO:0003679 misuse in Calu-3 cell lines."""
    def records(value):
        if isinstance(value, dict):
            yield value
            for child in value.values():
                yield from records(child)
        elif isinstance(value, list):
            for child in value:
                yield from records(child)

    kb_files = Path(__file__).resolve().parents[1] / "kb"
    data_files = [*VALID_EXAMPLE_FILES, *(str(path) for path in kb_files.rglob("*.yaml"))]
    offenders = []
    for filepath in data_files:
        data = yaml.safe_load(Path(filepath).read_text(encoding="utf-8"))
        if any(
            isinstance(record.get("cell_line"), dict)
            and record["cell_line"].get("name") == "Calu-3"
            and record["cell_line"].get("id") == "CLO:0003679"
            for record in records(data)
        ):
            offenders.append(Path(filepath).name)
    assert offenders == []


@pytest.mark.parametrize("filepath", VALID_EXAMPLE_FILES)
def test_valid_data_files(filepath):
    """Test loading of all valid data files.

    All valid data files are loaded against the Container class (tree_root),
    which holds collections of various measurement types.
    """
    # Use Container as the target class since it's the tree_root
    # that holds all measurement collections
    tgt_class = soma.datamodel.soma.Container
    obj = yaml_loader.load(filepath, target_class=tgt_class)
    assert obj


@pytest.mark.parametrize("filepath", INVALID_EXAMPLE_FILES)
def test_invalid_data_files(filepath):
    """Test that invalid data files fail to load against the Container class."""
    tgt_class = soma.datamodel.soma.Container
    with pytest.raises(Exception):
        yaml_loader.load(filepath, target_class=tgt_class)
