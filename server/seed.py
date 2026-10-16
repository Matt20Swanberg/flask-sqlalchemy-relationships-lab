#!/usr/bin/env python3
"""Reset and populate the EventWise database with demonstration records.

WARNING: Running this script deletes existing records in the five
application tables before inserting the sample dataset.
"""

from app import app
from models import db, Event, Session, Speaker, Bio
import datetime

# Database operations require an active Flask application context
with app.app_context():
    # Clear join-table rows first, followed by dependent and parent records
    # This is a destructive reset: existing application data is removed
    db.session.execute(db.text('DELETE FROM session_speakers'))
    Bio.query.delete()
    Session.query.delete()
    Speaker.query.delete()
    Event.query.delete()
    db.session.commit()

    # Create two conference events (parents of the session records)
    event1 = Event(name="Tech Future Conference", location="New York")
    event2 = Event(name="AI World Summit", location="San Francisco")
    db.session.add_all([event1, event2])
    db.session.commit()

    # Create sessions and link them to events through the event relationship
    session1 = Session(title="Building Scalable Web Apps", start_time=datetime.datetime(2023, 9, 15, 10, 0), event=event1)
    session2 = Session(title="Intro to Machine Learning", start_time=datetime.datetime(2023, 9, 15, 14, 0), event=event1)
    session3 = Session(title="The Future of AI Ethics", start_time=datetime.datetime(2023, 10, 20, 11, 0), event=event2)
    db.session.add_all([session1, session2, session3])
    db.session.commit()

    # Create speaker records independently of their session assignments
    speaker1 = Speaker(name="Alex Johnson")
    speaker2 = Speaker(name="Riley Chen")
    speaker3 = Speaker(name="Jordan Brooks")
    db.session.add_all([speaker1, speaker2, speaker3])
    db.session.commit()

    # Attach one biography to each speaker using the one-to-one relationship
    bio1 = Bio(bio_text="Expert in scalable backend systems with 10+ years of experience.", speaker=speaker1)
    bio2 = Bio(bio_text="AI researcher focusing on machine learning and data ethics.", speaker=speaker2)
    bio3 = Bio(bio_text="Software engineer passionate about teaching and open source.", speaker=speaker3)
    db.session.add_all([bio1, bio2, bio3])
    db.session.commit()

    # Populate the many-to-many join table via the speakers relationship
    session1.speakers.append(speaker1)
    session2.speakers.append(speaker2)
    session2.speakers.append(speaker3)
    session3.speakers.append(speaker2)
    db.session.commit()

    # Confirm the seed script completed all inserts and associations
    print("🌱 Database seeded successfully!")
