import os
from collections import Counter
from datetime import datetime
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Load credentials from .env
load_dotenv()

SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")
SCOPE = "playlist-read-private playlist-modify-private"

def get_most_common_artist_album(sp, playlist_id):
    """Find the most common artist and album in a playlist."""
    tracks = sp.playlist_items(playlist_id, fields="items(track(album(name, artists(name))))")
    artist_counter = Counter()
    album_counter = Counter()

    for item in tracks['items']:
        track = item['track']
        album = track['album']
        artist_counter.update(artist['name'] for artist in album['artists'])
        album_counter.update([album['name']])

    # Return most common artist and album
    common_artist = artist_counter.most_common(1)[0][0] if artist_counter else "Unknown Artist"
    common_album = album_counter.most_common(1)[0][0] if album_counter else "Unknown Album"
    return common_artist, common_album


def rename_playlists(sp, folder_name, target_folder):
    """Rename playlists in a specified folder."""
    user_id = sp.me()['id']
    playlists = sp.current_user_playlists()
    
    for playlist in playlists['items']:
        playlist_name = playlist['name']
        playlist_id = playlist['id']

        # Check if playlist belongs to the target folder
        if folder_name in playlist_name and target_folder in playlist_name:
            print(f"Processing playlist: {playlist_name}")
            
            # Extract most common artist and album
            # artist, album = get_most_common_artist_album(sp, playlist_id)
            # new_name = f"{artist} - {album}"
            
            # Rename playlist
            # sp.user_playlist_change_details(user=user_id, playlist_id=playlist_id, name=new_name)
            # print(f"Renamed to: {new_name}")

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET,
    redirect_uri=SPOTIPY_REDIRECT_URI,
    scope=SCOPE
))

user_id = "teilnehmenderbeobachter"
start_date = "2024-12-26"

threshold_date = datetime.strptime(start_date, "%Y-%m-%d")

# Fetch all playlists
playlists = sp.current_user_playlists()

for playlist in playlists['items']:
    # Check if the playlist was created by the user
    if playlist['owner']['id'] == user_id:
        playlist_id = playlist['id']
        playlist_name = playlist['name']

        # Approximate creation date based on earliest track added
        tracks = sp.playlist_items(playlist_id, fields="items(added_at)")
        timestamps = [item['added_at'] for item in tracks['items'] if item['added_at']]
        
        if timestamps:
            # Find the earliest track addition
            earliest_date = min(timestamps)
            earliest_datetime = datetime.strptime(earliest_date, "%Y-%m-%dT%H:%M:%SZ")

            # Check if the playlist falls within the threshold
            if earliest_datetime >= threshold_date:
                # Get the most common artist and album
                artist, album = get_most_common_artist_album(sp, playlist_id)
                new_name = f"{artist} - {album}"

                # Rename the playlist
                sp.user_playlist_change_details(user=user_id, playlist_id=playlist_id, name=new_name)
                print(f"Renamed playlist '{playlist_name}' to '{new_name}'")
        else:
            print(f"No track data available for playlist: {playlist_name}")


