import getpass
import json
from datetime import datetime, timezone
from pathlib import Path


class PublishReport:
    """
    Writes a publish_report.json alongside the published asset.
    Always written locally, independent of MongoDB availability.
    """

    def write(
        self,
        asset_dir: Path,
        asset_name: str,
        version: str,
        published_path: Path | None,
        validators_run: list[str],
        warnings: list[str],
        fixes: list[str],
        registry_recorded: bool,
        success: bool,
    ) -> Path:
        """
        Write publish_report.json to asset_dir.
        Returns the path to the written report.
        """
        report = {
            "asset_name": asset_name,
            "version": version,
            "published_at": datetime.now(timezone.utc).isoformat(),
            "published_by": getpass.getuser(),
            "published_path": str(published_path) if published_path else None,
            "validators_run": validators_run,
            "warnings": warnings,
            "fixes": fixes,
            "registry_recorded": registry_recorded,
            "success": success,
        }

        report_path = asset_dir / "publish_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        return report_path

    def write_for_file(
        self,
        usd_file: Path,
        validators_run: list[str],
        warnings: list[str],
        fixes: list[str],
        errors: list[str],
    ) -> Path:
        """
        Write a validation_report.json next to a validated external file.
        Used by the Validate File tab.
        """
        report = {
            "validated_file": str(usd_file),
            "validated_at": datetime.now(timezone.utc).isoformat(),
            "validated_by": getpass.getuser(),
            "validators_run": validators_run,
            "errors": errors,
            "warnings": warnings,
            "fixes": fixes,
            "success": len(errors) == 0,
        }

        report_path = usd_file.parent / "validation_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        return report_path
