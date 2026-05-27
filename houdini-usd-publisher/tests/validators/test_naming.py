from pathlib import Path
import json
import pytest
from houdini_usd_publisher.core.config import PublishConfig
from houdini_usd_publisher.validation.naming import NamingConventionValidator


# Config fixtures

@pytest.fixture
def any_style_config(tmp_path):
    cfg = {
        "validators": {
            "NamingConventionValidator": {
                "enabled": True,
                "naming_style": "any",
                "allow_leading_underscore": False,
                "allow_trailing_underscore": False,
                "allow_double_underscore": False,
                "reserved_names": ["default", "root"]
            }
        }
    }
    path = tmp_path / "config.json"
    path.write_text(json.dumps(cfg))
    return PublishConfig(path)


@pytest.fixture
def camel_case_config(tmp_path):
    cfg = {
        "validators": {
            "NamingConventionValidator": {
                "enabled": True,
                "naming_style": "CamelCase",
                "allow_leading_underscore": False,
                "allow_trailing_underscore": False,
                "allow_double_underscore": False,
                "reserved_names": ["default", "root"]
            }
        }
    }
    path = tmp_path / "config.json"
    path.write_text(json.dumps(cfg))
    return PublishConfig(path)


@pytest.fixture
def snake_case_config(tmp_path):
    cfg = {
        "validators": {
            "NamingConventionValidator": {
                "enabled": True,
                "naming_style": "snake_case",
                "allow_leading_underscore": False,
                "allow_trailing_underscore": False,
                "allow_double_underscore": False,
                "reserved_names": ["default", "root"]
            }
        }
    }
    path = tmp_path / "config.json"
    path.write_text(json.dumps(cfg))
    return PublishConfig(path)


# USD file fixtures

@pytest.fixture
def usda_clean(tmp_path) -> Path:
    path = tmp_path / "asset.usda"
    path.write_text("""\
#usda 1.0
(
    defaultPrim = "World"
)
def Xform "World"
{
    def Xform "GeoGroup" {}
    def Mesh "BodyMesh" {}
}
""")
    return path



@pytest.fixture
def usda_reserved_name(tmp_path) -> Path:
    path = tmp_path / "asset.usda"
    path.write_text("""\
#usda 1.0
(
    defaultPrim = "World"
)
def Xform "World"
{
    def Xform "default" {}
}
""")
    return path


@pytest.fixture
def usda_leading_underscore(tmp_path) -> Path:
    path = tmp_path / "asset.usda"
    path.write_text("""\
#usda 1.0
(
    defaultPrim = "World"
)
def Xform "World"
{
    def Xform "_hidden" {}
}
""")
    return path


@pytest.fixture
def usda_trailing_underscore(tmp_path) -> Path:
    path = tmp_path / "asset.usda"
    path.write_text("""\
#usda 1.0
(
    defaultPrim = "World"
)
def Xform "World"
{
    def Xform "geo_" {}
}
""")
    return path


@pytest.fixture
def usda_double_underscore(tmp_path) -> Path:
    path = tmp_path / "asset.usda"
    path.write_text("""\
#usda 1.0
(
    defaultPrim = "World"
)
def Xform "World"
{
    def Xform "geo__mesh" {}
}
""")
    return path


@pytest.fixture
def usda_snake_in_camel(tmp_path) -> Path:
    """snake_case name that should warn under CamelCase config."""
    path = tmp_path / "asset.usda"
    path.write_text("""\
#usda 1.0
(
    defaultPrim = "World"
)
def Xform "World"
{
    def Xform "geo_mesh" {}
}
""")
    return path


@pytest.fixture
def usda_camel_in_snake(tmp_path) -> Path:
    """CamelCase name that should warn under snake_case config."""
    path = tmp_path / "asset.usda"
    path.write_text("""\
#usda 1.0
(
    defaultPrim = "World"
)
def Xform "World"
{
    def Xform "GeoMesh" {}
}
""")
    return path


@pytest.fixture
def usda_with_reference(tmp_path) -> Path:
    """Root prim is clean, referenced content has bad names — should be ignored."""
    ref_file = tmp_path / "ref.usda"
    ref_file.write_text("""\
#usda 1.0
def Xform "1_bad_from_reference" {}
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


# Error tests

def test_clean_file_has_no_errors(any_style_config):
    validator = NamingConventionValidator(any_style_config)
    path = list(any_style_config._path.parent.glob("*.json"))[0]  # just need the fixture path
    # Use a fresh clean file
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".usda", mode="w", delete=False) as f:
        f.write("""\
#usda 1.0
(
    defaultPrim = "World"
)
def Xform "World"
{
    def Xform "GeoGroup" {}
}
""")
        tmp = Path(f.name)
    errors, warnings = validator.validate(tmp)
    assert errors == []
    assert warnings == []



def test_reserved_name_is_an_error(any_style_config, usda_reserved_name):
    validator = NamingConventionValidator(any_style_config)
    errors, warnings = validator.validate(usda_reserved_name)
    assert len(errors) == 1
    assert "reserved" in errors[0]


# Warning tests

def test_leading_underscore_is_a_warning(any_style_config, usda_leading_underscore):
    validator = NamingConventionValidator(any_style_config)
    errors, warnings = validator.validate(usda_leading_underscore)
    assert errors == []
    assert len(warnings) == 1
    assert "underscore" in warnings[0]


def test_trailing_underscore_is_a_warning(any_style_config, usda_trailing_underscore):
    validator = NamingConventionValidator(any_style_config)
    errors, warnings = validator.validate(usda_trailing_underscore)
    assert errors == []
    assert len(warnings) == 1
    assert "underscore" in warnings[0]


def test_double_underscore_is_a_warning(any_style_config, usda_double_underscore):
    validator = NamingConventionValidator(any_style_config)
    errors, warnings = validator.validate(usda_double_underscore)
    assert errors == []
    assert len(warnings) == 1
    assert "double underscore" in warnings[0]


def test_camel_case_style_warns_on_snake(camel_case_config, usda_snake_in_camel):
    validator = NamingConventionValidator(camel_case_config)
    errors, warnings = validator.validate(usda_snake_in_camel)
    assert errors == []
    assert any("CamelCase" in w for w in warnings)


def test_snake_case_style_warns_on_camel(snake_case_config, usda_camel_in_snake):
    validator = NamingConventionValidator(snake_case_config)
    errors, warnings = validator.validate(usda_camel_in_snake)
    assert errors == []
    assert any("snake_case" in w for w in warnings)


def test_any_style_allows_mixed(any_style_config, tmp_path):
    path = tmp_path / "asset.usda"
    path.write_text("""\
#usda 1.0
(
    defaultPrim = "World"
)
def Xform "World"
{
    def Xform "geo_mesh" {}
    def Xform "GeoMesh" {}
}
""")
    validator = NamingConventionValidator(any_style_config)
    errors, warnings = validator.validate(path)
    assert errors == []
    assert warnings == []


# Scope tests

def test_referenced_content_is_skipped(any_style_config, usda_with_reference):
    """Bad names inside referenced files should not be flagged."""
    validator = NamingConventionValidator(any_style_config)
    errors, warnings = validator.validate(usda_with_reference)
    assert errors == []
