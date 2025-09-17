from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
from flask_cors import CORS
import uuid
from typing import Any
from file_store import FileSessionStore
from parse_doc import parse_doc

app = Flask(__name__)
cors = CORS(app, origins='*')

upload_folder = "uploaded_notes"
os.makedirs(upload_folder, exist_ok=True)

store = FileSessionStore(base_dir="sessions", ext=".json")


def create_session(file_path: str) -> str:
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


@app.route('/api/upload', methods=['POST'])
def upload_note():
    # Checking if the file is present in the request
    if 'note' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['note']
    if file.filename == '' or file.filename is None:
        return jsonify({'error': 'Empty filename'}), 400

    # Saving the file on the server with a safe name
    filename = secure_filename(file.filename)
    file_path = os.path.join(upload_folder, filename)
    file.save(file_path)

    # Creating a new session (details will be implemented on the next steps)
    # function create_session will be implemented later
    try:
        session_id = create_session(file_path)
    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to create session'}), 500
        
    return jsonify({'message': 'File uploaded', 'session_id': session_id}), 200


@app.route('/api/users', methods=['GET'])
def get_users():
    return jsonify({'message': 'Users fetched'}), 200


if __name__ == "__main__":
    app.run(debug=True, port=8080)
