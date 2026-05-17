from pathlib import Path
import pytest
from houdini_usd_publisher.validation.file_reference import FileReferenceValidator


@pytest.fixture
def validator():
    return FileReferenceValidator()


@pytest.fixture
def usda_no_references(tmp_path) -> Path:
    path = tmp_path / "asset.usda"
    path.write_text("""\
#usda 1.0
(
    defaultPrim = "World"
)

def Xform "World" {}
""")
    return path


@pytest.fixture
def usda_with_valid_reference(tmp_path) -> Path:
    # Create the referenced file first
    ref_file = tmp_path / "geo.usda"
    ref_file.write_text("""\
#usda 1.0

def Mesh "Geo" {}
""")

    path = tmp_path / "asset.usda"
    path.write_text(f"""\
#usda 1.0
(
    defaultPrim = "World"
)

def Xform "World" (
    references = @{ref_file}@
)
{{
}}
""")
    return path


@pytest.fixture
def usda_with_missing_reference(tmp_path) -> Path:
    path = tmp_path / "asset.usda"
    path.write_text("""\
#usda 1.0
(
    defaultPrim = "World"
)

def Xform "World" (
    references = @./missing_file.usda@
)
{
}
""")
    return path


def test_no_references_produces_no_errors(validator, usda_no_references):
    errors, warnings = validator.validate(usda_no_references)
    assert errors == []


def test_valid_reference_produces_no_errors(validator, usda_with_valid_reference):
    errors, warnings = validator.validate(usda_with_valid_reference)
    assert errors == []


def test_missing_reference_produces_error(validator, usda_with_missing_reference):
    errors, warnings = validator.validate(usda_with_missing_reference)
    assert len(errors) >= 1


def test_no_references_produces_no_warnings(validator, usda_no_references):
    errors, warnings = validator.validate(usda_no_references)
    assert warnings == []
