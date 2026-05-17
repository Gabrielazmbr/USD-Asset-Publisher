from pathlib import Path
from pxr import Usd
from houdini_usd_publisher.validation.base import BaseValidator
from houdini_usd_publisher.core.config import PublishConfig


class VariantSetValidator(BaseValidator):

    def __init__(self, config: PublishConfig):
        self.config = config
        validator_cfg = config.get_validator_config("VariantSetValidator")
        self.required_sets = validator_cfg.get("required_sets", {})

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

        existing_sets = root_prim.GetVariantSets().GetNames()

        for required_set, required_values in self.required_sets.items():
            if required_set not in existing_sets:
                errors.append(f"Missing required variant set: '{required_set}'")
                continue

            variant_set = root_prim.GetVariantSets().GetVariantSet(required_set)
            existing_values = variant_set.GetVariantNames()
            for required_value in required_values:
                if required_value not in existing_values:
                    errors.append(
                        f"Variant set '{required_set}' "
                        f"missing required variant: '{required_value}'"
                    )

        return errors, warnings
