from pathlib import Path

from pxr import Sdf, Usd

from houdini_usd_publisher.core.config import PublishConfig
from houdini_usd_publisher.validation.base import BaseValidator


class MetadataValidator(BaseValidator):
    def __init__(self, config: PublishConfig):
        self.config = config

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

        for field in self.config.required_metadata_fields:
            if not root_prim.HasCustomDataKey(field):
                errors.append(f"Missing required metadata field: '{field}'")

        return errors, warnings
