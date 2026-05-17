from pathlib import Path
from pxr import Usd, UsdUtils
from houdini_usd_publisher.validation.base import BaseValidator


class FileReferenceValidator(BaseValidator):
    """
    Validates that all external file references in the USD stage
    exist on disk. Uses UsdUtils.ComputeAllDependencies to find
    all layers and assets referenced by the stage.

    Missing references are errors — they will cause silent failures
    downstream when the asset is consumed by other tools.
    Unresolved paths (paths USD couldn't resolve at all) are also errors.
    """

    def validate(self, usd_file: Path) -> tuple[list[str], list[str]]:
        errors = []
        warnings = []

        all_layers, all_assets, unresolved = UsdUtils.ComputeAllDependencies(
            str(usd_file)
        )

        # Unresolved paths — USD couldn't resolve them at all
        for path in unresolved:
            errors.append(f"Unresolved reference: '{path}'")

        # Check all referenced layers exist on disk
        for layer in all_layers:
            layer_path = layer.realPath
            if not layer_path:
                continue
            if not Path(layer_path).exists():
                errors.append(f"Missing referenced layer: '{layer_path}'")

        # Check all referenced assets exist on disk
        for asset_path in all_assets:
            if not Path(asset_path).exists():
                errors.append(f"Missing referenced asset: '{asset_path}'")

        return errors, warnings
