from pathlib import Path
import pytest
from houdini_usd_publisher.core.config import PublishConfig
from houdini_usd_publisher.validation.default_prim import DefaultPrimValidator
from houdini_usd_publisher.validation.metadata import MetadataValidator
from pxr import Usd
from pxr import Usd, UsdGeom

@pytest.fixture
def config(fresh_config):
    from houdini_usd_publisher.core.config import PublishConfig
    return PublishConfig(fresh_config)


@pytest.fixture
def usda_no_default_prim(tmp_path) -> Path:
    path = tmp_path / "asset.usda"
    path.write_text("""\
#usda 1.0

def Xform "World"
{
}
""")
    return path


@pytest.fixture
def usda_missing_metadata(tmp_path) -> Path:
    path = tmp_path / "asset.usda"
    path.write_text("""\
#usda 1.0
(
    defaultPrim = "World"
)

def Xform "World"
{
}
""")
    return path


# --- DefaultPrimValidator.fix() ---

def test_fix_default_prim_sets_default_prim(usda_no_default_prim):
    validator = DefaultPrimValidator()
    fixes = validator.fix(usda_no_default_prim)
    assert len(fixes) == 1
    assert "defaultPrim" in fixes[0]


def test_fix_default_prim_writes_to_file(usda_no_default_prim):
    validator = DefaultPrimValidator()
    validator.fix(usda_no_default_prim)
    stage = Usd.Stage.Open(str(usda_no_default_prim))
    assert stage.GetDefaultPrim().IsValid()


def test_fix_default_prim_no_fix_needed(usda_missing_metadata):
    """Should return no fixes if defaultPrim already set."""
    validator = DefaultPrimValidator()
    fixes = validator.fix(usda_missing_metadata)
    assert fixes == []


# --- MetadataValidator.fix() ---

def test_fix_metadata_sets_asset_name(config, usda_missing_metadata):
    validator = MetadataValidator(config)
    fixes = validator.fix(usda_missing_metadata, asset_name="tree", version="v001")
    assert any("asset_name" in f for f in fixes)


def test_fix_metadata_sets_version(config, usda_missing_metadata):
    validator = MetadataValidator(config)
    fixes = validator.fix(usda_missing_metadata, asset_name="tree", version="v001")
    assert any("version" in f for f in fixes)


def test_fix_metadata_writes_to_file(config, usda_missing_metadata):
    validator = MetadataValidator(config)
    validator.fix(usda_missing_metadata, asset_name="tree", version="v001")
    stage = Usd.Stage.Open(str(usda_missing_metadata))
    root = stage.GetDefaultPrim()
    assert root.HasCustomDataKey("asset_name")
    assert root.HasCustomDataKey("version")


def test_fix_metadata_no_fix_needed(config, tmp_path):
    """Should return no fixes if metadata already present."""
    path = tmp_path / "asset.usda"
    path.write_text("""\
#usda 1.0
(
    defaultPrim = "World"
)

def Xform "World" (
    customData = {
        string asset_name = "tree"
        string version = "v001"
    }
)
{
}
""")
    validator = MetadataValidator(config)
    fixes = validator.fix(path, asset_name="tree", version="v001")
    assert fixes == []


# --- publisher integration ---

def test_publish_result_has_fixes_field():
    from houdini_usd_publisher.core.publisher import PublishResult
    result = PublishResult(success=True, asset_name="tree", version="v001")
    assert result.fixes == []


def test_summary_shows_fixed():
    from houdini_usd_publisher.core.publisher import PublishResult
    result = PublishResult(
        success=True,
        asset_name="tree",
        version="v001",
        fixes=["defaultPrim set to 'World'"]
    )
    assert "FIXED" in result.summary()


# --- KindValidator.fix() ---

@pytest.fixture
def usda_no_kind(tmp_path) -> Path:
    path = tmp_path / "asset.usda"
    path.write_text("""\
#usda 1.0
(
    defaultPrim = "World"
)

def Xform "World"
{
}
""")
    return path


@pytest.fixture
def usda_wrong_kind(tmp_path) -> Path:
    path = tmp_path / "asset.usda"
    path.write_text("""\
#usda 1.0
(
    defaultPrim = "World"
)

def Xform "World" (
    kind = "group"
)
{
}
""")
    return path


def test_fix_kind_sets_component_when_missing(usda_no_kind):
    from houdini_usd_publisher.validation.kind import KindValidator
    validator = KindValidator()
    fixes = validator.fix(usda_no_kind)
    assert len(fixes) == 1
    assert "component" in fixes[0]


def test_fix_kind_writes_to_file(usda_no_kind):
    from houdini_usd_publisher.validation.kind import KindValidator
    from pxr.Usd import ModelAPI
    validator = KindValidator()
    validator.fix(usda_no_kind)
    stage = Usd.Stage.Open(str(usda_no_kind))
    kind = ModelAPI(stage.GetDefaultPrim()).GetKind()
    assert kind == "component"


def test_fix_kind_does_not_fix_wrong_kind(usda_wrong_kind):
    from houdini_usd_publisher.validation.kind import KindValidator
    validator = KindValidator()
    fixes = validator.fix(usda_wrong_kind)
    assert fixes == []


# --- UpAxisValidator.fix() ---

@pytest.fixture
def usda_z_up(tmp_path) -> Path:
    path = tmp_path / "asset.usda"
    path.write_text("""\
#usda 1.0
(
    defaultPrim = "World"
    upAxis = "Z"
)

def Xform "World" {}
""")
    return path


@pytest.fixture
def usda_y_up(tmp_path) -> Path:
    path = tmp_path / "asset.usda"
    path.write_text("""\
#usda 1.0
(
    defaultPrim = "World"
    upAxis = "Y"
)

def Xform "World" {}
""")
    return path


def test_fix_up_axis_corrects_z_to_y(usda_z_up, fresh_config):
    from houdini_usd_publisher.validation.up_axis import UpAxisValidator
    from houdini_usd_publisher.core.config import PublishConfig
    validator = UpAxisValidator(PublishConfig(fresh_config))
    fixes = validator.fix(usda_z_up)
    assert len(fixes) == 1
    assert "Z" in fixes[0]
    assert "Y" in fixes[0]


def test_fix_up_axis_writes_to_file(usda_z_up, fresh_config):
    from houdini_usd_publisher.validation.up_axis import UpAxisValidator
    from houdini_usd_publisher.core.config import PublishConfig
    validator = UpAxisValidator(PublishConfig(fresh_config))
    validator.fix(usda_z_up)
    stage = Usd.Stage.Open(str(usda_z_up))
    assert UsdGeom.GetStageUpAxis(stage) == "Y"


def test_fix_up_axis_no_fix_needed(usda_y_up, fresh_config):
    from houdini_usd_publisher.validation.up_axis import UpAxisValidator
    from houdini_usd_publisher.core.config import PublishConfig
    validator = UpAxisValidator(PublishConfig(fresh_config))
    fixes = validator.fix(usda_y_up)
    assert fixes == []
