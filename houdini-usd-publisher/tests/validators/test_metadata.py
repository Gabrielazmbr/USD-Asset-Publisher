from pathlib import Path

import pytest

from houdini_usd_publisher.core.config import PublishConfig
from houdini_usd_publisher.validation.metadata import MetadataValidator

CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "publish_config.json"


@pytest.fixture
def validator():
    return MetadataValidator(PublishConfig(CONFIG_PATH))


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
def usda_missing_metadata(tmp_path) -> Path:
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
def usda_with_metadata(tmp_path) -> Path:
    path = tmp_path / "asset.usda"
    path.write_text("""\
#usda 1.0
(
    defaultPrim = "Asset"
)

def Xform "Asset" (
    customData = {
        string asset_name = "AssetName"
        string version = "v001"
    }
)
{
}
""")
    return path


def test_no_default_prim_returns_error(validator, usda_no_default_prim):
    errors, warnings = validator.validate(usda_no_default_prim)
    assert any("defaultPrim" in e for e in errors)


def test_missing_metadata_returns_errors(validator, usda_missing_metadata):
    errors, warnings = validator.validate(usda_missing_metadata)
    assert set(errors) == {
        "Missing required metadata field: 'asset_name'",
        "Missing required metadata field: 'version'",
    }


def test_missing_metadata_produces_no_warnings(validator, usda_missing_metadata):
    errors, warnings = validator.validate(usda_missing_metadata)
    assert warnings == []


def test_valid_metadata_produces_no_errors(validator, usda_with_metadata):
    errors, warnings = validator.validate(usda_with_metadata)
    assert errors == []


def test_valid_metadata_produces_no_warnings(validator, usda_with_metadata):
    errors, warnings = validator.validate(usda_with_metadata)
    assert warnings == []
