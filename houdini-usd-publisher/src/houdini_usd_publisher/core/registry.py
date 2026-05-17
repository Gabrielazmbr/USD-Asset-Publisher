import os
import getpass
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file if USD_PUBLISHER_ROOT is set
_project_root = os.environ.get("USD_PUBLISHER_ROOT")
if _project_root:
    load_dotenv(dotenv_path=Path(_project_root) / ".env")
else:
    load_dotenv()  # fallback — tries cwd


class RegistryError(Exception):
    pass


class PublishRegistry:
    """
    Records publish events to MongoDB.
    Connection failures never block a publish, they are caught and reported
    as warnings so the pipeline continues even if the database is unavailable.
    """

    def __init__(self):
        self._client = None
        self._collection = None
        self._connect()

    def _connect(self):
        try:
            import certifi
            from pymongo import MongoClient

            uri = os.environ.get("MONGODB_URI")
            db_name = os.environ.get("MONGODB_DATABASE", "usd_publisher")

            if not uri:
                raise RegistryError("MONGODB_URI not set in environment")

            self._client = MongoClient(
                uri,
                serverSelectionTimeoutMS=3000,
                tlsCAFile=certifi.where()
            )
            db = self._client[db_name]
            self._collection = db["publishes"]

        except Exception as e:
            self._client = None
            self._collection = None
            print(f"Registry warning: could not connect to MongoDB: {e}")

    @property
    def is_connected(self) -> bool:
        return self._collection is not None

    def record(
        self,
        asset_name: str,
        version: str,
        published_path: Path | None,
        validators_run: list[str],
        warnings: list[str],
        dry_run: bool = False,
    ) -> bool:
        """
        Writes a publish record to MongoDB.

        Returns True if the record was written, False if it failed silently.
        Never raises — registry failures must not block publishing.
        """
        if not self.is_connected:
            return False

        document = {
            "asset_name": asset_name,
            "version": version,
            "published_at": datetime.now(timezone.utc),
            "published_by": getpass.getuser(),
            "published_path": str(published_path) if published_path else None,
            "validators_run": validators_run,
            "warnings": warnings,
            "dry_run": dry_run,
            "success": True,
        }

        try:
            self._collection.insert_one(document)
            return True
        except Exception as e:
            print(f"Registry warning: could not write record: {e}")
            return False

    def get_versions(self, asset_name: str) -> list[dict]:
        """
        Return all published versions of an asset, newest first.
        Returns empty list if registry is unavailable.
        """
        if not self.is_connected:
            return []
        try:
            cursor = self._collection.find(
                {"asset_name": asset_name, "dry_run": False},
                {"_id": 0}
            ).sort("published_at", -1)
            return list(cursor)
        except Exception:
            return []

    def get_latest_version(self, asset_name: str) -> dict | None:
        """
        Return the most recent successful publish record for an asset.
        Returns None if not found or registry unavailable.
        """
        versions = self.get_versions(asset_name)
        return versions[0] if versions else None

    def get_recent(self, limit: int = 20) -> list[dict]:
        """Return the most recent publishes across all assets."""
        if not self.is_connected:
            return []
        try:
            cursor = self._collection.find(
                {"dry_run": False},
                {"_id": 0}
            ).sort("published_at", -1).limit(limit)
            return list(cursor)
        except Exception:
            return []

    def close(self):
        if self._client:
            self._client.close()
