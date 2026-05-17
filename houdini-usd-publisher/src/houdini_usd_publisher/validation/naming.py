import re
from pathlib import Path
from pxr import Usd
from houdini_usd_publisher.validation.base import BaseValidator
from houdini_usd_publisher.core.config import PublishConfig

# Pre-compiled patterns
CAMEL_CASE_RE = re.compile(r'^[A-Z][a-zA-Z0-9]*(_[0-9]+)?$')
SNAKE_CASE_RE = re.compile(r'^[a-z][a-z0-9]*(_[a-z0-9]+)*(_[0-9]+)?$')
VALID_CHARS_RE = re.compile(r'^[a-zA-Z0-9_]+$')
STARTS_WITH_LETTER_RE = re.compile(r'^[a-zA-Z_]')


class NamingConventionValidator(BaseValidator):
    """
    Validates prim names follow the configured naming convention.

    Configurable rules:
    - allow_spaces: whether spaces are permitted in prim names
    - allow_special_chars: whether special characters are permitted
    - must_start_with_letter: whether names must start with a letter
    - naming_style: 'CamelCase', 'snake_case', or 'any'
    - instance_suffix_pattern: regex for instance numbering e.g. '_[0-9]+'
    """

    def __init__(self, config: PublishConfig):
        cfg = config.get_validator_config("NamingConventionValidator")
        self.allow_spaces = cfg.get("allow_spaces", False)
        self.allow_special_chars = cfg.get("allow_special_chars", False)
        self.must_start_with_letter = cfg.get("must_start_with_letter", True)
        self.naming_style = cfg.get("naming_style", "any")
        self.instance_suffix_pattern = cfg.get("instance_suffix_pattern", None)

        # Compile instance suffix pattern if provided
        self._instance_re = (
            re.compile(self.instance_suffix_pattern)
            if self.instance_suffix_pattern
            else None
        )

    def validate(self, usd_file: Path) -> tuple[list[str], list[str]]:
        errors = []
        warnings = []

        stage = Usd.Stage.Open(str(usd_file))
        if not stage:
            errors.append("Could not open USD stage")
            return errors, warnings

        for prim in stage.Traverse():
            name = prim.GetName()
            prim_errors = self._check_name(name, prim.GetPath())
            errors.extend(prim_errors)

        return errors, warnings

    def _check_name(self, name: str, path) -> list[str]:
        issues = []

        # Special characters — USD allows some we may not want
        if not self.allow_special_chars and not VALID_CHARS_RE.match(name):
            issues.append(
                f"Prim '{path}' contains special characters in name '{name}'"
            )
            return issues

        # Naming style
        if self.naming_style == "CamelCase":
            if not CAMEL_CASE_RE.match(name):
                issues.append(
                    f"Prim '{path}' name '{name}' does not follow CamelCase convention"
                )
        elif self.naming_style == "snake_case":
            if not SNAKE_CASE_RE.match(name):
                issues.append(
                    f"Prim '{path}' name '{name}' does not follow snake_case convention"
                )

        return issues
