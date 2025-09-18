from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
from flask_cors import CORS
from file_store import FileSessionStore
from create_session import create_session

from apscheduler.schedulers.background import BackgroundScheduler # type: ignore  # pyright: ignore[reportMissingTypeStubs]
from initial_call import make_patient_call


app = Flask(__name__)
cors = CORS(app, origins='*')

upload_folder = "uploaded_notes"
os.makedirs(upload_folder, exist_ok=True)

store = FileSessionStore(base_dir="sessions", ext=".json")


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
        session_id = create_session(file_path, store)
    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to create session'}), 500

    return jsonify({'message': 'File uploaded', 'session_id': session_id}), 200


@app.route('/api/users', methods=['GET'])
def get_users():
    return jsonify({'message': 'Users fetched'}), 200


scheduler = BackgroundScheduler()


def check_new_sessions():
    # Go through sessions and find new ones
    for session_id, sess in list(store.get_by_status('new').items()):
        print(f"[Scheduler] New session {session_id}, starting first call.")
        # Mark session as processed, so that we don't call it again
        store.update(session_id, {'status': 'calling'})
        # function to start the call, implement in step 5
        print(f"[Scheduler] Starting first call for session {session_id}")
        make_patient_call(store.get(session_id)["data"])
        print(f"[Scheduler] First call completed for session {session_id}")

        store.update(session_id, {'status': 'initial_call_completed'})



# Register task in scheduler: execute every 30 seconds
scheduler.add_job(check_new_sessions, 'interval', seconds=5)

# Start scheduler together with Flask


@app.before_request
def start_scheduler():
    if not scheduler.running:
        scheduler.start()


@app.teardown_appcontext
def shutdown_scheduler(exception=None):
    scheduler.shutdown()


if __name__ == "__main__":
    app.run(debug=True, port=8080)
