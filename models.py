from enum import unique
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.schema import UniqueConstraint

db = SQLAlchemy()


def connect_db(app):
    """Connect this database to provided Flask app.

    You should call this in your Flask app.
    """

    db.app = app
    db.init_app(app)


class User(db.Model):
    """Site user."""

    __tablename__ = "users"


    spotify_id = db.Column(db.String,  primary_key=True)
    reccomended_tracks = db.relationship("Reccomended_tracks", backref="user")
    # playlist = db.relationship("playlist", backref="user")


class Reccomended_tracks(db.Model):
    """reccomeded tracks for the user"""

    __tablename__ = "reccomended_tracks"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    artist = db.Column(db.String(), nullable=False)
    title = db.Column(db.String(), nullable=False)
    song_id = db.Column(db.String(), nullable=False)
    playlist_id = db.Column(db.Integer,db. ForeignKey(
        'playlists.id'), nullable=False)
 
    user_id = db.Column(db.String, db. ForeignKey(
        'users.spotify_id'), nullable=False)


class Recently_played_tracks(db.Model):
    """reccomeded tracks for the user"""

    __tablename__ = "recently_played_tracks"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    artist = db.Column(db.String(), nullable=False)
    title = db.Column(db.String(),  nullable=False)
    song_id = db.Column(db.String(), unique=True, nullable=False)
    artist_id = db.Column(db.String(), nullable=False)
    song_tempo = db.Column(db.String())
    song_key = db.Column(db.String())
    user_id = db.Column(db.String(), db. ForeignKey(
        'users.spotify_id'), nullable=False)

class Seed_tracks(db.Model):
    """reccomeded tracks for the user"""

    __tablename__ = "seed_tracks"

    id = db.Column(db.Integer, primary_key=True)
    artist = db.Column(db.String(), nullable=False)
    title = db.Column(db.String(), nullable=False)
    song_id = db.Column(db.String(), nullable=False)
    artist_id = db.Column(db.String())
    user_id = db.Column(db.String(), db. ForeignKey(
        'users.spotify_id'), nullable=False)


class playlist(db.Model):
    """playlist made of new recommended songs"""

    __tablename__ = "playlists"

    id = db.Column(db.Integer, primary_key=True)
    playlist_name = db.Column(db.String(), nullable=False)
    user_id = db.Column(db.String, db. ForeignKey(
        'users.spotify_id'), nullable=False)

class playlist_tracks(db.Model):

    __tablename__ = "playlist_tracks"


    song_id = db.Column(db.String, primary_key=True)   
    playlist_id = db.Column(db.Integer(), nullable=False)
    artist_name = db.Column(db.String(), nullable=False)
    track_name = db.Column(db.String(), nullable=False)
  

    