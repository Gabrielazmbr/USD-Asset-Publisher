import shutil
from pathlib import Path

from houdini_usd_publisher.core.config import PublishConfig


class PackageError(Exception):
    pass


class USDPackager:
    """
    Works as a file system organicer. Validates an input file and creates an asset directory to store main files and subfiles.
    """

    def __init__(self, config: PublishConfig):
        self.config = config

    def package(
        self,
        exported_file: Path,
        asset_name: str,
        version: str,
        publish_root: str | Path,
    ) -> Path:
        # Validates input file
        if not exported_file.exists():
            raise PackageError(f"Exported file not found: {exported_file}")

        # Creates asset directory
        asset_dir = Path(publish_root) / asset_name / version
        asset_dir.mkdir(parents=True, exist_ok=True)

        destination = asset_dir / "asset.usda"
        # Copies exported file to destination
        try:
            shutil.copy2(exported_file, destination)
        except OSError as e:
            raise PackageError(f"Failed to copy to publish location: {e}") from e

        # Writes stub files
        self._write_stub(asset_dir / "payload.usda", "Geometry — populated later")
        self._write_stub(asset_dir / "materials.usda", "Shading — populated later")

        return destination

    def _write_stub(self, path: Path, comment: str) -> None:
        if path.exists():
            return
        path.write_text(f"#usda 1.0\n# {comment}\n")

    def publish_path(
        self, publish_root: str | Path, asset_name: str, version: str
    ) -> Path:
        return Path(publish_root) / asset_name / version / "asset.usda"
