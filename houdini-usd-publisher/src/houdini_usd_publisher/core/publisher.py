from dataclasses import dataclass, field
from pathlib import Path

from houdini_usd_publisher.core.config import PublishConfig
from houdini_usd_publisher.core.exporter import ExportError, USDExporter
from houdini_usd_publisher.core.packager import PackageError, USDPackager
from houdini_usd_publisher.validation.default_prim import DefaultPrimValidator
from houdini_usd_publisher.validation.metadata import MetadataValidator
from houdini_usd_publisher.validation.variant_set import VariantSetValidator


@dataclass
class PublishResult:
    """
    Represents the result of a publish operation.
    """

    success: bool
    asset_name: str
    version: str
    published_path: Path | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"{'OK' if self.success else 'FAILED'} — {self.asset_name} {self.version}"
        ]
        for e in self.errors:
            lines.append(f"  ERROR   {e}")
        for w in self.warnings:
            lines.append(f"  WARNING {w}")
        if self.published_path:
            lines.append(f"  -> {self.published_path}")
        return "\n".join(lines)


class Publisher:
    """
    Manages the publishing process for USD assets.
    """

    def __init__(self, config: PublishConfig, publish_root: str | Path):
        self.config = config
        self.publish_root = Path(publish_root)
        self.exporter = USDExporter(config)
        self.packager = USDPackager(config)
        self._validators: list = []
        self._validators = [
            DefaultPrimValidator(),
            MetadataValidator(config),
            VariantSetValidator(config),
        ]

    def add_validator(self, validator) -> None:
        self._validators.append(validator)

    def publish(
        self,
        lop_node_path: str,
        asset_name: str,
        version: str,
        tmp_dir: str | Path,
        dry_run: bool = False,
    ) -> PublishResult:
        result = PublishResult(success=False, asset_name=asset_name, version=version)

        # 1. Export
        tmp_export = Path(tmp_dir) / f"{asset_name}_{version}_tmp.usda"
        try:
            exported = self.exporter.export(lop_node_path, tmp_export)
        except ExportError as e:
            result.errors.append(f"Export: {e}")
            return result

        # 2. Validate
        all_errors: list[str] = []
        all_warnings: list[str] = []
        for validator in self._validators:
            errors, warnings = validator.validate(exported)
            all_errors.extend(errors)
            all_warnings.extend(warnings)

        result.warnings = all_warnings
        if all_errors:
            result.errors = all_errors
            return result

        # Intercept dry run - skip packaging
        if dry_run:
            result.success = True
            result.published_path = None
            return result

        # 3. Package
        try:
            published = self.packager.package(
                exported_file=exported,
                asset_name=asset_name,
                version=version,
                publish_root=self.publish_root,
            )
        except PackageError as e:
            result.errors.append(f"Package: {e}")
            return result

        result.success = True
        result.published_path = published
        return result
