from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from houdini_usd_publisher.core.registry import PublishRegistry


@pytest.fixture
def mock_collection():
    return MagicMock()


@pytest.fixture
def registry(mock_collection):
    """Registry with a mocked MongoDB collection — no real connection needed."""
    reg = PublishRegistry.__new__(PublishRegistry)
    reg._client = MagicMock()
    reg._collection = mock_collection
    return reg


@pytest.fixture
def disconnected_registry():
    """Registry that failed to connect."""
    reg = PublishRegistry.__new__(PublishRegistry)
    reg._client = None
    reg._collection = None
    return reg


# Connection state

def test_connected_registry_is_connected(registry):
    assert registry.is_connected is True


def test_disconnected_registry_is_not_connected(disconnected_registry):
    assert disconnected_registry.is_connected is False


# record()

def test_record_inserts_document(registry, mock_collection):
    registry.record(
        asset_name="tree",
        version="v001",
        published_path=Path("/assets/tree/v001/asset.usda"),
        validators_run=["DefaultPrimValidator"],
        warnings=[],
        dry_run=False,
    )
    assert mock_collection.insert_one.called


def test_record_document_contains_correct_fields(registry, mock_collection):
    registry.record(
        asset_name="tree",
        version="v001",
        published_path=Path("/assets/tree/v001/asset.usda"),
        validators_run=["DefaultPrimValidator", "MetadataValidator"],
        warnings=["something looks odd"],
        dry_run=False,
    )
    doc = mock_collection.insert_one.call_args[0][0]
    assert doc["asset_name"] == "tree"
    assert doc["version"] == "v001"
    assert doc["published_path"] == "/assets/tree/v001/asset.usda"
    assert doc["validators_run"] == ["DefaultPrimValidator", "MetadataValidator"]
    assert doc["warnings"] == ["something looks odd"]
    assert doc["dry_run"] is False
    assert doc["success"] is True
    assert "published_at" in doc
    assert "published_by" in doc


def test_record_returns_true_on_success(registry):
    result = registry.record(
        asset_name="tree",
        version="v001",
        published_path=Path("/assets/tree/v001/asset.usda"),
        validators_run=[],
        warnings=[],
    )
    assert result is True


def test_record_returns_false_when_disconnected(disconnected_registry):
    result = disconnected_registry.record(
        asset_name="tree",
        version="v001",
        published_path=None,
        validators_run=[],
        warnings=[],
    )
    assert result is False


def test_record_returns_false_on_insert_failure(registry, mock_collection):
    mock_collection.insert_one.side_effect = Exception("network error")
    result = registry.record(
        asset_name="tree",
        version="v001",
        published_path=None,
        validators_run=[],
        warnings=[],
    )
    assert result is False


# get_versions()

def test_get_versions_returns_list(registry, mock_collection):
    mock_collection.find.return_value.sort.return_value = [
        {"asset_name": "tree", "version": "v002"},
        {"asset_name": "tree", "version": "v001"},
    ]
    result = registry.get_versions("tree")
    assert len(result) == 2
    assert result[0]["version"] == "v002"


def test_get_versions_returns_empty_when_disconnected(disconnected_registry):
    result = disconnected_registry.get_versions("tree")
    assert result == []


def test_get_versions_returns_empty_on_failure(registry, mock_collection):
    mock_collection.find.side_effect = Exception("timeout")
    result = registry.get_versions("tree")
    assert result == []


# get_latest_version()

def test_get_latest_version_returns_first_result(registry, mock_collection):
    mock_collection.find.return_value.sort.return_value = [
        {"asset_name": "tree", "version": "v003"},
    ]
    result = registry.get_latest_version("tree")
    assert result["version"] == "v003"


def test_get_latest_version_returns_none_when_disconnected(disconnected_registry):
    result = disconnected_registry.get_latest_version("tree")
    assert result is None


def test_get_latest_version_returns_none_when_no_versions(registry, mock_collection):
    mock_collection.find.return_value.sort.return_value = []
    result = registry.get_latest_version("tree")
    assert result is None
