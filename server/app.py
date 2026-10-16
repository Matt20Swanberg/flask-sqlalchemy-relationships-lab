#!/usr/bin/env python3
"""Expose EventWise conference data through read-only Flask JSON endpoints.

The API queries SQLAlchemy models and traverses relationships between events,
sessions, speakers, and biographies. Missing resources return HTTP 404.
"""

from flask import Flask, jsonify, make_response
from flask_migrate import Migrate

from models import db, Event, Session, Speaker, Bio

# Create the Flask application and configure its SQLite database
app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

# Enable Alembic migrations and connect SQLAlchemy to this application
migrate = Migrate(app, db)
db.init_app(app)

# ==========================================
# Reusable Serialization Helper Functions
# ==========================================

def serialize_session(session, include_start_time=False):
    """
    Convert a Session model instance into a dictionary.

    Args:
        session (Session): The session to serialize.
        include_start_time (bool): Whether to include the start time.

    Returns:
        dict: Serialized session information.
    """
    session_dict = {
        "id": session.id,
        "title": session.title
    }

    if include_start_time:
        session_dict["start_time"] = (
            session.start_time.isoformat()
            if session.start_time else None
        )

    return session_dict


def serialize_speaker(speaker, include_bio=False):
    """
    Convert a Speaker model instance into a dictionary.

    Args:
        speaker (Speaker): The speaker to serialize.
        include_bio (bool): Whether to include biography text.

    Returns:
        dict: Serialized speaker information.
    """
    speaker_dict = {
        "id": speaker.id,
        "name": speaker.name
    }

    if include_bio:
        speaker_dict["bio_text"] = (
            speaker.bio.bio_text
            if speaker.bio else "No bio available"
        )

    return speaker_dict

# ==========================================
# API Endpoints
# ==========================================

@app.route('/')
def index():
    """Return a welcome message confirming that the API is running."""
    body = {'message': 'Welcome to my lab'}
    return make_response(body, 200)

@app.route('/events', methods=["GET"])
def get_events():
    """Return all events with the IDs and titles of their related sessions.

    Returns:
        Flask JSON response: Event dictionaries and HTTP 200.
    """
    events = Event.query.all()
    event_list = []

    for event in events:
        session_dict = [
            serialize_session(session)
            for session in event.sessions
        ]

        event_dict = {
            "id": event.id,
            "name": event.name,
            "location": event.location,
            "sessions": session_dict
        }

        event_list.append(event_dict)

    return jsonify(event_list), 200


@app.route('/events/<int:id>/sessions')
def get_event_sessions(id):
    """
    Retrieve all sessions associated with a specific event.

    Args:
        id (int): The event's unique ID.

    Returns:
        JSON: List of associated sessions.
        HTTP 200: Event found.
        HTTP 404: Event not found.
    """
    event = Event.query.filter(Event.id == id).first()

    # Return 404 if the event does not exist
    if event is None:
        return jsonify({"error": "Event not found"}), 404

    # SQLAlchemy loads the sessions associated with this event
    sessions = event.sessions

    session_dict = [
        serialize_session(session, include_start_time=True)
        for session in event.sessions
    ]

    return jsonify(session_dict), 200


@app.route('/speakers', methods=["GET"])
def get_speakers():
    """
    Retrieve all speakers from the database.

    Returns:
        JSON: List of speakers containing their ID and name.
        HTTP 200: Successful request.
    """
    # Retrieve all speakers from the database
    speakers = Speaker.query.all()

    # Serialize each speaker into a dictionary
    speaker_list = [
        serialize_speaker(speaker)
        for speaker in speakers
    ]

    # Return all speakers as JSON
    return jsonify(speaker_list), 200


@app.route('/speakers/<int:id>', methods=["GET"])
def get_speaker(id):
    """
    Retrieve a specific speaker and their biography.

    Args:
        id (int): The speaker's unique ID.

    Returns:
        JSON: Speaker details including biography text.
        HTTP 200: Speaker found.
        HTTP 404: Speaker not found.
    """
    # Retrieve the speaker matching the provided ID
    speaker = Speaker.query.filter(Speaker.id == id).first()

    # Return 404 if the speaker does not exist
    if speaker is None:
        return jsonify({"error": "Speaker not found"}), 404

    # Serialize the speaker into a dictionary
    speaker_dict = serialize_speaker(speaker, include_bio=True)

    # Return the speaker as JSON
    return jsonify(speaker_dict), 200


@app.route('/sessions/<int:id>/speakers')
def get_session_speakers(id):
    """
    Retrieve all speakers associated with a specific session.

    Args:
        id (int): The session's unique ID.

    Returns:
        JSON: List of speakers including biography text.
        HTTP 200: Session found.
        HTTP 404: Session not found.
    """
    session = Session.query.filter(Session.id == id).first()

    # Return 404 if the session does not exist
    if session is None:
        return jsonify({"error": "Session not found"}), 404

    speaker_list = []

    for speaker in session.speakers:
        speaker_dict = serialize_speaker(speaker, include_bio=True)

        # Preserve the original endpoint's missing-bio behavior.
        if speaker.bio is None:
            speaker_dict["bio_text"] = None

        speaker_list.append(speaker_dict)

    return jsonify(speaker_list), 200

@app.route('/speakers/<int:id>/bio')
def get_speaker_bio(id):
    """
    Retrieve the biography associated with a specific speaker.

    Args:
        id (int): The speaker's unique ID.

    Returns:
        JSON: Biography ID, text, and speaker ID.
        HTTP 200: Biography found.
        HTTP 404: Speaker or biography not found.
    """
    speaker = Speaker.query.filter(Speaker.id == id).first()

    # Return 404 if the speaker does not exist
    if speaker is None:
        return jsonify({"error": "Speaker not found"}), 404

    # The one-to-one relationship returns a Bio object or None
    bio = speaker.bio

    if bio is None:
        return jsonify({"error": "Bio not found"}), 404

    bio_dict = {
        "id": bio.id,
        "bio_text": bio.bio_text,
        "speaker_id": bio.speaker_id
    }

    return jsonify(bio_dict), 200

@app.route('/speakers/<int:id>/sessions', methods=["GET"])
def get_speaker_sessions(id):
    """
    Retrieve all sessions associated with a specific speaker.

    Args:
        id (int): The speaker's unique ID.

    Returns:
        JSON: List of associated sessions containing ID and title.
        HTTP 200: Speaker found.
        HTTP 404: Speaker not found.
    """
    # Retrieve the speaker matching the provided ID
    speaker = Speaker.query.filter(Speaker.id == id).first()

    # Return 404 if the speaker does not exist
    if speaker is None:
        return jsonify({"error": "Speaker not found"}), 404

    # Serialize the speaker into a dictionary
    session_dict = [
        serialize_session(session)
        for session in speaker.sessions
    ]

    # Return the serialized sessions as JSON
    return jsonify(session_dict), 200

   
# Start the development server only when this module is run directly
if __name__ == '__main__':
    app.run(port=5555, debug=True)