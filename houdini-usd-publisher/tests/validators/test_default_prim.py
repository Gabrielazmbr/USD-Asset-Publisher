from pathlib import Path

import pytest

from houdini_usd_publisher.validation.default_prim import DefaultPrimValidator


@pytest.fixture
def validator():
    return DefaultPrimValidator()


@pytest.fixture
def usda_without_default_prim(tmp_path) -> Path:
    content = """\
#usda 1.0
(
    upAxis = "Y"
)

def Xform "World"
{
    def Xform "Geo"
    {
    }
}
"""
    path = tmp_path / "asset.usda"
    path.write_text(content)
    return path


@pytest.fixture
def usda_with_default_prim(tmp_path) -> Path:
    content = """\
#usda 1.0
(
    defaultPrim = "World"
    upAxis = "Y"
)

def Xform "World"
{
    def Xform "Geo"
    {
    }
}
"""
    path = tmp_path / "asset.usda"
    path.write_text(content)
    return path


def test_missing_default_prim_is_an_error(validator, usda_without_default_prim):
    errors, warnings = validator.validate(usda_without_default_prim)
    assert len(errors) == 1
    assert "defaultPrim" in errors[0]


def test_valid_default_prim_produces_no_errors(validator, usda_with_default_prim):
    errors, warnings = validator.validate(usda_with_default_prim)
    assert errors == []


def test_valid_default_prim_produces_no_warnings(validator, usda_with_default_prim):
    errors, warnings = validator.validate(usda_with_default_prim)
    assert warnings == []
