from pathlib import Path
from pxr import Usd, UsdGeom
from houdini_usd_publisher.validation.base import BaseValidator
from houdini_usd_publisher.core.config import PublishConfig


class UpAxisValidator(BaseValidator):
    """
    Validates that the USD stage uses the expected up-axis convention.

    Ensures consistent scene orientation across assets (e.g. Y-up or Z-up)
    to prevent transform and import issues in downstream applications.
    """

    def __init__(self, config: PublishConfig):
        validator_cfg = config.get_validator_config("UpAxisValidator")
        self.expected_axis = validator_cfg.get("expected_axis", "Y")

    def validate(self, usd_file: Path) -> tuple[list[str], list[str]]:
        errors = []
        warnings = []

        stage = Usd.Stage.Open(str(usd_file))
        if not stage:
            errors.append("Could not open USD stage")
            return errors, warnings

        up_axis = UsdGeom.GetStageUpAxis(stage)

        if up_axis != self.expected_axis:
            errors.append(
                f"Stage upAxis is '{up_axis}' — "
                f"expected '{self.expected_axis}'"
            )

        return errors, warnings

    def fix(self, usd_file: Path, **kwargs) -> list[str]:
        """
        Auto-fix: set upAxis to the expected axis if it doesn't match.
        """
        fixes = []

        stage = Usd.Stage.Open(str(usd_file))
        if not stage:
            return fixes

        current_axis = UsdGeom.GetStageUpAxis(stage)
        if current_axis == self.expected_axis:
            return fixes

        UsdGeom.SetStageUpAxis(stage, self.expected_axis)
        stage.GetRootLayer().Save()
        fixes.append(
            f"upAxis changed from '{current_axis}' to '{self.expected_axis}'"
        )

        return fixes
