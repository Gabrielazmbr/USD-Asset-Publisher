import json
from pathlib import Path


class ConfigError(Exception):
    pass


class PublishConfig:

    def __init__(self, config_path: str | Path):
        self._path = Path(config_path)
        self._data = self._load()

    def _load(self) -> dict:
        if not self._path.exists():
            raise ConfigError(f"Config file not found: {self._path}")
        try:
            with open(self._path) as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigError(f"Invalid JSON in config: {e}") from e

    @property
    def export_format(self) -> str:
        return self._data.get("export_format", "usda")

    @property
    def assets_root(self) -> str:
        return self._data.get("assets_root", "assets")

    @property
    def enabled_validators(self) -> list[str]:
        """Return names of all enabled validators in config order."""
        return [
            name
            for name, cfg in self._data.get("validators", {}).items()
            if cfg.get("enabled", True)
        ]


    def is_auto_fix_enabled(self, name: str) -> bool:
        """Return whether auto_fix is enabled for a specific validator."""
        return self.get_validator_config(name).get("auto_fix", False)


    def is_validator_enabled(self, name: str) -> bool:
        validators = self._data.get("validators", {})
        if name not in validators:
            return False
        return validators[name].get("enabled", True)

    def get_validator_config(self, name: str) -> dict:
        """Return the config dict for a specific validator."""
        return self._data.get("validators", {}).get(name, {})

    def raw(self) -> dict:
        return self._data
