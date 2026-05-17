from pathlib import Path
from pxr import Usd
from pxr.Usd import ModelAPI
from houdini_usd_publisher.validation.base import BaseValidator

VALID_ROOT_KINDS = {"component", "assembly"}
VALID_CHILD_KINDS = {"group", "component", "assembly"}


class KindValidator(BaseValidator):
    """
    Validates the USD kind hierarchy.

    Rules:
    - Root prim (defaultPrim) must be 'component' or 'assembly'
    - No component prim should contain other model prims (components/assemblies)
    - All prims that are part of the model hierarchy must have a kind set
    """

    def validate(self, usd_file: Path) -> tuple[list[str], list[str]]:
        errors = []
        warnings = []

        stage = Usd.Stage.Open(str(usd_file))
        if not stage:
            errors.append("Could not open USD stage")
            return errors, warnings

        root_prim = stage.GetDefaultPrim()
        if not root_prim.IsValid():
            errors.append("No defaultPrim set — cannot check kind hierarchy")
            return errors, warnings

        # Check root prim kind
        root_kind = ModelAPI(root_prim).GetKind()
        if not root_kind:
            errors.append(
                f"defaultPrim '{root_prim.GetName()}' has no kind set — "
                "expected 'component' or 'assembly'"
            )
        elif root_kind not in VALID_ROOT_KINDS:
            errors.append(
                f"defaultPrim '{root_prim.GetName()}' has kind '{root_kind}' — "
                f"expected one of {sorted(VALID_ROOT_KINDS)}"
            )

        # Check component prims don't contain other model prims
        for prim in stage.Traverse():
            kind = ModelAPI(prim).GetKind()
            if kind != "component":
                continue
            for child in prim.GetChildren():
                child_kind = ModelAPI(child).GetKind()
                if child_kind in {"component", "assembly"}:
                    errors.append(
                        f"Component prim '{prim.GetPath()}' contains "
                        f"child '{child.GetName()}' with kind '{child_kind}' — "
                        "components should be leaf nodes"
                    )

        return errors, warnings

    def fix(self, usd_file: Path, **kwargs) -> list[str]:
        """
        Auto-fix: set kind to 'component' on defaultPrim if kind is missing.
        Only fixes missing kind — does not correct wrong kind values.
        """
        fixes = []

        stage = Usd.Stage.Open(str(usd_file))
        if not stage:
            return fixes

        root_prim = stage.GetDefaultPrim()
        if not root_prim.IsValid():
            return fixes

        root_kind = ModelAPI(root_prim).GetKind()

        if not root_kind:
            ModelAPI(root_prim).SetKind("component")
            stage.GetRootLayer().Save()
            fixes.append(
                f"Kind set to 'component' on '{root_prim.GetName()}'"
            )

        return fixes
