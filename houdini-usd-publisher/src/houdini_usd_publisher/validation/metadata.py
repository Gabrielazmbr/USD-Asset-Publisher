from pathlib import Path
from pxr import Usd
from houdini_usd_publisher.validation.base import BaseValidator
from houdini_usd_publisher.core.config import PublishConfig


class MetadataValidator(BaseValidator):
    """
    Validates required custom metadata on the USD root prim.

    Ensures that key production fields (e.g. asset name, version)
    are present, and can optionally auto-fill missing values.
    """

    def __init__(self, config: PublishConfig):
        self.config = config
        validator_cfg = config.get_validator_config("MetadataValidator")
        self.required_fields = validator_cfg.get("required_fields", [])

    def validate(self, usd_file: Path) -> tuple[list[str], list[str]]:
        errors = []
        warnings = []

        stage = Usd.Stage.Open(str(usd_file))
        if not stage:
            errors.append("Could not open USD stage")
            return errors, warnings

        root_prim = stage.GetDefaultPrim()
        if not root_prim.IsValid():
            errors.append("No defaultPrim set — cannot check metadata")
            return errors, warnings

        for field in self.required_fields:
            if not root_prim.HasCustomDataKey(field):
                errors.append(f"Missing required metadata field: '{field}'")

        return errors, warnings

    def fix(self, usd_file: Path, asset_name: str = "", version: str = "", **kwargs) -> list[str]:
        fixes = []

        stage = Usd.Stage.Open(str(usd_file))
        if not stage:
            return fixes

        root_prim = stage.GetDefaultPrim()
        if not root_prim.IsValid():
            return fixes

        auto_values = {
            "asset_name": asset_name,
            "version": version,
        }

        for field in self.required_fields:
            if not root_prim.HasCustomDataKey(field):
                value = auto_values.get(field)
                if value:
                    root_prim.SetCustomDataByKey(field, value)
                    fixes.append(f"Metadata field '{field}' set to '{value}'")

        if fixes:
            stage.GetRootLayer().Save()

        return fixes
