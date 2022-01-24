
from types import MethodWrapperType
from flask import Flask, session, request, redirect, render_template, json, jsonify
from flask.templating import render_template_string
from flask_session import Session
from dotenv import load_dotenv
import os
import re
import spotipy
import uuid
from models import Recently_played_tracks, db, connect_db, User, Reccomended_tracks, playlist, Seed_tracks, playlist_tracks
from forms import createPlaylistForm
import json
import pandas as pd
from sqlalchemy.exc import IntegrityError


load_dotenv()


app = Flask(__name__)

# uri = os.getenv("DATABASE_URL")
# if uri.startswith("postgres://"):
#     uri = uri.replace("postgres://", "postgresql://")

# engine = create_engine(uri, echo=True)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL').replace("://", "ql://", 1)

# app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "postgresql:///fluidity")
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'hellosecret1')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'


connect_db(app)





caches_folder = './.spotify_caches/'
if not os.path.exists(caches_folder):
    os.makedirs(caches_folder)


def session_cache_path():
    return caches_folder + session.get('uuid')


@app.route('/')
def index():
    if not session.get('uuid'):
        # Step 1. Visitor is unknown, give random ID
        session['uuid'] = str(uuid.uuid4())


    cache_handler = spotipy.cache_handler.CacheFileHandler(
        cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(scope='user-read-recently-played user-read-private user-top-read user-read-currently-playing playlist-modify-public',
                                               cache_handler=cache_handler,
                                               show_dialog=True)

    if request.args.get("code"):
        # Step 3. Being redirected from Spotify auth page
        auth_manager.get_access_token(request.args.get("code"))
        return redirect('/')

    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        # Step 2. Display sign in link when no token
        auth_url = auth_manager.get_authorize_url()
        return f'<h2><a href="{auth_url}">Sign in</a></h2>'

    # Step 4. Signed in, display data
    spotify = spotipy.Spotify(auth_manager=auth_manager)

    user_id = spotify.me()['id']

    user = User(spotify_id=user_id)

    if User.query.get(user_id):


        return redirect('/home')

    else:

       db.session.add(user)
       db.session.commit()

       return redirect('/home')


@app.route('/home')
def home_page_for_playlist_form():
    """diplsay a form to create a new playlist"""

    sp = validate()
    user_id = sp.me()['id']
    form = createPlaylistForm()

    playlist_names = show_all_playlists()

    if form.validate_on_submit():
        playlist_name = form.playlist_name.data

        response = sp.user_playlist_create(user_id, name=playlist_name)

        newPlaylist = playlist(playlist_name=playlist_name, user_id=user_id)
        db.session.add(newPlaylist)

        try:
            db.session.commit()
            
        except IntegrityError:
            db.session.rollback()

        user = User.query.get_or_404(user_id)
        user.playlist_id = newPlaylist.id
        db.session.commit()

        return redirect('/recently_played')
    else:
    
        return render_template("/index.html", form=form, playlist_names=playlist_names)

@app.route('/playlist', methods=['POST', 'GET'])
def create_playlist():
    """use form data to create a new playlist"""

    sp = validate()
    user_id = sp.me()['id']
    form = createPlaylistForm()

    if form.validate_on_submit():
        playlist_name = form.playlist_name.data

        response = sp.user_playlist_create(user_id, name=playlist_name)

        newPlaylist = playlist(playlist_name=playlist_name, user_id=user_id)
        db.session.add(newPlaylist)

        try:
            db.session.commit()
            
        except IntegrityError:
            db.session.rollback()

        user = User.query.get_or_404(user_id)
        user.playlist_id = newPlaylist.id
        db.session.commit()

        return redirect('/recently_played')

    else:
        return redirect('/', form=form)

@app.route('/handle_audio_features')
def get_audio_features():

    sp = validate()
    user_id = sp.me()['id']

    track_key = []
    track_tempo= []
    track_id = []

    tracks = []

    response = sp.current_user_recently_played(
        limit=30, after=None, before=None)

    for song in response['items']:

        song_id=song['track']["id"]

        tracks.append(song_id)

    features = sp.audio_features(tracks=tracks)

    for feature in features:

        track_key.append(feature['key'])
        track_tempo.append(feature['tempo'])
        track_id.append(feature['id'])

    return str(feature)


@app.route('/recently_played')
def get_recently_played_tracks():
    """display a list of recently played tracks with audio features"""

    sp = validate()
    user_id = sp.me()['id']

    response = sp.current_user_recently_played(
        limit=50, after=None, before=None)

    genres = sp.recommendation_genre_seeds()

    user_id = sp.me()['id']

    response = sp.current_user_recently_played(
        limit=30, after=None, before=None)


    list_1 = []

    for song in response['items']:

        list_1.append(song['track']["id"])

        if len(list_1) == len(set(list_1)):

            rec_track = Recently_played_tracks(artist=song['track']["album"]['artists'][0]['name'], title=song['track']['name'], song_id=song['track']["id"], artist_id=song['track']["album"]['artists'][0]['id'], user_id=user_id)
            
            db.session.add(rec_track)
    try:
        db.session.commit()
            
    except IntegrityError:
        db.session.rollback()
  
    tracks = Recently_played_tracks.query.filter_by(
                user_id=user_id).limit(20)
       
    features = sp.audio_features(list_1)

    all_tracks = Recently_played_tracks.query.all()


    for track in all_tracks:

        for feature in features:

            if track.song_id == feature['id']:

                track.song_tempo = feature['tempo']
                track.song_key = feature['key']

    db.session.commit()

    return render_template('recently_played_tracks.html', tracks=tracks) 

    
  
  

@app.route('/add_seed_track/<int:id>')
def handle_seed_tracks(id):
    """add seed tracks takedn from recently played tracks"""

    track = Recently_played_tracks.query.get_or_404(id)

    seed = Seed_tracks(artist=track.artist,title=track.title , song_id=track.song_id, artist_id=track.artist_id, user_id=track.user_id)
    
    db.session.add(seed)
    try:
        db.session.commit()
            
    except IntegrityError:
        db.session.rollback()
    

    return redirect('/recently_played')
       


@app.route('/reccomendations', methods=['GET','POST'])
def get_seed_tracks():

    sp = validate()
    user_id = sp.me()['id']

    seed_tracks_tracks = []
    seed_tracks_artist = []
    seed_genres = ['alternative', 'ambient', 'chill', 'deep-house', 'groove']

    user = User.query.get_or_404(user_id)

    seed_tracks = Seed_tracks.query.limit(5)

    playlist_id= user.playlist_id

    p = playlist.query.get_or_404(playlist_id)

    for seed_track in seed_tracks:


       seed_tracks_tracks.append(seed_track.song_id)
       seed_tracks_artist.append(seed_track.artist_id)

    response = sp.recommendations(seed_tracks=seed_tracks_tracks)

    for song in response['tracks']:

        title = song['name']
        song_id = song['id']

        for artist_name in song['artists']:

           artist = artist_name['name']
    
        reco_track = Reccomended_tracks(artist=artist, title=title, song_id=song_id, user_id=user_id, playlist_id=playlist_id)

        db.session.add(reco_track)

    try:
        db.session.commit()
            
    except IntegrityError:
        db.session.rollback()
 
    tracks = Reccomended_tracks.query.filter_by(
                playlist_id=playlist_id).limit(20)

    return render_template('reccomended_tracks_playlist.html', tracks=tracks, playlist_id=playlist_id)


@app.route('/handle_add_tracks_to_playlist/<int:id>')
def handle_add_track_to_playlist(id):
    """add track to current playlist from reccomended tracks"""

    sp = validate()
    track = Reccomended_tracks.query.get_or_404(id)
  
    track_id = track.song_id
    tracks = []
    tracks.append(track_id)
    playlist_id = track.playlist_id
    current_playlist = playlist.query.get_or_404(playlist_id)
    username = sp.me()['id']
    playlist_name = current_playlist.playlist_name
    spotify_playlist_id = GetPlaylistID(username, playlist_name)

    response = sp.playlist_add_items(playlist_id=spotify_playlist_id, items=tracks)

    return redirect('/reccomendations')
 

@app.route('/playlist/<int:id>')
def show_playlist(id):

    sp = validate()

    current_playlist = playlist.query.get_or_404(id)
    username = sp.me()['id']
    playlist_name = current_playlist.playlist_name
    spotify_playlist_id = GetPlaylistID(username, playlist_name)

    response = sp.user_playlist_tracks(user = username,playlist_id=spotify_playlist_id)['items']

    for song_id in response:

        song = song_id["track"]["id"] 

        all_tracks = playlist_tracks.query.filter_by(song_id=song)

    playlist_features = {}

    for track in response:

        artist =  track["track"]["album"]["artists"][0]["name"]
        track_name = track["track"]["name"]
        song_id = track["track"]["id"]

        playlist_track = playlist_tracks(artist_name=artist,track_name=track_name, playlist_id=id, song_id=song_id)

   
        db.session.add(playlist_track)

        try:
            db.session.commit()
            
        except IntegrityError:
            db.session.rollback()
        
    tracks = playlist_tracks.query.filter_by(
                playlist_id=id).limit(30)

    return render_template('show_playlist.html', tracks=tracks, current_playlist=current_playlist)


def show_all_playlists():

    sp = validate()
    username = sp.me()['id']

    response = sp.user_playlists(username, limit=50, offset=0)


    user_playlist_names=[]

    for playlist in response['items']:

        
        user_playlist_names.append(playlist['name'])
        

    return str(user_playlist_names)


        

    




   

    


    

    

 

    

     




@ app.route('/currently_playing')
def currently_playing():
    cache_handler = spotipy.cache_handler.CacheFileHandler(
        cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    track = spotify.current_user_playing_track()
    if not track is None:
        return track
    return "No track currently playing."


@ app.route('/current_user')
def current_user():
    cache_handler = spotipy.cache_handler.CacheFileHandler(
        cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    return spotify.current_user()


'''
Following lines allow application to be run more conveniently with
`python app.py` (Make sure you're using python3)
(Also includes directive to leverage pythons threading capacity.)
'''
# if __name__ == '__main__':
#     app.run(threaded=True, port=int(os.environ.get("PORT",
#                                                    os.environ.get("SPOTIPY_REDIRECT_URI", 8080).split(":")[-1])))




@app.route('/test')
def test():


    sp = validate()


    track = Reccomended_tracks.query.get_or_404(1)

   
    track_id = track.song_id
    tracks = []
    tracks.append(track_id)
    playlist_id = track.playlist_id
    current_playlist = playlist.query.get_or_404(playlist_id)
    username = sp.me()['id']
    playlist_name = 'run'
    spotify_playlist_id = GetPlaylistID(username, playlist_name)
    response = sp.playlist_add_items(playlist_id='4TDipLAhGc0cjmEccnE26O', items=['5DiQ3VjKVa9GgSoKj4Fwgh'])

  

    return str(response)

def validate():

    cache_handler = spotipy.cache_handler.CacheFileHandler(
        cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')

    else:
        sp = spotipy.Spotify(auth_manager=auth_manager)
        return sp 



  

def GetPlaylistID(username, playlist_name):

    cache_handler = spotipy.cache_handler.CacheFileHandler(
        cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)

    sp = spotipy.Spotify(auth_manager=auth_manager)

    playlist_id = ''
    playlists = sp.user_playlists(username)
    for playlist in playlists['items']:  # iterate through playlists I follow
        if playlist['name'] == playlist_name:  # filter for newly created playlist
            playlist_id = playlist['id']
    return playlist_id
    

def call_playlist(creator, playlist_id):

    cache_handler = spotipy.cache_handler.CacheFileHandler(
        cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')

    sp = spotipy.Spotify(auth_manager=auth_manager)
    
    #step1

    playlist_features_list = ["artist","album","track_name",  "track_id","danceability","energy","key","loudness","mode", "speechiness","instrumentalness","liveness","valence","tempo", "duration_ms","time_signature"]
    
    playlist_df = pd.DataFrame(columns = playlist_features_list)
    
    #step2
    
    playlist = sp.user_playlist_tracks(creator, playlist_id)["items"]
    for track in playlist:
        # Create empty dict
        playlist_features = {}
        # Get metadata
        playlist_features["artist"] = track["track"]["album"]["artists"][0]["name"]
        playlist_features["album"] = track["track"]["album"]["name"]
        playlist_features["track_name"] = track["track"]["name"]
        playlist_features["track_id"] = track["track"]["id"]
        
        # Get audio features
        audio_features = sp.audio_features(playlist_features["track_id"])[0]
        for feature in playlist_features_list[4:]:
            playlist_features[feature] = audio_features[feature]
        
        # Concat the dfs
        track_df = pd.DataFrame(playlist_features, index = [0])
        playlist_df = pd.concat([playlist_df, track_df], ignore_index = True)

    #Step 3
        
    return playlist_df   


  
 
   