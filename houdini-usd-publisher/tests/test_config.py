from pathlib import Path

import pytest

from houdini_usd_publisher.core.config import ConfigError, PublishConfig

CONFIG_PATH = Path(__file__).parent.parent / "config" / "publish_config.json"


def test_loads_valid_config():
    config = PublishConfig(CONFIG_PATH)
    assert config.export_format == "usda"
    assert config.assets_root == "assets"


def test_required_lod_variants():
    config = PublishConfig(CONFIG_PATH)
    assert config.required_lod_variants == ["low", "mid", "high"]


def test_required_metadata_fields():
    config = PublishConfig(CONFIG_PATH)
    assert "asset_name" in config.required_metadata_fields
    assert "version" in config.required_metadata_fields


def test_missing_config_raises(tmp_path):
    with pytest.raises(ConfigError):
        PublishConfig(tmp_path / "does_not_exist.json")


def test_invalid_json_raises(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{ not valid json }")
    with pytest.raises(ConfigError):
        PublishConfig(bad)
