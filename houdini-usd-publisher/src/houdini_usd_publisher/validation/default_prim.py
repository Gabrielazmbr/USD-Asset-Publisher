from pathlib import Path
from pxr import Usd
from houdini_usd_publisher.validation.base import BaseValidator


class DefaultPrimValidator(BaseValidator):
    """
    Ensures the USD stage has a valid defaultPrim.

    The defaultPrim defines the root entry point of an asset for references.
    If missing, the validator can assign the first root prim as a fallback.
    """

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

    def fix(self, usd_file: Path, **kwargs) -> list[str]:
        """
        Auto-fix: set defaultPrim to the first root-level prim if missing.
        Returns a list of fix descriptions applied.
        """
        fixes = []

        stage = Usd.Stage.Open(str(usd_file))
        if not stage:
            return fixes

        # Already set — nothing to fix
        if stage.GetDefaultPrim().IsValid():
            return fixes

        # Find first root-level prim
        root_prims = stage.GetPseudoRoot().GetChildren()
        if not root_prims:
            return fixes

        first_prim = root_prims[0]
        stage.SetDefaultPrim(first_prim)
        stage.GetRootLayer().Save()

        fixes.append(
            f"defaultPrim set to '{first_prim.GetName()}'"
        )
        return fixes
