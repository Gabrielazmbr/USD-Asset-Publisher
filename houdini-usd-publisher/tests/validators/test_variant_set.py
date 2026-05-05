from pathlib import Path

import pytest

from houdini_usd_publisher.core.config import PublishConfig
from houdini_usd_publisher.validation.variant_set import VariantSetValidator

CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "publish_config.json"


@pytest.fixture
def validator():
    return VariantSetValidator(PublishConfig(CONFIG_PATH))


@pytest.fixture
def usda_no_default_prim(tmp_path) -> Path:
    path = tmp_path / "asset.usda"
    path.write_text("""\
#usda 1.0

def Xform "Asset"
{
}
""")
    return path


@pytest.fixture
def usda_no_variants(tmp_path) -> Path:
    path = tmp_path / "asset.usda"
    path.write_text("""\
#usda 1.0
(
    defaultPrim = "Asset"
)

def Xform "Asset"
{
}
""")
    return path


@pytest.fixture
def usda_with_variants(tmp_path) -> Path:
    path = tmp_path / "asset.usda"
    path.write_text("""\
#usda 1.0
(
    defaultPrim = "Asset"
)

def Xform "Asset" (
    variants = {
        string lod = "mid"
    }
    variantSets = "lod"
)
{
    variantSet "lod" = {
        "low" {}
        "mid" {}
        "high" {}
    }
}
""")
    return path


def test_no_default_prim_returns_error(validator, usda_no_default_prim):
    errors, warnings = validator.validate(usda_no_default_prim)
    assert any("defaultPrim" in e for e in errors)


def test_missing_variant_set_returns_single_error(validator, usda_no_variants):
    errors, warnings = validator.validate(usda_no_variants)
    assert errors == ["Missing required variant set: 'lod'"]


def test_valid_variants_produces_no_errors(validator, usda_with_variants):
    errors, warnings = validator.validate(usda_with_variants)
    assert errors == []


def test_valid_variants_produces_no_warnings(validator, usda_with_variants):
    errors, warnings = validator.validate(usda_with_variants)
    assert warnings == []
