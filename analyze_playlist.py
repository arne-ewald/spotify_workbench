import os
from collections import Counter
from datetime import datetime
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import matplotlib.pyplot as plt
import pandas as pd
from wordcloud import WordCloud
from collections import defaultdict

# Load credentials from .env
load_dotenv()

SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")
SCOPE = "playlist-read-private"

# Initialize Spotify client
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET,
    redirect_uri=SPOTIPY_REDIRECT_URI,
    scope=SCOPE
))

# Fetch playlists
playlists = []
offset = 0
limit = 50
while True:
    response = sp.current_user_playlists(limit=limit, offset=offset)
    playlists.extend(response['items'])
    if len(response['items']) < limit:
        break
    offset += limit

# Find playlist ID
playlist_name = "Ohrenschmaus"  # Name of the collaborative playlist
playlist_id = None
for playlist in playlists:
    if playlist['name'].lower() == playlist_name.lower():
        playlist_id = playlist['id']
        break

if not playlist_id:
    raise ValueError(f"Playlist '{playlist_name}' not found!")

# Fetch all tracks
tracks = []
offset = 0
limit = 100
while True:
    response = sp.playlist_items(
        playlist_id,
        limit=limit,
        offset=offset,
        fields="items(track(album(artists, id, name), id, name, duration_ms), added_by.id, added_at)"
    )
    tracks.extend(response['items'])
    if len(response['items']) < limit:
        break
    offset += limit

# Process tracks
artist_counter = Counter()
contributor_counter = Counter()
genre_counter = Counter()
durations = []
added_dates = []
user_contributions = defaultdict(list)

for item in tracks:
    track = item['track']

    # Skip None tracks (e.g., removed or unavailable tracks)
    if track is None:
        continue

    added_by = item['added_by']['id']
    contributors_name = sp.user(added_by)['display_name']

    added_at = item['added_at']
    added_date = datetime.strptime(added_at, "%Y-%m-%dT%H:%M:%SZ")
    added_dates.append(added_date)

    contributor_counter[contributors_name] += 1
    
    user_contributions[contributors_name].append(added_date)

    # Safely handle missing 'duration_ms'
    if 'duration_ms' in track and track['duration_ms'] is not None:
        durations.append(track['duration_ms'])
    else:
        print(f"Track '{track.get('name', 'Unknown')}' missing 'duration_ms'")

    artists = [artist['name'] for artist in track['album']['artists']]
    artist_counter.update(artists)

    for artist_id in [artist['id'] for artist in track['album']['artists']]:
        if artist_id:
            artist_info = sp.artist(artist_id)
            genres = artist_info.get('genres', [])
            genre_counter.update(genres)


# Visualize and print statistics
print(f"Analysis of '{playlist_name}':")
print(f"Total Tracks: {len(tracks)}")
print(f"Unique Artists: {len(artist_counter)}")
print(f"Total Duration: {sum(durations) // 60000 // 60} hours")

# Cumulative Tracks Added Over Time
added_dates.sort()
cumulative_counts = range(1, len(added_dates) + 1)
plt.figure(figsize=(10, 6))
plt.plot(added_dates, cumulative_counts, marker="o")
plt.title("Cumulative Tracks Added Over Time")
plt.xlabel("Date")
plt.ylabel("Total Tracks")
plt.grid()
plt.tight_layout()
plt.show()

# Top Artists
top_artists = pd.DataFrame(artist_counter.most_common(10), columns=["Artist", "Count"])
plt.figure(figsize=(10, 6))
plt.bar(top_artists["Artist"], top_artists["Count"])
plt.title("Top 10 Artists")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# Contributions by User
contributors = pd.DataFrame(contributor_counter.items(), columns=["Contributor", "Tracks"]).sort_values(by="Tracks", ascending=False)
plt.figure(figsize=(10, 6))
plt.pie(contributors["Tracks"], labels=contributors["Contributor"], autopct="%1.1f%%", startangle=140)
plt.title("Contributions by User")
plt.tight_layout()
plt.show()

# Genre Word Cloud
genre_text = " ".join([genre for genre, count in genre_counter.items() for _ in range(count)])
wordcloud = WordCloud(width=800, height=400, background_color="white").generate(genre_text)
plt.figure(figsize=(10, 6))
plt.imshow(wordcloud, interpolation="bilinear")
plt.axis("off")
plt.title("Genre Word Cloud")
plt.tight_layout()
plt.show()

# Genre Bar Chart
top_genres = pd.DataFrame(genre_counter.most_common(10), columns=["Genre", "Count"])
plt.figure(figsize=(10, 6))
plt.bar(top_genres["Genre"], top_genres["Count"])
plt.title("Top 10 Genres")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()


# Convert to a DataFrame for visualization
data = []
for user, dates in user_contributions.items():
    for date in dates:
        data.append({'User': user, 'Date': date})

df = pd.DataFrame(data)
df.sort_values(by='Date', inplace=True)  # Ensure the data is sorted by date

# Create a cumulative count for each user
df['Cumulative Count'] = df.groupby('User').cumcount() + 1

# Plot the data
plt.figure(figsize=(12, 8))
for user in df['User'].unique():
    user_data = df[df['User'] == user]
    plt.plot(user_data['Date'], user_data['Cumulative Count'], marker='o', label=user)

plt.title("Cumulative Contributions Over Time")
plt.xlabel("Date")
plt.ylabel("Cumulative Tracks Added")
plt.legend(title="Users")
plt.grid()
plt.tight_layout()
plt.show()
