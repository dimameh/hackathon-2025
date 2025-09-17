import json
import uuid
import os
from pathlib import Path
from typing import Optional, Dict, Any
from threading import Lock


class FileSessionStore:
    """
    File system session store.
    All sessions are stored in a single file as a map: session_id -> session_data
    """

    def __init__(self, base_dir: str = "sessions", ext: str = ".json"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.store_path = self.base_dir / "sessions_store.json"
        self._lock = Lock()
        
        # Initialize store file if it doesn't exist
        if not self.store_path.exists():
            self._atomic_write({})

    # --- public API ---

    def create(self, initial: Dict[str, Any], session_id: Optional[str] = None) -> str:
        """
        Creates a new session and writes the initial data.
        If session_id is not passed — generate UUID.
        """
        sid = session_id or str(uuid.uuid4())
        with self._lock:
            store = self._read_store()
            if sid in store:
                raise FileExistsError(f"Session '{sid}' already exists")
            store[sid] = initial
            self._atomic_write(store)
        return sid

    def get(self, session_id: str) -> Dict[str, Any]:
        """Returns the session data. Throws KeyError if session does not exist."""
        with self._lock:
            store = self._read_store()
            if session_id not in store:
                raise FileNotFoundError(f"Session '{session_id}' not found")
            return store[session_id]

    def get_by_status(self, status: str) -> Dict[str, Any]:
        """Returns the session data by status."""
        with self._lock:
            store = self._read_store()
            return {sid: sess for sid, sess in store.items() if sess['status'] == status}

    def set(self, session_id: str, data: Dict[str, Any]) -> None:
        """Completely replaces the session content with the passed dictionary."""
        with self._lock:
            store = self._read_store()
            if session_id not in store:
                raise FileNotFoundError(f"Session '{session_id}' not found")
            store[session_id] = data
            self._atomic_write(store)

    def update(self, session_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
        """
        Partial update: shallow-merge patch into existing data.
        Returns the updated data.
        """
        with self._lock:
            store = self._read_store()
            if session_id not in store:
                raise FileNotFoundError(f"Session '{session_id}' not found")
            store[session_id].update(patch)
            self._atomic_write(store)
            return store[session_id]

    def exists(self, session_id: str) -> bool:
        with self._lock:
            store = self._read_store()
            return session_id in store

    def delete(self, session_id: str) -> None:
        with self._lock:
            store = self._read_store()
            if session_id in store:
                del store[session_id]
                self._atomic_write(store)

    # --- internal ---

    def _read_store(self) -> Dict[str, Dict[str, Any]]:
        """Reads the entire store file."""
        try:
            with open(self.store_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def _atomic_write(self, data: Dict[str, Dict[str, Any]]) -> None:
        """Atomically writes the entire store."""
        tmp = self.store_path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.store_path)