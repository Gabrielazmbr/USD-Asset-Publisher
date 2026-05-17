#!/usr/bin/env python3
"""
USD Asset Publisher — Houdini Package Installer

Installs the Houdini package definition so the tool loads automatically
on Houdini startup. Run this once per machine.

Usage:
    # From inside Houdini's Python Shell:
    exec(open('/path/to/houdini-usd-publisher/install.py').read())

    # From terminal:
    uv run python install.py
"""

import json
import platform
import sys
from pathlib import Path


PACKAGE_NAME = "houdini-usd-publisher"

# Houdini preferences locations per OS
HOUDINI_PREFS = {
    "Linux": lambda version: Path.home() / f"houdini{version}",
    "Darwin": lambda version: Path.home() / "Library" / "Preferences" / "houdini" / version,
    "Windows": lambda version: Path.home() / "Documents" / "houdini" / version,
}


def get_houdini_version() -> str:
    """Get the current Houdini version string e.g. '21.0'."""
    try:
        import hou
        major = hou.getenv("HOUDINI_MAJOR_RELEASE")
        minor = hou.getenv("HOUDINI_MINOR_RELEASE")
        return f"{major}.{minor}"
    except ImportError:
        # Running outside Houdini — ask the user
        version = input("Enter your Houdini version (e.g. 21.0): ").strip()
        if not version:
            raise ValueError("Houdini version is required")
        return version


def find_houdini_prefs(version: str) -> Path:
    """Find the Houdini preferences folder for the current OS."""
    op_sys = platform.system()
    if op_sys not in HOUDINI_PREFS:
        raise OSError(f"Unsupported OS: {op_sys}")

    prefs = HOUDINI_PREFS[op_sys](version)
    if not prefs.exists():
        raise FileNotFoundError(
            f"Houdini preferences folder not found: {prefs}\n"
            f"Make sure Houdini {version} has been launched at least once."
        )
    return prefs


def write_package(packages_dir: Path, project_root: Path) -> Path:
    """Write the package JSON file."""
    package = {
        "env": [
            {
                "PYTHONPATH": {
                    "value": str(project_root / "src"),
                    "method": "prepend"
                }
            },
            {
                "USD_PUBLISHER_ROOT": str(project_root)
            }
        ]
    }

    package_file = packages_dir / f"{PACKAGE_NAME}.json"
    with open(package_file, "w") as f:
        json.dump(package, f, indent=2)

    return package_file


def install():
    print(f"\n USD Asset Publisher — Package Installer")
    print(f" {'─' * 40}")

    project_root = Path(__file__).parent.resolve()
    print(f" Project root: {project_root}")

    # Verify project structure looks correct
    if not (project_root / "src" / "houdini_usd_publisher").exists():
        print(f"\n ERROR: Could not find houdini_usd_publisher package.")
        print(f" Make sure you're running this from the project root.")
        sys.exit(1)

    if not (project_root / "config" / "publish_config.json").exists():
        print(f"\n ERROR: Could not find publish_config.json.")
        sys.exit(1)

    # Get Houdini version
    try:
        version = get_houdini_version()
        print(f" Houdini version: {version}")
    except (ValueError, Exception) as e:
        print(f"\n ERROR: {e}")
        sys.exit(1)

    # Find preferences folder
    try:
        prefs = find_houdini_prefs(version)
        print(f" Houdini prefs: {prefs}")
    except FileNotFoundError as e:
        print(f"\n ERROR: {e}")
        sys.exit(1)

    # Create packages folder
    packages_dir = prefs / "packages"
    packages_dir.mkdir(exist_ok=True, parents=False)
    print(f" Packages folder: {packages_dir}")

    # Check for existing installation
    package_file = packages_dir / f"{PACKAGE_NAME}.json"
    if package_file.exists():
        print(f"\n WARNING: Package already installed at:")
        print(f"   {package_file}")
        answer = input(" Overwrite? (y/n): ").strip().lower()
        if answer != "y":
            print(" Installation cancelled.")
            sys.exit(0)

    # Write package file
    written = write_package(packages_dir, project_root)
    print(f"\n Package installed: {written}")
    print(f"\n Contents:")
    print(json.dumps(json.loads(written.read_text()), indent=2))
    print(f"\n Done. Restart Houdini to load the USD Asset Publisher.")
    print(f" The panel will be available under Windows → Python Panels.")

    # Write panel registration
    panel_written = write_panel(prefs, project_root)
    print(f" Panel registered: {panel_written}")


def write_panel(houdini_prefs: Path, project_root: Path) -> Path:
    """Write the Python Panel registration file."""
    panels_dir = houdini_prefs / "python_panels"
    panels_dir.mkdir(exist_ok=True, parents=False)

    panel_script = f"""\
import sys
import os

# Ensure the package is importable
_src = r"{project_root / 'src'}"
if _src not in sys.path:
    sys.path.insert(0, _src)

# Set project root for config resolution
os.environ["USD_PUBLISHER_ROOT"] = r"{project_root}"

# Also add venv site-packages if available
_venv = r"{project_root / '.venv' / 'lib'}"
import glob
for _sp in glob.glob(f"{{_venv}}/python*/site-packages"):
    if _sp not in sys.path:
        sys.path.insert(0, _sp)

from houdini_usd_publisher.ui.panel import createInterface
"""

    pypanel_content = f"""\
<?xml version="1.0" encoding="UTF-8"?>
<pythonPanelDocument>
  <interface name="USDPublisher" label="USD Asset Publisher" icon="MISC_python" help_url="">
    <script><![CDATA[
{panel_script}
    ]]></script>
    <includeInPaneTabMenu menu_position="0" create_separator="false"/>
  </interface>
</pythonPanelDocument>
"""

    panel_file = panels_dir / "usd_publisher.pypanel"
    with open(panel_file, "w") as f:
        f.write(pypanel_content)

    return panel_file

if __name__ == "__main__":
    install()
