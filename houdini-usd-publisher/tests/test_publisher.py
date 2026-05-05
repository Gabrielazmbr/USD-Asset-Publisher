from pathlib import Path

import pytest

from houdini_usd_publisher.core.config import PublishConfig
from houdini_usd_publisher.core.publisher import Publisher, PublishResult

CONFIG_PATH = Path(__file__).parent.parent / "config" / "publish_config.json"


@pytest.fixture
def publish_root(tmp_path):
    return tmp_path / "publish"


@pytest.fixture
def publisher(tmp_path, publish_root):
    config = PublishConfig(CONFIG_PATH)
    return Publisher(config, publish_root=publish_root)


# Export failure


def test_export_failure_returns_failed_result(publisher, tmp_path):
    result = publisher.publish(
        lop_node_path="invalid_path",
        asset_name="tree",
        version="v001",
        tmp_dir=tmp_path,
    )
    assert result.success is False
    assert any("Export" in e for e in result.errors)


def test_export_failure_has_correct_asset_info(publisher, tmp_path):
    result = publisher.publish("invalid_path", "tree", "v001", tmp_path)
    assert result.asset_name == "tree"
    assert result.version == "v001"
    assert result.published_path is None


# Validator behaviour


class AlwaysErrorValidator:
    def validate(self, path):
        return ["something is wrong"], []


class AlwaysWarnValidator:
    def validate(self, path):
        return [], ["something looks odd"]


class PassingValidator:
    def validate(self, path):
        return [], []


@pytest.fixture
def real_exported_file(tmp_path):
    """Fake exported USD file — enough for the packager to work with."""
    f = tmp_path / "tree_v001_tmp.usda"
    f.write_text("#usda 1.0\n")
    return f


@pytest.fixture
def publisher_with_real_export(tmp_path, publish_root, monkeypatch):
    config = PublishConfig(CONFIG_PATH)
    p = Publisher(config, publish_root=publish_root)

    fake_file = tmp_path / "tree_v001_tmp.usda"
    fake_file.write_text("""\
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

    monkeypatch.setattr(p.exporter, "export", lambda *args, **kwargs: fake_file)
    return p, tmp_path


def test_validator_errors_block_publish(publisher_with_real_export):
    p, tmp_path = publisher_with_real_export
    p.add_validator(AlwaysErrorValidator())
    result = p.publish("/stage/finalize", "tree", "v001", tmp_path)
    assert result.success is False
    assert "something is wrong" in result.errors


def test_validator_warnings_do_not_block_publish(publisher_with_real_export):
    p, tmp_path = publisher_with_real_export
    p.add_validator(AlwaysWarnValidator())
    result = p.publish("/stage/finalize", "tree", "v001", tmp_path)
    assert result.success is True
    assert "something looks odd" in result.warnings


def test_multiple_validators_all_errors_collected(publisher_with_real_export):
    p, tmp_path = publisher_with_real_export
    p.add_validator(AlwaysErrorValidator())
    p.add_validator(AlwaysWarnValidator())
    result = p.publish("/stage/finalize", "tree", "v001", tmp_path)
    assert result.success is False
    assert "something is wrong" in result.errors
    assert "something looks odd" in result.warnings


def test_passing_validator_allows_publish(publisher_with_real_export):
    p, tmp_path = publisher_with_real_export
    p.add_validator(PassingValidator())
    result = p.publish("/stage/finalize", "tree", "v001", tmp_path)
    assert result.success is True


# Successful publish


def test_successful_publish_returns_path(publisher_with_real_export, publish_root):
    p, tmp_path = publisher_with_real_export
    result = p.publish("/stage/finalize", "tree", "v001", tmp_path)
    assert result.success is True
    assert result.published_path == publish_root / "tree" / "v001" / "asset.usda"


def test_successful_publish_file_exists(publisher_with_real_export, publish_root):
    p, tmp_path = publisher_with_real_export
    result = p.publish("/stage/finalize", "tree", "v001", tmp_path)
    assert result.published_path.exists()


# Summary


def test_summary_shows_ok_on_success(publisher_with_real_export):
    p, tmp_path = publisher_with_real_export
    result = p.publish("/stage/finalize", "tree", "v001", tmp_path)
    assert "OK" in result.summary()


def test_summary_shows_failed_on_error(publisher, tmp_path):
    result = publisher.publish("invalid_path", "tree", "v001", tmp_path)
    assert "FAILED" in result.summary()


# Dry run
def test_dry_run_true(publisher_with_real_export, publish_root):
    p, tmp_path = publisher_with_real_export
    result = p.publish(
        lop_node_path="/stage/finalize",
        asset_name="tree",
        version="v001",
        tmp_dir=tmp_path,
        dry_run=True,
    )
    assert result.success is True
    assert result.published_path is None


def test_dry_run_does_not_write_files(publisher_with_real_export, publish_root):
    p, tmp_path = publisher_with_real_export
    p.publish(
        lop_node_path="/stage/finalize",
        asset_name="tree",
        version="v001",
        tmp_dir=tmp_path,
        dry_run=True,
    )
    assert not publish_root.exists()
