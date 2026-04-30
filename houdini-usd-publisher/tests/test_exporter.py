from pathlib import Path

import pytest

from houdini_usd_publisher.core.config import PublishConfig
from houdini_usd_publisher.core.exporter import ExportError, USDExporter

CONFIG_PATH = Path(__file__).parent.parent / "config" / "publish_config.json"


@pytest.fixture
def exporter():
    return USDExporter(PublishConfig(CONFIG_PATH))


def test_export_invalid_node_raises(exporter, tmp_path):
    with pytest.raises(ExportError, match="LOP node not found"):
        exporter.export("not_a_valid_path", tmp_path / "out.usda")
