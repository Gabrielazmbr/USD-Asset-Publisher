import pytest
from pathlib import Path
from houdini_usd_publisher.core.config import PublishConfig, ConfigError

CONFIG_PATH = Path(__file__).parent.parent / "config" / "publish_config.json"


@pytest.fixture
def config(fresh_config):
    return PublishConfig(fresh_config)


def test_loads_valid_config():
    c = PublishConfig(CONFIG_PATH)
    assert c.export_format == "usda"
    assert c.assets_root == "assets"


def test_enabled_validators(config):
    enabled = config.enabled_validators
    assert "DefaultPrimValidator" in enabled
    assert "MetadataValidator" in enabled
    assert "VariantSetValidator" in enabled


def test_validator_config_metadata(config):
    cfg = config.get_validator_config("MetadataValidator")
    assert "asset_name" in cfg.get("required_fields", [])
    assert "version" in cfg.get("required_fields", [])


def test_validator_config_variants(config):
    cfg = config.get_validator_config("VariantSetValidator")
    assert "lod" in cfg.get("required_sets", {})
    assert cfg["required_sets"]["lod"] == ["low", "mid", "high"]


def test_is_validator_enabled(config):
    assert config.is_validator_enabled("DefaultPrimValidator") is True


def test_is_validator_enabled_unknown(config):
    assert config.is_validator_enabled("NonExistentValidator") is False


def test_auto_fix_enabled_for_metadata(config):
    assert config.is_auto_fix_enabled("MetadataValidator") is True


def test_auto_fix_disabled_for_variant_set(config):
    assert config.is_auto_fix_enabled("VariantSetValidator") is False

def test_auto_fix_disabled_for_material(config):
    assert config.is_auto_fix_enabled("MaterialValidator") is False

def test_auto_fix_disabled_for_unknown(config):
    assert config.is_auto_fix_enabled("NonExistentValidator") is False


def test_disabled_validator_not_in_enabled_list(tmp_path):
    import json
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(json.dumps({
        "validators": {
            "DefaultPrimValidator": {"enabled": False},
            "MetadataValidator": {"enabled": True, "required_fields": []}
        }
    }))
    c = PublishConfig(cfg_path)
    assert "DefaultPrimValidator" not in c.enabled_validators
    assert "MetadataValidator" in c.enabled_validators


def test_missing_config_raises(tmp_path):
    with pytest.raises(ConfigError):
        PublishConfig(tmp_path / "does_not_exist.json")


def test_invalid_json_raises(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{ not valid json }")
    with pytest.raises(ConfigError):
        PublishConfig(bad)
