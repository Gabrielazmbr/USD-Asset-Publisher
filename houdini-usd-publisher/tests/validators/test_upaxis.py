from pathlib import Path
import pytest
from houdini_usd_publisher.core.config import PublishConfig
from houdini_usd_publisher.validation.up_axis import UpAxisValidator

@pytest.fixture
def validator(fresh_config):
    return UpAxisValidator(PublishConfig(fresh_config))


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
def usda_no_up_axis(tmp_path) -> Path:
    path = tmp_path / "asset.usda"
    path.write_text("""\
#usda 1.0
(
    defaultPrim = "World"
)

def Xform "World" {}
""")
    return path


def test_y_up_produces_no_errors(validator, usda_y_up):
    errors, warnings = validator.validate(usda_y_up)
    assert errors == []


def test_y_up_produces_no_warnings(validator, usda_y_up):
    errors, warnings = validator.validate(usda_y_up)
    assert warnings == []


def test_z_up_produces_error(validator, usda_z_up):
    errors, warnings = validator.validate(usda_z_up)
    assert len(errors) == 1
    assert "upAxis" in errors[0]
    assert "Z" in errors[0]

def test_no_up_axis_set_passes(validator, usda_no_up_axis):
    errors, warnings = validator.validate(usda_no_up_axis)
    assert errors == []
    assert warnings == []
