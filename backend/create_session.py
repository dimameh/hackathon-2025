import uuid
from typing import Any
from file_store import FileSessionStore
from parse_doc import parse_doc


def create_session(file_path: str, store: FileSessionStore) -> str:
    """Creates a new session for the uploaded note."""
    # Generating ID
    session_id = str(uuid.uuid4())
    initial: dict[str, Any] = {
        "file_path": file_path,
        "data": None,
        "status": "new",
        "reminders": []
    }

    parsed_data = parse_doc([file_path])
    initial['data'] = parsed_data

    store.create(initial, session_id=session_id)
    return session_id
