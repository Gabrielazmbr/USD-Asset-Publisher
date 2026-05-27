import re
from pathlib import Path
from pxr import Usd
from houdini_usd_publisher.validation.base import BaseValidator
from houdini_usd_publisher.core.config import PublishConfig

CAMEL_CASE_RE = re.compile(r'^[A-Z][a-zA-Z0-9]*$')
SNAKE_CASE_RE = re.compile(r'^[a-z][a-z0-9]*(_[a-z0-9]+)*$')


class NamingConventionValidator(BaseValidator):
    """
    Validates prim names in the root layer only (skips referenced/instanced content).

    Errors (block publish):
    - Prim name matches a reserved word

    Warnings (allow with feedback):
    - Naming style violation (CamelCase or snake_case)
    - Leading underscore
    - Trailing underscore
    - Double underscore
    """

    def __init__(self, config: PublishConfig):
        cfg = config.get_validator_config("NamingConventionValidator")
        self.naming_style = cfg.get("naming_style", "any")
        self.allow_leading_underscore = cfg.get("allow_leading_underscore", False)
        self.allow_trailing_underscore = cfg.get("allow_trailing_underscore", False)
        self.allow_double_underscore = cfg.get("allow_double_underscore", False)
        self.reserved_names = cfg.get("reserved_names", ["default", "root"])

    def validate(self, usd_file: Path) -> tuple[list[str], list[str]]:
        errors = []
        warnings = []

        stage = Usd.Stage.Open(str(usd_file))
        if not stage:
            errors.append("Could not open USD stage")
            return errors, warnings

        root_layer = stage.GetRootLayer()

        for prim in stage.Traverse():
            # Skip prims that didn't originate in the root layer
            if not prim.GetPrimStack():
                continue
            if prim.GetPrimStack()[0].layer.identifier != root_layer.identifier:
                continue
            # Skip instance prototypes
            if prim.IsInPrototype():
                continue

            name = prim.GetName()
            prim_errors, prim_warnings = self._check_name(name, prim.GetPath())
            errors.extend(prim_errors)
            warnings.extend(prim_warnings)

        return errors, warnings

    def _check_name(self, name: str, path) -> tuple[list[str], list[str]]:
        errors = []
        warnings = []

        # Errors

        if name.lower() in [r.lower() for r in self.reserved_names]:
            errors.append(
                f"Prim '{path}' uses reserved name '{name}'"
            )

        # Warnings

        if not self.allow_leading_underscore and name.startswith("_"):
            warnings.append(
                f"Prim '{path}' name '{name}' starts with an underscore"
            )

        if not self.allow_trailing_underscore and name.endswith("_"):
            warnings.append(
                f"Prim '{path}' name '{name}' ends with an underscore"
            )

        if not self.allow_double_underscore and "__" in name:
            warnings.append(
                f"Prim '{path}' name '{name}' contains double underscore"
            )

        if self.naming_style == "CamelCase" and not CAMEL_CASE_RE.match(name):
            warnings.append(
                f"Prim '{path}' name '{name}' does not follow CamelCase convention"
            )
        elif self.naming_style == "snake_case" and not SNAKE_CASE_RE.match(name):
            warnings.append(
                f"Prim '{path}' name '{name}' does not follow snake_case convention"
            )

        return errors, warnings
