import json
from pathlib import Path


# Define ConfigError
class ConfigError(Exception):
    pass


class PublishConfig:
    """
    Acts as global settings loader. Reads a JSON config file and provides access to settings.
    """

    def __init__(self, config_path: str | Path):
        self._path = Path(config_path)
        self._data = self._load()

    # Load json file
    def _load(self) -> dict:
        # No json file
        if not self._path.exists():
            raise ConfigError(f"Config file not found: {self._path}")
        try:
            with open(self._path) as f:
                return json.load(f)
        # Invalid json
        except json.JSONDecodeError as e:
            raise ConfigError(f"Invalid JSON in config: {e}") from e

    @property
    # export formats - default usda
    def export_format(self) -> str:
        return self._data.get("export_format", "usda")

    @property
    def assets_root(self) -> str:
        return self._data.get("assets_root", "assets")

    @property
    # load variants - low / mid / high
    def required_lod_variants(self) -> list[str]:
        return self._data.get("variants", {}).get("lod", [])

    @property
    # metadata for name and version
    def required_metadata_fields(self) -> list[str]:
        return self._data.get("metadata", {}).get("required_fields", [])

    @property
    # metadata for variant set names.
    def required_variant_sets(self) -> list[str]:
        return list(self._data.get("variants", {}).keys())
