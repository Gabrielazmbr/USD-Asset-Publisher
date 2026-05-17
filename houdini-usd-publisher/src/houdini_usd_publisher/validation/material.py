from pathlib import Path
from pxr import Usd, UsdShade
from houdini_usd_publisher.validation.base import BaseValidator


class MaterialValidator(BaseValidator):
    """
    Validates material setup on the asset.

    Checks:
    - At least one Mesh prim exists in the stage
    - At least one Material prim exists in the stage
    - Mesh prims have a computed material binding (direct or inherited)

    These are warnings rather than errors because:
    - Some assets have no geometry (e.g. locators, rigs)
    - Material binding through collection APIs is valid but harder to detect
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
            errors.append("No defaultPrim set — cannot check materials")
            return errors, warnings

        mesh_prims = [
            p for p in stage.Traverse()
            if p.GetTypeName() == "Mesh"
        ]
        material_prims = [
            p for p in stage.Traverse()
            if p.GetTypeName() == "Material"
        ]

        # No geometry at all — warning, not error
        if not mesh_prims:
            warnings.append(
                "No Mesh prims found — asset may be missing geometry"
            )
            return errors, warnings

        # Geometry exists but no materials
        if not material_prims:
            warnings.append(
                f"Found {len(mesh_prims)} Mesh prim(s) but no Material prims — "
                "materials may be in a separate layer or not yet assigned"
            )
            return errors, warnings

        # Check mesh prims have a computed binding
        unbound = []
        for prim in mesh_prims:
            mat, _ = UsdShade.MaterialBindingAPI(prim).ComputeBoundMaterial()
            if not mat:
                unbound.append(str(prim.GetPath()))

        if unbound:
            warnings.append(
                f"{len(unbound)} Mesh prim(s) have no material binding: "
                f"{', '.join(unbound[:3])}"
                f"{'...' if len(unbound) > 3 else ''}"
            )

        return errors, warnings
