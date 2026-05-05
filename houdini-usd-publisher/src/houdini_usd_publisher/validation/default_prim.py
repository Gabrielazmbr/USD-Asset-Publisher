from pathlib import Path

from pxr import Usd

from houdini_usd_publisher.validation.base import BaseValidator


class DefaultPrimValidator(BaseValidator):
    def validate(self, usd_file: Path) -> tuple[list[str], list[str]]:
        errors = []
        warnings = []

        stage = Usd.Stage.Open(str(usd_file))
        if not stage:
            errors.append("Could not open USD stage")
            return errors, warnings

        default_prim = stage.GetDefaultPrim()
        if not default_prim.IsValid():
            errors.append(
                "Stage has no defaultPrim set — "
                "references to this asset will be ambiguous"
            )

        return errors, warnings
