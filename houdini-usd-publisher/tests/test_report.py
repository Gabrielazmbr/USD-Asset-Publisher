from pathlib import Path
import json
import pytest
from houdini_usd_publisher.core.report import PublishReport


@pytest.fixture
def report():
    return PublishReport()


@pytest.fixture
def asset_dir(tmp_path) -> Path:
    d = tmp_path / "tree" / "v001"
    d.mkdir(parents=True)
    return d


# --- write() ---

def test_write_creates_report_file(report, asset_dir):
    report.write(
        asset_dir=asset_dir,
        asset_name="tree",
        version="v001",
        published_path=asset_dir / "asset.usda",
        validators_run=["DefaultPrimValidator"],
        warnings=[],
        fixes=[],
        registry_recorded=True,
        success=True,
    )
    assert (asset_dir / "publish_report.json").exists()


def test_write_report_contains_correct_fields(report, asset_dir):
    report.write(
        asset_dir=asset_dir,
        asset_name="tree",
        version="v001",
        published_path=asset_dir / "asset.usda",
        validators_run=["DefaultPrimValidator", "MetadataValidator"],
        warnings=["something looks odd"],
        fixes=["Metadata field 'asset_name' set to 'tree'"],
        registry_recorded=True,
        success=True,
    )
    data = json.loads((asset_dir / "publish_report.json").read_text())
    assert data["asset_name"] == "tree"
    assert data["version"] == "v001"
    assert data["validators_run"] == ["DefaultPrimValidator", "MetadataValidator"]
    assert data["warnings"] == ["something looks odd"]
    assert data["fixes"] == ["Metadata field 'asset_name' set to 'tree'"]
    assert data["registry_recorded"] is True
    assert data["success"] is True
    assert "published_at" in data
    assert "published_by" in data


def test_write_report_registry_failed(report, asset_dir):
    report.write(
        asset_dir=asset_dir,
        asset_name="tree",
        version="v001",
        published_path=None,
        validators_run=[],
        warnings=[],
        fixes=[],
        registry_recorded=False,
        success=True,
    )
    data = json.loads((asset_dir / "publish_report.json").read_text())
    assert data["registry_recorded"] is False


# --- write_for_file() ---

def test_write_for_file_creates_report(report, tmp_path):
    usd_file = tmp_path / "asset.usda"
    usd_file.write_text("#usda 1.0\n")
    report.write_for_file(
        usd_file=usd_file,
        validators_run=["DefaultPrimValidator"],
        warnings=[],
        fixes=[],
        errors=[],
    )
    assert (tmp_path / "validation_report.json").exists()


def test_write_for_file_success_when_no_errors(report, tmp_path):
    usd_file = tmp_path / "asset.usda"
    usd_file.write_text("#usda 1.0\n")
    report.write_for_file(
        usd_file=usd_file,
        validators_run=[],
        warnings=[],
        fixes=[],
        errors=[],
    )
    data = json.loads((tmp_path / "validation_report.json").read_text())
    assert data["success"] is True


def test_write_for_file_failed_when_errors(report, tmp_path):
    usd_file = tmp_path / "asset.usda"
    usd_file.write_text("#usda 1.0\n")
    report.write_for_file(
        usd_file=usd_file,
        validators_run=[],
        warnings=[],
        fixes=[],
        errors=["Missing defaultPrim"],
    )
    data = json.loads((tmp_path / "validation_report.json").read_text())
    assert data["success"] is False
    assert "Missing defaultPrim" in data["errors"]


def test_write_for_file_contains_fixes(report, tmp_path):
    usd_file = tmp_path / "asset.usda"
    usd_file.write_text("#usda 1.0\n")
    report.write_for_file(
        usd_file=usd_file,
        validators_run=["MetadataValidator"],
        warnings=[],
        fixes=["Metadata field 'asset_name' set to 'tree'"],
        errors=[],
    )
    data = json.loads((tmp_path / "validation_report.json").read_text())
    assert len(data["fixes"]) == 1
    assert "asset_name" in data["fixes"][0]
