import os
from pathlib import Path

# Set project root for standalone mode
os.environ["USD_PUBLISHER_ROOT"] = str(Path(__file__).parent.parent.parent.parent)

import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch


from PySide6 import QtWidgets

"""
Runner for the USD Publisher panel.
Runs outside Houdini for UI development.
Exports are simulated.

Usage:
    uv run python -m houdini_usd_publisher.ui.dummy_panel
"""


def create_fake_export(asset_name: str, version: str, tmp_dir: str) -> Path:
    fake = Path(tmp_dir) / f"{asset_name}_{version}_tmp.usda"
    fake.write_text("""\
#usda 1.0
(
    defaultPrim = "Asset"
)

def Xform "Asset" (
    customData = {
        string asset_name = "tree"
        string version = "v001"
    }
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
    return fake


def main():
    # Patch the exporter so it writes a valid fake USD instead of calling hou
    with patch(
        "houdini_usd_publisher.core.exporter.USDExporter.export",
        side_effect=lambda self_inner, lop_path, output_path: create_fake_export(
            "tree", "v001", str(Path(output_path).parent)
        ),
    ):
        # Import panel after patching so it gets the mocked exporter
        from houdini_usd_publisher.ui.panel import USDPublisherPanel

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
        window = QtWidgets.QMainWindow()
        window.setWindowTitle("USD Publisher — Standalone Dev Mode")
        window.setMinimumSize(500, 600)

        panel = USDPublisherPanel()
        window.setCentralWidget(panel)
        window.show()

        sys.exit(app.exec())


if __name__ == "__main__":
    main()
