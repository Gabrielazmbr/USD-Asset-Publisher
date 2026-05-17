from dataclasses import dataclass, field
from pathlib import Path

from houdini_usd_publisher.core.config import PublishConfig
from houdini_usd_publisher.core.exporter import ExportError, USDExporter
from houdini_usd_publisher.core.packager import PackageError, USDPackager
from houdini_usd_publisher.validation.default_prim import DefaultPrimValidator
from houdini_usd_publisher.validation.metadata import MetadataValidator
from houdini_usd_publisher.validation.variant_set import VariantSetValidator
from houdini_usd_publisher.validation.kind import KindValidator
from houdini_usd_publisher.validation.material import MaterialValidator
from houdini_usd_publisher.validation.up_axis import UpAxisValidator
from houdini_usd_publisher.validation.file_reference import FileReferenceValidator
from houdini_usd_publisher.validation.naming import NamingConventionValidator
from houdini_usd_publisher.core.registry import PublishRegistry
from houdini_usd_publisher.core.report import PublishReport


@dataclass
class PublishResult:
    success: bool
    asset_name: str
    version: str
    published_path: Path | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    fixes: list[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = [f"{'OK' if self.success else 'FAILED'} — {self.asset_name} {self.version}"]
        for f in self.fixes:
            lines.append(f"  FIXED   {f}")
        for e in self.errors:
            lines.append(f"  ERROR   {e}")
        for w in self.warnings:
            lines.append(f"  WARNING {w}")
        if self.published_path:
            lines.append(f"  -> {self.published_path}")
        return "\n".join(lines)


# Registry of all available validators
_VALIDATOR_REGISTRY = {
    "DefaultPrimValidator": lambda config: DefaultPrimValidator(),
    "MetadataValidator": lambda config: MetadataValidator(config),
    "VariantSetValidator": lambda config: VariantSetValidator(config),
    "KindValidator": lambda config: KindValidator(),
    "MaterialValidator": lambda config: MaterialValidator(),
    "UpAxisValidator": lambda config: UpAxisValidator(config),
    "FileReferenceValidator": lambda config: FileReferenceValidator(),
    "NamingConventionValidator": lambda config: NamingConventionValidator(config),
}

class Publisher:
    """
    Manages the publishing process for USD assets.
    """

    def __init__(
        self,
        config: PublishConfig,
        publish_root: str | Path,
        use_registry: bool = True,
    ):
        self.config = config
        self.publish_root = Path(publish_root)
        self.exporter = USDExporter(config)
        self.packager = USDPackager(config)
        self.registry = PublishRegistry() if use_registry else None
        self._validators = self._build_validators()
        self.report = PublishReport()

    def _build_validators(self) -> list:
        """Instantiate validators based on config — only enabled ones."""
        validators = []
        for name in self.config.enabled_validators:
            if name in _VALIDATOR_REGISTRY:
                validators.append(_VALIDATOR_REGISTRY[name](self.config))
            else:
                print(f"Warning: unknown validator '{name}' in config — skipping")
        return validators

    def add_validator(self, validator) -> None:
        self._validators.append(validator)

    def publish(
        self,
        lop_node_path: str,
        asset_name: str,
        version: str,
        tmp_dir: str | Path,
        dry_run: bool = False,
        auto_fix: bool = False,
    ) -> PublishResult:
        result = PublishResult(success=False, asset_name=asset_name, version=version)

        # 1. Export
        tmp_export = Path(tmp_dir) / f"{asset_name}_{version}_tmp.usda"
        try:
            exported = self.exporter.export(lop_node_path, tmp_export)
        except ExportError as e:
            result.errors.append(f"Export: {e}")
            return result

        # Auto-fix pass — runs before validation
        if auto_fix:
            for validator in self._validators:
                name = validator.__class__.__name__
                if hasattr(validator, "fix") and self.config.is_auto_fix_enabled(name):
                    fixes = validator.fix(
                        exported,
                        asset_name=asset_name,
                        version=version
                    )
                    result.fixes.extend(fixes)

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

        validator_names = [v.__class__.__name__ for v in self._validators]

        # Record to registry
        registry_recorded = False
        if self.registry:
            registry_recorded = self.registry.record(
                asset_name=asset_name,
                version=version,
                published_path=published,
                validators_run=validator_names,
                warnings=all_warnings,
                dry_run=False,
            )

        # Write local report
        self.report.write(
            asset_dir=published.parent,
            asset_name=asset_name,
            version=version,
            published_path=published,
            validators_run=validator_names,
            warnings=all_warnings,
            fixes=result.fixes,
            registry_recorded=registry_recorded,
            success=True,
        )

        return result
