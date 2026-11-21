import os
import uuid
from abc import ABC, abstractmethod
from pathlib import Path


class StorageProvider(ABC):
    """
    Abstract storage provider interface.
    Allows easy swapping between local disk storage and cloud storage (e.g., S3).
    """

    @abstractmethod
    def save_file(self, content: bytes, filename: str, subfolder: str = "") -> str:
        """Saves file bytes and returns accessible URL or path."""
        pass

    @abstractmethod
    def get_file_path(self, relative_path: str) -> str:
        """Returns the local or absolute path to the file."""
        pass

    @abstractmethod
    def delete_file(self, relative_path: str) -> bool:
        """Deletes a file given its relative path."""
        pass


class LocalStorageProvider(StorageProvider):
    def __init__(self, base_dir: str = None):
        if base_dir is None:
            # Point to backend/uploads
            base_path = Path(__file__).resolve().parent.parent.parent / "uploads"
        else:
            base_path = Path(base_dir)
        self.base_dir = base_path
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_file(self, content: bytes, filename: str, subfolder: str = "") -> str:
        target_dir = self.base_dir / subfolder if subfolder else self.base_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        ext = Path(filename).suffix or ".wav"
        unique_name = f"{uuid.uuid4().hex}{ext}"
        target_file = target_dir / unique_name

        with open(target_file, "wb") as f:
            f.write(content)

        relative = f"/uploads/{subfolder}/{unique_name}" if subfolder else f"/uploads/{unique_name}"
        return relative.replace("//", "/")

    def get_file_path(self, relative_path: str) -> str:
        clean_path = relative_path.lstrip("/").replace("uploads/", "", 1)
        return str(self.base_dir / clean_path)

    def delete_file(self, relative_path: str) -> bool:
        try:
            clean_path = relative_path.lstrip("/").replace("uploads/", "", 1)
            target = self.base_dir / clean_path
            if target.exists():
                target.unlink()
                return True
        except Exception:
            pass
        return False


_storage_provider: StorageProvider = LocalStorageProvider()


def get_storage_provider() -> StorageProvider:
    return _storage_provider
