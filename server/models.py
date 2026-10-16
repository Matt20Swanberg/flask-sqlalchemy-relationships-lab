"""Define EventWise database tables and their ORM relationships.

Event-to-Session is one-to-many, Speaker-to-Bio is one-to-one, and
Session-to-Speaker is many-to-many through the session_speakers table.
"""

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from sqlalchemy.ext.associationproxy import association_proxy

# Use predictable foreign-key constraint names for migrations
metadata = MetaData(naming_convention={
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
})

# Share this SQLAlchemy instance with the Flask application
db = SQLAlchemy(metadata=metadata)

# Join table for the many-to-many Session/Speaker relationship
# The composite primary key prevents duplicate session/speaker pairs
session_speakers = db.Table(
    'session_speakers',
    metadata,
    db.Column(
        'speaker_id',
        db.Integer,
        db.ForeignKey('speakers.id'),
        primary_key=True
    ),
    db.Column(
        'session_id',
        db.Integer,
        db.ForeignKey('sessions.id'),
        primary_key=True
    )
)


class Event(db.Model):
    """Represent a conference event containing zero or more sessions.

    Deleting an event also deletes its dependent sessions.
    """
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    location = db.Column(db.String, nullable=False)

    # Removing an event cascades deletion to its sessions
    sessions = db.relationship('Session', back_populates='event', cascade='all, delete-orphan')

    def __repr__(self):
        """Return a readable summary of this event for debugging."""
        return f'<Event {self.id}, {self.name}, {self.location}>'

class Session(db.Model):
    """Represent a scheduled session belonging to an event.

    Sessions may have multiple speakers, and speaker_names exposes their
    names directly through an SQLAlchemy association proxy.
    """
    __tablename__ = 'sessions'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    start_time = db.Column(db.DateTime)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'))
    event = db.relationship('Event', back_populates="sessions")
    speakers = db.relationship('Speaker', secondary=session_speakers, back_populates='sessions')

    # Access related speaker names without manually iterating over speakers
    speaker_names = association_proxy('speakers', 'name')


    def __repr__(self):
        """Return a readable summary of this session for debugging."""
        return f'<Session {self.id}, {self.title}, {self.start_time}>'


class Speaker(db.Model):
    """Represent a speaker with an optional bio and multiple sessions.

    Deleting a speaker also deletes its associated biography.
    """
    __tablename__ = 'speakers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)

    # uselist=False makes this a scalar one-to-one relationship
    bio = db.relationship('Bio', uselist=False, back_populates='speaker', cascade='all, delete-orphan')
    sessions = db.relationship(
        'Session', secondary=session_speakers, back_populates='speakers'
    )

    def __repr__(self):
        """Return a readable summary of this speaker for debugging."""
        return f'<Speaker {self.id}, {self.name}>'

class Bio(db.Model):
    """Represent the optional, unique biography of one speaker."""
    __tablename__ = 'bios'

    id = db.Column(db.Integer, primary_key=True)
    bio_text = db.Column(db.Text, nullable=False)

    # A unique foreign key prevents multiple biographies per speaker
    speaker_id = db.Column(db.Integer, db.ForeignKey('speakers.id'), unique=True)

    speaker = db.relationship('Speaker', back_populates='bio')

    def __repr__(self):
        """Return a readable summary of this biography for debugging."""
        return f'<Bio {self.id}, {self.bio_text}>'
