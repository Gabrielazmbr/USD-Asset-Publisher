from pathlib import Path

import pytest

from houdini_usd_publisher.core.config import PublishConfig
from houdini_usd_publisher.core.exporter import ExportError, USDExporter
from houdini_usd_publisher.core.packager import PackageError, USDPackager

CONFIG_PATH = Path(__file__).parent.parent / "config" / "publish_config.json"


def test_export_file_not_found(tmp_path):
    config = PublishConfig(CONFIG_PATH)
    packager = USDPackager(config)
    a_file = tmp_path / "missing.usda"
    with pytest.raises(PackageError, match=f"Exported file not found: {a_file}"):
        packager.package(a_file, "a_name", "v001", tmp_path)


@pytest.fixture
def package(tmp_path):
    config = PublishConfig(CONFIG_PATH)
    packager = USDPackager(config)

    a_file = tmp_path / "a_file.usda"
    a_file.write_text("usd data")
    result = packager.package(a_file, "a_name", "v001", tmp_path)

    return result, tmp_path


def test_folder_structure(package):
    result, tmp_path = package
    expected_path = tmp_path / "a_name" / "v001" / "asset.usda"
    assert result == expected_path
    assert result.exists()


def test_copied_file(package, tmp_path):
    result, _ = package
    assert result.read_text() == "usd data"


def test_copy_failure(tmp_path, monkeypatch):
    config = PublishConfig(CONFIG_PATH)
    packager = USDPackager(config)

    source = tmp_path / "a_file.usda"
    source.write_text("usd data")

    def fake_copy2(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr("houdini_usd_publisher.core.packager.shutil.copy2", fake_copy2)

    with pytest.raises(PackageError, match="Failed to copy"):
        packager.package(source, "a_name", "v001", tmp_path)


def test_stub_files_created(package):
    result, _ = package
    asset_dir = result.parent

    payload = asset_dir / "payload.usda"
    materials = asset_dir / "materials.usda"

    assert payload.exists()
    assert materials.exists()
    assert "#usda 1.0" in payload.read_text()


def test_publish_path():
    config = PublishConfig(CONFIG_PATH)
    packager = USDPackager(config)

    result = packager.publish_path("/tmp", "a_name", "v001")

    assert result == Path("/tmp") / "a_name" / "v001" / "asset.usda"
