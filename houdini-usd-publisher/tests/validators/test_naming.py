from pathlib import Path
import json
import pytest
from houdini_usd_publisher.core.config import PublishConfig
from houdini_usd_publisher.validation.naming import NamingConventionValidator


@pytest.fixture
def validator(fresh_config):
    return NamingConventionValidator(PublishConfig(fresh_config))


@pytest.fixture
def camel_case_config(tmp_path):
    cfg = {
        "validators": {
            "NamingConventionValidator": {
                "enabled": True,
                "allow_spaces": False,
                "allow_special_chars": False,
                "must_start_with_letter": True,
                "naming_style": "CamelCase",
                "instance_suffix_pattern": "_[0-9]+"
            }
        }
    }
    path = tmp_path / "config.json"
    path.write_text(json.dumps(cfg))
    return path


@pytest.fixture
def snake_case_config(tmp_path):
    cfg = {
        "validators": {
            "NamingConventionValidator": {
                "enabled": True,
                "allow_spaces": False,
                "allow_special_chars": False,
                "must_start_with_letter": True,
                "naming_style": "snake_case",
            }
        }
    }
    path = tmp_path / "config.json"
    path.write_text(json.dumps(cfg))
    return path


@pytest.fixture
def usda_valid_camel(tmp_path) -> Path:
    path = tmp_path / "asset.usda"
    path.write_text("""\
#usda 1.0
(
    defaultPrim = "World"
)

def Xform "World"
{
    def Xform "TreeTrunk" {}
    def Xform "TreeBranch_1" {}
    def Xform "TreeBranch_2" {}
}
""")
    return path


@pytest.fixture
def usda_with_spaces(tmp_path) -> Path:
    path = tmp_path / "asset.usda"
    path.write_text("""\
#usda 1.0
(
    defaultPrim = "World"
)

def Xform "World"
{
    def Xform "Tree_Trunk" {}
}
""")
    return path


@pytest.fixture
def usda_starts_with_number(tmp_path) -> Path:
    path = tmp_path / "asset.usda"
    path.write_text("""\
#usda 1.0
(
    defaultPrim = "World"
)

def Xform "World"
{
    def Xform "TreeTrunk" {}
}
""")
    return path


@pytest.fixture
def usda_valid_snake(tmp_path) -> Path:
    path = tmp_path / "asset.usda"
    path.write_text("""\
#usda 1.0
(
    defaultPrim = "World"
)

def Xform "World"
{
    def Xform "tree_trunk" {}
    def Xform "tree_branch" {}
}
""")
    return path


def test_valid_camel_case_no_errors(camel_case_config):
    validator = NamingConventionValidator(PublishConfig(camel_case_config))
    path = Path(__file__).parent / "fixtures" / "valid_camel.usda"

    # Use inline fixture
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".usda", mode="w", delete=False) as f:
        f.write("""\
#usda 1.0
(
    defaultPrim = "World"
)
def Xform "World"
{
    def Xform "TreeTrunk" {}
    def Xform "TreeBranch_1" {}
}
""")
        tmp = f.name
    errors, warnings = validator.validate(Path(tmp))
    assert errors == []



def test_snake_case_valid_no_errors(snake_case_config, tmp_path):
    validator = NamingConventionValidator(PublishConfig(snake_case_config))
    path = tmp_path / "asset.usda"
    path.write_text("""\
#usda 1.0
(
    defaultPrim = "world"
)
def Xform "world"
{
    def Xform "tree_trunk" {}
}
""")
    errors, _ = validator.validate(path)
    assert errors == []


def test_camel_case_fails_snake_input(camel_case_config, tmp_path):
    validator = NamingConventionValidator(PublishConfig(camel_case_config))
    path = tmp_path / "asset.usda"
    path.write_text("""\
#usda 1.0
(
    defaultPrim = "world"
)
def Xform "world"
{
    def Xform "tree_trunk_geo" {}
}
""")
    errors, _ = validator.validate(path)
    assert any("CamelCase" in e for e in errors)


def test_any_style_allows_mixed(tmp_path):
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(json.dumps({
        "validators": {
            "NamingConventionValidator": {
                "enabled": True,
                "allow_spaces": False,
                "naming_style": "any"
            }
        }
    }))
    validator = NamingConventionValidator(PublishConfig(cfg_path))
    path = tmp_path / "asset.usda"
    path.write_text("""\
#usda 1.0
(
    defaultPrim = "World"
)
def Xform "World"
{
    def Xform "tree_trunk" {}
    def Xform "TreeBranch" {}
}
""")
    errors, _ = validator.validate(path)
    assert errors == []
