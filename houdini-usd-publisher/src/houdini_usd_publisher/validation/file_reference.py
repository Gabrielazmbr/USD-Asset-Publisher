from pathlib import Path
from pxr import UsdUtils
from houdini_usd_publisher.validation.base import BaseValidator


class FileReferenceValidator(BaseValidator):
    """
    It checks unresolved paths and missing files to ensure the stage has
    no broken references before publishing.
    """

    def validate(self, usd_file: Path) -> tuple[list[str], list[str]]:
        errors = []
        warnings = []

        all_layers, all_assets, unresolved = (
            UsdUtils.ComputeAllDependencies(str(usd_file))
        )

        for path in unresolved:

            clean_path = (
                path.split(":SDF_FORMAT_ARGS:")[0]
                .strip()
            )

            print(repr(clean_path))
            print(Path(clean_path).exists())

            if not Path(clean_path).exists():
                errors.append(
                    f"Unresolved reference: '{clean_path}'"
                )

        for layer in all_layers:
            identifier = (
                layer.identifier
                .split(":SDF_FORMAT_ARGS:")[0]
                .strip()
            )

            if not identifier:
                continue

            if Path(identifier).resolve() == usd_file.resolve():
                continue

            if not Path(identifier).exists():
                errors.append(
                    f"Missing referenced layer: '{identifier}'"
                )

        for asset_path in all_assets:
            identifier = (
                asset_path
                .split(":SDF_FORMAT_ARGS:")[0]
                .strip()
            )

            if not identifier:
                continue

            if not Path(identifier).exists():
                errors.append(
                    f"Missing referenced asset: '{identifier}'"
                )

        return errors, warnings
