import pytest
from pathlib import Path

ROOT = Path(__file__).parent.parent
CONFIG_PATH = ROOT / "config" / "publish_config.json"

import sys
sys.path.insert(0, str(ROOT / "src"))


@pytest.fixture(scope="session")
def config():
    from houdini_usd_publisher.core.config import PublishConfig
    return PublishConfig(CONFIG_PATH)


@pytest.fixture
def fresh_config(tmp_path):
    """
    A known-good config in tmp_path — unaffected by UI changes to the real file.
    Use this in tests that depend on specific config values.
    """
    import json
    cfg = {
        "export_format": "usda",
        "assets_root": "assets",
        "validators": {
            "DefaultPrimValidator": {"enabled": True, "auto_fix": True},
            "MetadataValidator": {
                "enabled": True,
                "auto_fix": True,
                "required_fields": ["asset_name", "version"]
            },
            "VariantSetValidator": {
                "enabled": True,
                "required_sets": {"lod": ["low", "mid", "high"]}
            },
            "KindValidator": {"enabled": True, "auto_fix": True},
            "MaterialValidator": {"enabled": True},
            "UpAxisValidator": {
                "enabled": True,
                "auto_fix": True,
                "expected_axis": "Y"
            },
            "FileReferenceValidator": {"enabled": True},
            "NamingConventionValidator": {
                "enabled": True,
                "allow_special_chars": False,
                "naming_style": "any",
                "instance_suffix_pattern": "_[0-9]+"
            }
        }
    }
    path = tmp_path / "publish_config.json"
    with open(path, "w") as f:
        json.dump(cfg, f)
    return path
