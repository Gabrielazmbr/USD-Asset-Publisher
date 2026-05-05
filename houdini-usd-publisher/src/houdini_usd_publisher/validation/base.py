from abc import ABC, abstractmethod
from pathlib import Path


class BaseValidator(ABC):
    @abstractmethod
    def validate(self, usd_file: Path) -> tuple[list[str], list[str]]:
        """
        Validate a USD file on disk.

        Returns:
            A tuple of (errors, warnings).
            Errors block publishing. Warnings allow it with feedback.
        """
        ...
