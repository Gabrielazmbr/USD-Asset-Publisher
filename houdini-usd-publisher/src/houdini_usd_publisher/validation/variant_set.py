from pathlib import Path

from pxr import Usd

from houdini_usd_publisher.core.config import PublishConfig
from houdini_usd_publisher.validation.base import BaseValidator


class VariantSetValidator(BaseValidator):
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
            errors.append("No defaultPrim set — cannot check variant sets")
            return errors, warnings

        # Check required variant sets exist
        existing_sets = root_prim.GetVariantSets().GetNames()
        for required_set in self.config.required_variant_sets:
            if required_set not in existing_sets:
                errors.append(f"Missing required variant set: '{required_set}'")
                continue

            # Check required values exist inside the variant set
            variant_set = root_prim.GetVariantSets().GetVariantSet(required_set)
            existing_values = variant_set.GetVariantNames()
            for required_value in self.config.required_lod_variants:
                if required_value not in existing_values:
                    errors.append(
                        f"Variant set '{required_set}' "
                        f"missing required variant: '{required_value}'"
                    )

        return errors, warnings
