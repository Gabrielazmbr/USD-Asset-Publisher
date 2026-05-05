import tempfile
from pathlib import Path

from houdini_usd_publisher.core.config import ConfigError, PublishConfig
from houdini_usd_publisher.core.publisher import Publisher

try:
    from PySide2 import QtCore, QtGui, QtWidgets
except ImportError:
    from PySide6 import QtCore, QtGui, QtWidgets


import os

_PROJECT_ROOT = os.environ.get(
    "USD_PUBLISHER_ROOT", "/your/full/path/to/houdini-usd-publisher"
)
CONFIG_PATH = Path(_PROJECT_ROOT) / "config" / "publish_config.json"


STYLE_BASE = """
    QWidget {
        background-color: #2b2b2b;
        color: #cccccc;
        font-family: monospace;
        font-size: 12px;
    }
    QLineEdit {
        background-color: #3c3c3c;
        border: 1px solid #555555;
        border-radius: 3px;
        padding: 4px;
        color: #ffffff;
    }
    QLabel {
        color: #aaaaaa;
    }
    QPushButton {
        background-color: #4a4a4a;
        border: 1px solid #666666;
        border-radius: 3px;
        padding: 6px 14px;
        color: #ffffff;
    }
    QPushButton:hover {
        background-color: #5a5a5a;
    }
    QPushButton:pressed {
        background-color: #3a3a3a;
    }
"""
# Button Styles
STYLE_PUBLISH_BTN = "QPushButton { background-color: #ed712e; border-color: #40916c; }"
STYLE_DRYRUN_BTN = "QPushButton { background-color: #458dc8; border-color: #6666aa; }"


class USDPublisherPanel(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(STYLE_BASE)
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 16, 16, 16)

        # Title
        title = QtWidgets.QLabel("USD Asset Publisher")
        title.setStyleSheet("font-size: 16px; color: #ffffff; font-weight: bold;")
        layout.addWidget(title)

        layout.addWidget(self._divider())

        # Form fields
        form = QtWidgets.QFormLayout()
        form.setSpacing(6)

        self.asset_input = QtWidgets.QLineEdit()
        self.asset_input.setPlaceholderText("e.g. AssetName")
        form.addRow("Asset Name:", self.asset_input)

        self.version_input = QtWidgets.QLineEdit()
        self.version_input.setPlaceholderText("e.g. v001")
        form.addRow("Version:", self.version_input)

        self.lop_input = QtWidgets.QLineEdit()
        self.lop_input.setText("/stage/finalize")
        form.addRow("LOP Node:", self.lop_input)

        # Publish Root
        self.publish_root_input = QtWidgets.QLineEdit()
        self.publish_root_input.setText(str(Path.cwd() / "assets"))

        layout.addLayout(form)
        layout.addWidget(self._divider())

        # Publish Root browse button
        root_layout = QtWidgets.QHBoxLayout()
        root_layout.addWidget(self.publish_root_input)
        browse_btn = QtWidgets.QPushButton("Browse")
        browse_btn.setFixedWidth(60)
        browse_btn.clicked.connect(self._on_browse)
        root_layout.addWidget(browse_btn)
        form.addRow("Publish Root:", root_layout)

        # Buttons
        btn_layout = QtWidgets.QHBoxLayout()

        self.dry_run_btn = QtWidgets.QPushButton("Dry Run")
        self.dry_run_btn.setStyleSheet(STYLE_DRYRUN_BTN)
        self.dry_run_btn.clicked.connect(self._on_dry_run)
        btn_layout.addWidget(self.dry_run_btn)

        self.publish_btn = QtWidgets.QPushButton("Publish")
        self.publish_btn.setStyleSheet(STYLE_PUBLISH_BTN)
        self.publish_btn.clicked.connect(self._on_publish)
        btn_layout.addWidget(self.publish_btn)

        layout.addLayout(btn_layout)

        # Results area
        self.results = QtWidgets.QTextEdit()
        self.results.setReadOnly(True)
        self.results.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                border: 1px solid #444444;
                border-radius: 3px;
                font-family: monospace;
                font-size: 11px;
            }
        """)
        self.results.setMinimumHeight(180)
        layout.addWidget(self.results)

        layout.addStretch()

    def _divider(self) -> QtWidgets.QFrame:
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setStyleSheet("color: #444444;")
        return line

    def _on_dry_run(self):
        self._run(dry_run=True)

    def _on_publish(self):
        self._run(dry_run=False)

    def _run(self, dry_run: bool):
        asset_name = self.asset_input.text().strip()
        version = self.version_input.text().strip()
        lop_path = self.lop_input.text().strip()
        publish_root = self.publish_root_input.text().strip()
        if not publish_root:
            self._show_error("Publish root is required.")
            return

        # Basic input validation
        if not asset_name:
            self._show_error("Asset name is required.")
            return
        if not version:
            self._show_error("Version is required.")
            return
        if not lop_path:
            self._show_error("LOP node path is required.")
            return

        self._set_busy(True)
        self.results.clear()

        try:
            config = PublishConfig(CONFIG_PATH)
            publisher = Publisher(config, publish_root=Path(publish_root))

            with tempfile.TemporaryDirectory() as tmp:
                result = publisher.publish(
                    lop_node_path=lop_path,
                    asset_name=asset_name,
                    version=version,
                    tmp_dir=tmp,
                    dry_run=dry_run,
                )

            self._show_result(result, dry_run)

        except ConfigError as e:
            self._show_error(f"Config error: {e}")
        except Exception as e:
            self._show_error(f"Unexpected error: {e}")
        finally:
            self._set_busy(False)

    def _show_result(self, result, dry_run: bool):
        html = []

        if result.success:
            label = "DRY RUN PASSED" if dry_run else "PUBLISHED"
            html.append(f'<p style="color:#40916c; font-weight:bold;">✓ {label}</p>')
        else:
            html.append('<p style="color:#e63946; font-weight:bold;">✗ FAILED</p>')

        for e in result.errors:
            html.append(f'<p style="color:#e63946;">ERROR &nbsp; {e}</p>')

        for w in result.warnings:
            html.append(f'<p style="color:#f4a261;">WARNING &nbsp; {w}</p>')

        if result.published_path:
            html.append(f'<p style="color:#aaaaaa;">→ {result.published_path}</p>')

        self.results.setHtml("".join(html))

    def _show_error(self, message: str):
        self.results.setHtml(
            f'<p style="color:#e63946; font-weight:bold;">✗ {message}</p>'
        )

    def _set_busy(self, busy: bool):
        self.publish_btn.setEnabled(not busy)
        self.dry_run_btn.setEnabled(not busy)
        if busy:
            self.results.setHtml('<p style="color:#aaaaaa;">Running...</p>')

    def _on_browse(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Select Publish Root",
            self.publish_root_input.text(),
        )
        if folder:
            self.publish_root_input.setText(folder)


try:

    def createInterface():
        return USDPublisherPanel()
except Exception:
    pass
