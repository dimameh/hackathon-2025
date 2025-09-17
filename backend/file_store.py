import os
import json
import uuid
from pathlib import Path
from typing import Optional, Dict, Any


class FileSessionStore:
    """
    File system session store.
    For each session — one file: <base_dir>/<session_id><ext>
    Data inside is a JSON object.
    """

    def __init__(self, base_dir: str = "sessions", ext: str = ".json"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        # If you want the exact name without the extension, pass ext="".
        self.ext = ext

    # --- public API ---

    def create(self, initial: Dict[str, Any], session_id: Optional[str] = None) -> str:
        """
        Creates a session file and writes the initial data.
        If session_id is not passed — generate UUID.
        """
        sid = session_id or str(uuid.uuid4())
        path = self._path(sid)
        if path.exists():
            raise FileExistsError(f"Session '{sid}' already exists")
        self._atomic_write(path, initial)
        return sid

    def get(self, session_id: str) -> Dict[str, Any]:
        """Returns the entire JSON dictionary. Throws FileNotFoundError if the file does not exist."""
        path = self._path(session_id)
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def set(self, session_id: str, data: Dict[str, Any]) -> None:
        """Completely replaces the session content with the passed dictionary."""
        path = self._path(session_id)
        if not path.exists():
            raise FileNotFoundError(f"Session '{session_id}' not found")
        self._atomic_write(path, data)

    def update(self, session_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
        """
        Partial update: shallow-merge (shallow merge) patch -> data.
        Returns the updated data.
        """
        data = self.get(session_id)
        data.update(patch)
        self.set(session_id, data)
        return data

    def exists(self, session_id: str) -> bool:
        return self._path(session_id).exists()

    def delete(self, session_id: str) -> None:
        path = self._path(session_id)
        if path.exists():
            path.unlink()

    # --- internal ---

    def _path(self, session_id: str) -> Path:
        return self.base_dir / f"{session_id}{self.ext}"

    @staticmethod
    def _atomic_write(path: Path, data: Dict[str, Any]) -> None:
        tmp = path.with_suffix(path.suffix + ".tmp") if path.suffix else Path(str(path) + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)