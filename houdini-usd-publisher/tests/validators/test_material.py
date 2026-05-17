from pathlib import Path

import pytest

from houdini_usd_publisher.validation.material import MaterialValidator

@pytest.fixture
def validator():
    return MaterialValidator()

@pytest.fixture
def usd_no_mesh_prims_file(tmp_path) -> Path:
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
def usd_mesh_prims_file(tmp_path) -> Path:
    content = """\
#usda 1.0
(
    defaultPrim = "World"
    upAxis = "Y"
)
def Xform "World" (
    kind = "assembly"
)
{
    def Mesh "geo" {}
}
"""
    path = tmp_path / "asset.usda"
    path.write_text(content)
    return path


@pytest.fixture
def usd_mesh_mat_prims_file(tmp_path) -> Path:
    content = """\
#usda 1.0
(
    defaultPrim = "World"
    upAxis = "Y"
)
def Xform "World" (
    kind = "assembly"
)
{
    def Mesh "geo" {}
    def Material "mat" {}
}
"""
    path = tmp_path / "asset.usda"
    path.write_text(content)
    return path


@pytest.fixture
def usd_bindings_prims_file(tmp_path) -> Path:
    content = """\
#usda 1.0
(
    defaultPrim = "World"
    upAxis = "Y"
)
def Xform "World" (
    kind = "assembly"
)
{
    def Mesh "geo" (
        prepend apiSchemas = ["MaterialBindingAPI"]
    )
    {
        rel material:binding = </World/mat>
    }
    def Material "mat" {}
}
"""
    path = tmp_path / "asset.usda"
    path.write_text(content)
    return path


def test_usd_no_mesh_prims_warnings (validator, usd_no_mesh_prims_file):
    errors, warnings = validator.validate(usd_no_mesh_prims_file)
    assert len(warnings) == 1
    assert "No Mesh prims found — asset may be missing geometry" in warnings[0]

def test_usd_only_mesh_prims_warnings (validator, usd_mesh_prims_file):
    errors, warnings = validator.validate(usd_mesh_prims_file)
    assert len(warnings) == 1
    assert "Mesh prim(s) but no Material prims — " in warnings[0]

def test_usd_mat_mesh_prims_warnings (validator, usd_mesh_mat_prims_file):
    errors, warnings = validator.validate(usd_mesh_mat_prims_file)
    assert len(warnings) == 1
    assert "Mesh prim(s) have no material binding: " in warnings[0]

def test_usd_binding_prims_no_warnings (validator, usd_bindings_prims_file):
    errors, warnings = validator.validate(usd_bindings_prims_file)
    assert warnings == []
