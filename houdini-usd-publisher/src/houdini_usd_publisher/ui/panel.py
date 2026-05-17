import os
import tempfile
from pathlib import Path

from houdini_usd_publisher.core.config import PublishConfig, ConfigError
from houdini_usd_publisher.core.publisher import Publisher
from houdini_usd_publisher.core.registry import PublishRegistry

try:
    from PySide2 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide6 import QtWidgets, QtCore, QtGui

_PROJECT_ROOT = os.environ.get(
    "USD_PUBLISHER_ROOT",
    "/your/full/path/to/houdini-usd-publisher"
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
    QTabWidget::pane {
        border: 1px solid #444444;
    }
    QTabBar::tab {
        background-color: #3c3c3c;
        color: #aaaaaa;
        padding: 6px 16px;
        border: 1px solid #444444;
    }
    QTabBar::tab:selected {
        background-color: #2b2b2b;
        color: #ffffff;
    }
    QCheckBox {
        color: #aaaaaa;
    }
"""

STYLE_PUBLISH_BTN = "QPushButton { background-color: #ed712e; border-color: #8d390c; }"
STYLE_DRYRUN_BTN = "QPushButton { background-color: #458dc8; border-color: #235176; }"
STYLE_VALIDATE_BTN = "QPushButton { background-color: #2d6a4f; border-color: #40916c; }"


class USDPublisherPanel(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(STYLE_BASE)
        self._build_ui()
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding
        )

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 16, 16, 16)

        title = QtWidgets.QLabel("USD Asset Publisher")
        title.setStyleSheet("font-size: 16px; color: #ffffff; font-weight: bold;")
        layout.addWidget(title)

        layout.addWidget(self._divider())

        # Tabs order
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.addTab(self._build_config_tab(), "Config")
        self.tabs.addTab(self._build_publish_tab(), "Publish")
        self.tabs.addTab(self._build_validate_tab(), "Validate File")
        layout.addWidget(self.tabs)


    def _build_config_tab(self) -> QtWidgets.QWidget:
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)

        # Header
        header = QtWidgets.QLabel("Pipeline Configuration")
        header.setStyleSheet("font-size: 13px; color: #ffffff; font-weight: bold;")
        layout.addWidget(header)

        info = QtWidgets.QLabel("Changes take effect on the next publish or validate.")
        info.setStyleSheet("color: #666666; font-size: 11px;")
        layout.addWidget(info)

        layout.addWidget(self._divider())

        # Scroll area for validators
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")


        scroll.setMinimumHeight(150)
        scroll.setMaximumHeight(400)

        scroll_widget = QtWidgets.QWidget()
        self._config_form_layout = QtWidgets.QVBoxLayout(scroll_widget)
        self._config_form_layout.setSpacing(4)

        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        layout.addWidget(self._divider())

        # Buttons
        btn_layout = QtWidgets.QHBoxLayout()

        reset_btn = QtWidgets.QPushButton("Reset to File")
        reset_btn.clicked.connect(self._on_config_reset)
        btn_layout.addWidget(reset_btn)

        save_btn = QtWidgets.QPushButton("Save Config")
        save_btn.setStyleSheet("QPushButton { background-color: #2d6a4f; border-color: #40916c; }")
        save_btn.clicked.connect(self._on_config_save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

        # Status label
        self._config_status = QtWidgets.QLabel("")
        self._config_status.setStyleSheet("font-size: 11px;")
        layout.addWidget(self._config_status)

        # Load config into form
        self._config_widgets = {}
        self._load_config_into_form()

        return widget


    def _load_config_into_form(self):
        """Read config file and populate the form widgets."""
        # Clear existing widgets
        while self._config_form_layout.count():
            item = self._config_form_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._config_widgets = {}

        try:
            import json
            with open(CONFIG_PATH) as f:
                config_data = json.load(f)
        except Exception as e:
            label = QtWidgets.QLabel(f"Could not load config: {e}")
            label.setStyleSheet("color: #e63946;")
            self._config_form_layout.addWidget(label)
            return

        validators = config_data.get("validators", {})

        for validator_name, validator_cfg in validators.items():
            # Validator group box
            group = QtWidgets.QGroupBox(validator_name)
            group.setStyleSheet("""
                QGroupBox {
                    color: #cccccc;
                    border: 1px solid #444444;
                    border-radius: 4px;
                    margin-top: 8px;
                    padding: 8px;
                    font-weight: bold;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 8px;
                    padding: 0 4px;
                }
            """)
            group_layout = QtWidgets.QFormLayout(group)
            group_layout.setSpacing(6)

            widgets = {}

            # Enabled checkbox
            enabled_cb = QtWidgets.QCheckBox()
            enabled_cb.setChecked(validator_cfg.get("enabled", True))
            group_layout.addRow("Enabled:", enabled_cb)
            widgets["enabled"] = enabled_cb

            # Auto-fix checkbox
            if "auto_fix" in validator_cfg:
                auto_fix_cb = QtWidgets.QCheckBox()
                auto_fix_cb.setChecked(validator_cfg.get("auto_fix", False))
                group_layout.addRow("Auto-fix:", auto_fix_cb)
                widgets["auto_fix"] = auto_fix_cb

            # required_fields — comma separated line edit
            if "required_fields" in validator_cfg:
                fields_input = QtWidgets.QLineEdit()
                fields_input.setText(", ".join(validator_cfg["required_fields"]))
                fields_input.setPlaceholderText("e.g. asset_name, version")
                group_layout.addRow("Required Fields:", fields_input)
                widgets["required_fields"] = fields_input

            # expected_axis — dropdown
            if "expected_axis" in validator_cfg:
                axis_combo = QtWidgets.QComboBox()
                axis_combo.setStyleSheet("""
                    QComboBox {
                        background-color: #3c3c3c;
                        border: 1px solid #555555;
                        border-radius: 3px;
                        padding: 6px;
                        color: #ffffff;
                    }
                """)
                axis_combo.addItems(["Y", "Z"])
                axis_combo.setCurrentText(validator_cfg.get("expected_axis", "Y"))
                group_layout.addRow("Expected Axis:", axis_combo)
                widgets["expected_axis"] = axis_combo

            # Variant set — editable values + add new set button
            if "required_sets" in validator_cfg:
                for set_name, set_values in validator_cfg["required_sets"].items():
                    row_layout = QtWidgets.QHBoxLayout()
                    set_input = QtWidgets.QLineEdit()
                    set_input.setText(", ".join(set_values))
                    set_input.setPlaceholderText("e.g. low, mid, high")
                    row_layout.addWidget(set_input)

                    delete_btn = QtWidgets.QPushButton("✕")
                    delete_btn.setFixedWidth(30)
                    delete_btn.setStyleSheet(
                        "QPushButton { background-color: #6a2a2a; border-color: #aa4444; "
                        "color: #ffffff; font-weight: bold; }"
                    )
                    row_layout.addWidget(delete_btn)

                    row_widget = QtWidgets.QWidget()
                    row_widget.setLayout(row_layout)
                    group_layout.addRow(f"'{set_name}' variants:", row_widget)
                    widgets[f"required_sets.{set_name}"] = set_input

                    def make_delete_callback(grp_layout, grp_widgets, s_name, r_widget):
                        def _delete():
                            # Remove from layout
                            for i in range(grp_layout.rowCount()):
                                if grp_layout.itemAt(i, QtWidgets.QFormLayout.FieldRole):
                                    if grp_layout.itemAt(i, QtWidgets.QFormLayout.FieldRole).widget() == r_widget:
                                        grp_layout.removeRow(i)
                                        break
                            # Remove from widgets dict
                            key = f"required_sets.{s_name}"
                            if key in grp_widgets:
                                del grp_widgets[key]
                        return _delete

                    delete_btn.clicked.connect(
                        make_delete_callback(group_layout, widgets, set_name, row_widget)
                    )

                # Add new variant set row
                add_layout = QtWidgets.QHBoxLayout()
                new_set_name = QtWidgets.QLineEdit()
                new_set_name.setPlaceholderText("set name e.g. shading")
                new_set_values = QtWidgets.QLineEdit()
                new_set_values.setPlaceholderText("values e.g. base, damaged")
                add_btn = QtWidgets.QPushButton("+")
                add_btn.setFixedWidth(30)
                add_layout.addWidget(new_set_name)
                add_layout.addWidget(new_set_values)
                add_layout.addWidget(add_btn)
                group_layout.addRow("Add set:", add_layout)

                def make_add_callback(grp_layout, grp_widgets, ns_name, ns_values, validator_n):
                    def _add():
                        name = ns_name.text().strip()
                        values = ns_values.text().strip()
                        if not name or not values:
                            return

                        row_layout = QtWidgets.QHBoxLayout()
                        new_input = QtWidgets.QLineEdit()
                        new_input.setText(values)
                        row_layout.addWidget(new_input)

                        del_btn = QtWidgets.QPushButton("✕")
                        del_btn.setFixedWidth(30)
                        del_btn.setStyleSheet(
                            "QPushButton { background-color: #6a2a2a; border-color: #aa4444; "
                            "color: #ffffff; font-weight: bold; }"
                        )
                        row_layout.addWidget(del_btn)

                        row_widget = QtWidgets.QWidget()
                        row_widget.setLayout(row_layout)
                        grp_layout.addRow(f"'{name}' variants:", row_widget)
                        grp_widgets[f"required_sets.{name}"] = new_input

                        def _delete():
                            for i in range(grp_layout.rowCount()):
                                field = grp_layout.itemAt(i, QtWidgets.QFormLayout.FieldRole)
                                if field and field.widget() == row_widget:
                                    grp_layout.removeRow(i)
                                    break
                            key = f"required_sets.{name}"
                            if key in grp_widgets:
                                del grp_widgets[key]

                        del_btn.clicked.connect(_delete)
                        ns_name.clear()
                        ns_values.clear()
                    return _add

                add_btn.clicked.connect(
                    make_add_callback(
                        group_layout, widgets,
                        new_set_name, new_set_values,
                        validator_name
                    )
                )
                widgets["_new_set_name"] = new_set_name
                widgets["_new_set_values"] = new_set_values

            self._config_widgets[validator_name] = widgets
            self._config_form_layout.addWidget(group)

        self._config_form_layout.addStretch()


    def _on_config_reset(self):
        """Reload from file, discarding unsaved changes."""
        self._load_config_into_form()
        self._config_status.setText("Reset to saved config.")
        self._config_status.setStyleSheet("color: #aaaaaa; font-size: 11px;")


    def _on_config_save(self):
        """Write current form values back to publish_config.json."""
        import json

        try:
            with open(CONFIG_PATH) as f:
                config_data = json.load(f)
        except Exception as e:
            self._config_status.setText(f"Could not read config: {e}")
            self._config_status.setStyleSheet("color: #e63946; font-size: 11px;")
            return

        validators = config_data.get("validators", {})

        for validator_name, widgets in self._config_widgets.items():
            if validator_name not in validators:
                continue

            cfg = validators[validator_name]

            # enabled
            if "enabled" in widgets:
                cfg["enabled"] = widgets["enabled"].isChecked()

            # auto_fix
            if "auto_fix" in widgets:
                cfg["auto_fix"] = widgets["auto_fix"].isChecked()

            # required_fields
            if "required_fields" in widgets:
                raw = widgets["required_fields"].text()
                cfg["required_fields"] = [
                    f.strip() for f in raw.split(",") if f.strip()
                ]

            # expected_axis
            if "expected_axis" in widgets:
                cfg["expected_axis"] = widgets["expected_axis"].currentText()

            # required_sets
            for key, widget in widgets.items():
                if key.startswith("required_sets."):
                    set_name = key.split(".", 1)[1]
                    raw = widget.text()
                    if "required_sets" not in cfg:
                        cfg["required_sets"] = {}
                    cfg["required_sets"][set_name] = [
                        v.strip() for v in raw.split(",") if v.strip()
                    ]
                # skip internal helper keys
                elif key.startswith("_"):
                    continue

            validators[validator_name] = cfg

        config_data["validators"] = validators

        try:
            with open(CONFIG_PATH, "w") as f:
                json.dump(config_data, f, indent=2)
            self._config_status.setText("Config saved successfully.")
            self._config_status.setStyleSheet("color: #40916c; font-size: 11px;")
        except Exception as e:
            self._config_status.setText(f"Could not save config: {e}")
            self._config_status.setStyleSheet("color: #e63946; font-size: 11px;")

    def _build_publish_tab(self) -> QtWidgets.QWidget:
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)

        # Form fields
        form = QtWidgets.QFormLayout()
        form.setSpacing(6)
        form.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)

        self.asset_input = QtWidgets.QLineEdit()
        self.asset_input.setPlaceholderText("e.g. tree")
        self.asset_input.setMinimumHeight(24)
        form.addRow("Asset Name:", self.asset_input)

        self.version_input = QtWidgets.QLineEdit()
        self.version_input.setPlaceholderText("e.g. v001")
        self.version_input.setMinimumHeight(24)
        form.addRow("Version:", self.version_input)

        self.lop_input = QtWidgets.QLineEdit()
        self.lop_input.setText("/stage/finalize")
        self.lop_input.setMinimumHeight(24)
        form.addRow("LOP Node:", self.lop_input)

        # Publish root with browse
        self.publish_root_input = QtWidgets.QLineEdit()
        self.publish_root_input.setText(str(Path.cwd() / "assets"))
        root_layout = QtWidgets.QHBoxLayout()
        root_layout.addWidget(self.publish_root_input)
        browse_btn = QtWidgets.QPushButton("Browse")
        browse_btn.setFixedWidth(100)
        browse_btn.clicked.connect(self._on_browse_publish_root)
        root_layout.addWidget(browse_btn)
        form.addRow("Publish Root:", root_layout)

        layout.addLayout(form)
        layout.addWidget(self._divider())

        # Auto-fix checkbox
        self.auto_fix_checkbox = QtWidgets.QCheckBox("Auto-fix correctable errors")
        layout.addWidget(self.auto_fix_checkbox)

        # Buttons
        btn_layout = QtWidgets.QHBoxLayout()
        self.dry_run_btn = QtWidgets.QPushButton("Dry Run")
        self.dry_run_btn.setStyleSheet(STYLE_DRYRUN_BTN)
        self.dry_run_btn.clicked.connect(self._on_dry_run)
        btn_layout.addWidget(self.dry_run_btn)

        self.publish_btn = QtWidgets.QPushButton("Publish")
        self.publish_btn.setStyleSheet(STYLE_PUBLISH_BTN)
        self.publish_btn.clicked.connect(self._on_publish)
        self.publish_root_input.setMinimumHeight(24)
        btn_layout.addWidget(self.publish_btn)
        layout.addLayout(btn_layout)

        # Results
        self.results = self._build_results_area()
        layout.addWidget(self.results)

        layout.addWidget(self._divider())

        # History
        history_label = QtWidgets.QLabel("Recent Publishes")
        history_label.setStyleSheet("font-size: 13px; color: #ffffff; font-weight: bold;")
        layout.addWidget(history_label)

        refresh_btn = QtWidgets.QPushButton("Refresh History")
        refresh_btn.clicked.connect(self._on_refresh_history)
        layout.addWidget(refresh_btn)

        self.history_table = QtWidgets.QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(["Asset", "Version", "Published At", "Warnings"])
        self.history_table.horizontalHeader().setStretchLastSection(True)
        self.history_table.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        self.history_table.setSelectionBehavior(QtWidgets.QTableWidget.SelectRows)
        self.history_table.setMinimumHeight(100)
        self.history_table.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e1e;
                border: 1px solid #444444;
                gridline-color: #333333;
                font-size: 11px;
            }
            QHeaderView::section {
                background-color: #3c3c3c;
                color: #aaaaaa;
                padding: 4px;
                border: none;
            }
            QTableWidget::item {
                padding: 4px;
                color: #cccccc;
            }
            QTableWidget::item:selected {
                background-color: #4a4a6a;
            }
        """)
        layout.addWidget(self.history_table)
        layout.addStretch()

        return widget

    def _build_validate_tab(self) -> QtWidgets.QWidget:
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)

        form = QtWidgets.QFormLayout()
        form.setSpacing(6)

        # File picker
        self.validate_file_input = QtWidgets.QLineEdit()
        self.validate_file_input.setPlaceholderText("path/to/asset.usda")
        file_layout = QtWidgets.QHBoxLayout()
        file_layout.addWidget(self.validate_file_input)
        browse_file_btn = QtWidgets.QPushButton("Browse")
        browse_file_btn.setFixedWidth(100)
        browse_file_btn.clicked.connect(self._on_browse_validate_file)
        file_layout.addWidget(browse_file_btn)
        form.addRow("USD File:", file_layout)

        # Optional fields for auto-fix
        self.validate_asset_input = QtWidgets.QLineEdit()
        self.validate_asset_input.setPlaceholderText("e.g. tree (used by auto-fix)")
        form.addRow("Asset Name:", self.validate_asset_input)

        self.validate_version_input = QtWidgets.QLineEdit()
        self.validate_version_input.setPlaceholderText("e.g. v001 (used by auto-fix)")
        form.addRow("Version:", self.validate_version_input)

        layout.addLayout(form)
        layout.addWidget(self._divider())

        # Auto-fix checkbox
        self.validate_auto_fix_checkbox = QtWidgets.QCheckBox("Auto-fix correctable errors")
        layout.addWidget(self.validate_auto_fix_checkbox)

        # Validate button
        self.validate_btn = QtWidgets.QPushButton("Validate")
        self.validate_btn.setStyleSheet(STYLE_VALIDATE_BTN)
        self.validate_btn.clicked.connect(self._on_validate_file)
        layout.addWidget(self.validate_btn)

        # Results
        self.validate_results = self._build_results_area()
        layout.addWidget(self.validate_results)

        # Open in Houdini button — only useful inside Houdini
        self.open_in_houdini_btn = QtWidgets.QPushButton("Open Fixed File in Houdini")
        self.open_in_houdini_btn.setStyleSheet(
            "QPushButton { background-color: #4a4a4a; border-color: #666666; }"
        )
        self.open_in_houdini_btn.clicked.connect(self._on_open_in_houdini)
        self.open_in_houdini_btn.setEnabled(False)  # enabled after successful validate
        layout.addWidget(self.open_in_houdini_btn)

        layout.addStretch()
        return widget

    def _build_results_area(self) -> QtWidgets.QTextEdit:
        results = QtWidgets.QTextEdit()
        results.setReadOnly(True)
        results.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                border: 1px solid #444444;
                border-radius: 3px;
                font-family: monospace;
                font-size: 11px;
            }
        """)
        results.setMinimumHeight(120)
        return results

    def _divider(self) -> QtWidgets.QFrame:
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setStyleSheet("color: #444444;")
        return line

    def _on_open_in_houdini(self):
        file_path = self.validate_file_input.text().strip()
        if not file_path:
            return

        try:
            import hou

            stage = hou.node("/stage")
            if stage is None:
                stage = hou.node("/").createNode("lopnet", "stage")

            sublayer = stage.createNode("sublayer", "imported_usd")
            sublayer.parm("filepath1").set(file_path)
            sublayer.setDisplayFlag(True)

            self._show_success(
                self.validate_results,
                f"Imported into /stage/imported_usd"
            )

        except ImportError:
            self._show_error(
                self.validate_results,
                "Open in Houdini is only available inside a Houdini session."
            )
        except Exception as e:
            self._show_error(self.validate_results, f"Could not import: {e}")

    # --- Publish tab actions ---

    def _on_dry_run(self):
        self._run(dry_run=True)

    def _on_publish(self):
        self._run(dry_run=False)

    def _run(self, dry_run: bool):
        asset_name = self.asset_input.text().strip()
        version = self.version_input.text().strip()
        lop_path = self.lop_input.text().strip()
        publish_root = self.publish_root_input.text().strip()

        if not asset_name:
            self._show_error(self.results, "Asset name is required.")
            return
        if not version:
            self._show_error(self.results, "Version is required.")
            return
        if not lop_path:
            self._show_error(self.results, "LOP node path is required.")
            return
        if not publish_root:
            self._show_error(self.results, "Publish root is required.")
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
                    auto_fix=self.auto_fix_checkbox.isChecked(),
                )

            self._show_result(self.results, result, dry_run)

        except ConfigError as e:
            self._show_error(self.results, f"Config error: {e}")
        except Exception as e:
            self._show_error(self.results, f"Unexpected error: {e}")
        finally:
            self._set_busy(False)

    def _on_browse_publish_root(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Publish Root", self.publish_root_input.text()
        )
        if folder:
            self.publish_root_input.setText(folder)

    def _on_refresh_history(self):
        try:
            registry = PublishRegistry()
            asset_name = self.asset_input.text().strip()
            records = registry.get_versions(asset_name) if asset_name else registry.get_recent()
            self._populate_history(records)
        except Exception as e:
            print(f"History error: {e}")
            self._populate_history([])

    def _populate_history(self, records: list[dict]):
        self.history_table.setRowCount(0)
        for record in records:
            row = self.history_table.rowCount()
            self.history_table.insertRow(row)
            self.history_table.setItem(row, 0, QtWidgets.QTableWidgetItem(record.get("asset_name", "")))
            self.history_table.setItem(row, 1, QtWidgets.QTableWidgetItem(record.get("version", "")))
            published_at = record.get("published_at", "")
            if hasattr(published_at, "strftime"):
                published_at = published_at.strftime("%Y-%m-%d %H:%M")
            self.history_table.setItem(row, 2, QtWidgets.QTableWidgetItem(str(published_at)))
            warnings = record.get("warnings", [])
            warning_text = f"{len(warnings)} ⚠" if warnings else "0"
            warning_item = QtWidgets.QTableWidgetItem(warning_text)
            if warnings:
                warning_item.setForeground(QtGui.QColor("#f4a261"))
            self.history_table.setItem(row, 3, warning_item)
        self.history_table.resizeColumnsToContents()

    # --- Validate tab actions ---

    def _on_browse_validate_file(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select USD File",
            "",
            "USD Files (*.usd *.usda *.usdc);;All Files (*)"
        )
        if path:
            self.validate_file_input.setText(path)

    def _on_validate_file(self):
        file_path = self.validate_file_input.text().strip()
        if not file_path:
            self._show_error(self.validate_results, "Please select a USD file.")
            return

        path = Path(file_path)
        if not path.exists():
            self._show_error(self.validate_results, f"File not found: {file_path}")
            return

        self.validate_btn.setEnabled(False)
        self.validate_results.clear()

        try:
            config = PublishConfig(CONFIG_PATH)

            from houdini_usd_publisher.validation.default_prim import DefaultPrimValidator
            from houdini_usd_publisher.validation.metadata import MetadataValidator
            from houdini_usd_publisher.validation.variant_set import VariantSetValidator
            from houdini_usd_publisher.validation.kind import KindValidator
            from houdini_usd_publisher.validation.material import MaterialValidator
            from houdini_usd_publisher.validation.up_axis import UpAxisValidator

            validator_registry = {
                "DefaultPrimValidator": DefaultPrimValidator(),
                "MetadataValidator": MetadataValidator(config),
                "VariantSetValidator": VariantSetValidator(config),
                "KindValidator": KindValidator(),
                "MaterialValidator": MaterialValidator(),
                "UpAxisValidator": UpAxisValidator(config),
            }

            validators = [
                validator_registry[name]
                for name in config.enabled_validators
                if name in validator_registry
            ]

            # Auto-fix pass — respects per-validator auto_fix flag in config
            fixes = []
            if self.validate_auto_fix_checkbox.isChecked():
                for v in validators:
                    name = v.__class__.__name__
                    if hasattr(v, "fix") and config.is_auto_fix_enabled(name):
                        fixes.extend(v.fix(
                            path,
                            asset_name=self.validate_asset_input.text().strip(),
                            version=self.validate_version_input.text().strip(),
                        ))

            # Validate
            all_errors = []
            all_warnings = []
            for v in validators:
                errors, warnings = v.validate(path)
                all_errors.extend(errors)
                all_warnings.extend(warnings)

            self._show_validate_result(path, all_errors, all_warnings, fixes)

            # Write validation report next to the file
            from houdini_usd_publisher.core.report import PublishReport
            report = PublishReport()
            report_path = report.write_for_file(
                usd_file=path,
                validators_run=[v.__class__.__name__ for v in validators],
                warnings=all_warnings,
                fixes=fixes,
                errors=all_errors,
            )
            # Append report path to results
            self.validate_results.append(
                f'<p style="color:#666666;">Report: {report_path}</p>'
            )

        except Exception as e:
            self._show_error(self.validate_results, f"Unexpected error: {e}")
        finally:
            self.validate_btn.setEnabled(True)

    def _show_validate_result(self, path, errors, warnings, fixes):
        html = []
        html.append(f'<p style="color:#aaaaaa;">File: {path.name}</p>')

        if not errors:
            html.append('<p style="color:#40916c; font-weight:bold;">✓ VALID</p>')
            self.open_in_houdini_btn.setEnabled(True)
        else:
            html.append('<p style="color:#e63946; font-weight:bold;">✗ INVALID</p>')
            self.open_in_houdini_btn.setEnabled(False)

        for f in fixes:
            html.append(f'<p style="color:#48cae4;">FIXED &nbsp; {f}</p>')
        for e in errors:
            html.append(f'<p style="color:#e63946;">ERROR &nbsp; {e}</p>')
        for w in warnings:
            html.append(f'<p style="color:#f4a261;">WARNING &nbsp; {w}</p>')

        if fixes:
            html.append(
                f'<p style="color:#aaaaaa;">Fixed file: {path}</p>'
            )

        self.validate_results.setHtml("".join(html))
    # --- Shared helpers ---

    def _show_result(self, results_widget, result, dry_run: bool):
        html = []
        if result.success:
            label = "DRY RUN PASSED" if dry_run else "PUBLISHED"
            html.append(f'<p style="color:#40916c; font-weight:bold;">✓ {label}</p>')
            if not dry_run:
                self._on_refresh_history()
        else:
            html.append('<p style="color:#e63946; font-weight:bold;">✗ FAILED</p>')

        for f in result.fixes:
            html.append(f'<p style="color:#48cae4;">FIXED &nbsp; {f}</p>')
        for e in result.errors:
            html.append(f'<p style="color:#e63946;">ERROR &nbsp; {e}</p>')
        for w in result.warnings:
            html.append(f'<p style="color:#f4a261;">WARNING &nbsp; {w}</p>')
        if result.published_path:
            html.append(f'<p style="color:#aaaaaa;">→ {result.published_path}</p>')

        results_widget.setHtml("".join(html))

    def _show_error(self, results_widget, message: str):
        results_widget.setHtml(
            f'<p style="color:#e63946; font-weight:bold;">✗ {message}</p>'
        )

    def _show_success(self, results_widget, message: str):
        current = results_widget.toHtml()
        results_widget.setHtml(
            current + f'<p style="color:#40916c;">✓ {message}</p>'
        )

    def _set_busy(self, busy: bool):
        self.publish_btn.setEnabled(not busy)
        self.dry_run_btn.setEnabled(not busy)
        if busy:
            self.results.setHtml('<p style="color:#aaaaaa;">Running...</p>')


try:
    def createInterface():
        return USDPublisherPanel()
except Exception:
    pass
