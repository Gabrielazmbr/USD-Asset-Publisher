from pathlib import Path

import pytest

from houdini_usd_publisher.validation.kind import KindValidator



@pytest.fixture
def validator():
    return KindValidator()

@pytest.fixture
def valid_component_usd_file(tmp_path) -> Path:
    content = """\
#usda 1.0
(
    defaultPrim = "World"
    upAxis = "Y"
)
def Xform "World" (
    kind = "component"
)
{}
"""
    path = tmp_path / "asset.usda"
    path.write_text(content)
    return path

@pytest.fixture
def valid_assembly_usd_file(tmp_path) -> Path:
    content = """\
#usda 1.0
(
    defaultPrim = "World"
    upAxis = "Y"
)
def Xform "World" (
    kind = "assembly"
)
{}
"""
    path = tmp_path / "asset.usda"
    path.write_text(content)
    return path


@pytest.fixture
def no_kind_usd_file(tmp_path) -> Path:
    content = """\
#usda 1.0
(
    defaultPrim = "World"
    upAxis = "Y"
)
def Xform "World" (
)
{}
"""
    path = tmp_path / "asset.usda"
    path.write_text(content)
    return path


@pytest.fixture
def component_holds_component_usd_file(tmp_path) -> Path:
    content = """\
#usda 1.0
(
    defaultPrim = "World"
    upAxis = "Y"
)
def Xform "World" (
    kind = "component"
)
{
    def Xform "Arch_compo" (
        kind = "component"
    )
    {}
}
"""
    path = tmp_path / "asset.usda"
    path.write_text(content)
    return path


def test_valid_component_asset_no_errors (validator, valid_component_usd_file):
    errors, warnings = validator.validate(valid_component_usd_file)
    assert errors == []

def test_valid_assembly_asset_no_errors (validator, valid_assembly_usd_file):
    errors, warnings = validator.validate(valid_assembly_usd_file)
    assert errors == []

def test_invalid_kind_asset_errors (validator, no_kind_usd_file):
    errors, warnings = validator.validate(no_kind_usd_file)
    assert len(errors) == 1
    assert "has no kind set" in errors[0]


def test_component_holds_component_asset_errors (validator, component_holds_component_usd_file):
    errors, warnings = validator.validate(component_holds_component_usd_file)
    assert len(errors) == 1
    assert "components should be leaf nodes" in errors[0]
