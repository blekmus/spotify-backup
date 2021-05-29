#!/usr/bin/env python3

import argparse
import codecs
import http.client
import http.server
import json
import logging
import re
import sys
import time
import csv
import os
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from datetime import timedelta

logging.basicConfig(level=20, datefmt="%I:%M:%S", format="[%(asctime)s] %(message)s")


class SpotifyAPI:
    # Requires an OAuth token.
    def __init__(self, auth):
        self._auth = auth

    # Gets a resource from the Spotify API and returns the object.
    def get(self, url, params={}, tries=3):
        # Construct the correct URL.
        if not url.startswith("https://api.spotify.com/v1/"):
            url = "https://api.spotify.com/v1/" + url
        if params:
            url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)

        # Try the sending off the request a specified number of times before giving up.
        for _ in range(tries):
            try:
                req = urllib.request.Request(url)
                req.add_header("Authorization", "Bearer " + self._auth)
                res = urllib.request.urlopen(req)
                reader = codecs.getreader("utf-8")
                return json.load(reader(res))
            except Exception as err:
                logging.info("Couldn't load URL: {} ({})".format(url, err))
                time.sleep(2)
                logging.info("Trying again...")
        sys.exit(1)

    # fetches liked, playlists, podcast episodes and albums then joins them
    def list(self, url, params={}):
        response = self.get(url, params)
        items = response["items"]

        # loop through to bring all tracks and their data
        while response["next"]:
            logging.info(f"Loaded {len(items)}/{response['total']} items")

            response = self.get(response["next"])
            items += response["items"]

        return items

    # fetches followed artists and joins them
    def list_artists(self, url, params={}):
        response = self.get(url, params)
        items = response['artists']["items"]

        # loop through to bring all tracks and their data
        while response['artists']["next"]:
            logging.info(f"Loaded {len(items)}/{response['artists']['total']} items")

            response = self.get(response['artists']["next"])
            items += response['artists']["items"]

        return items

    # Pops open a browser window for a user to log in and authorize API access.
    @staticmethod
    def authorize(client_id, scope):
        url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(
            {
                "response_type": "token",
                "client_id": client_id,
                "scope": scope,
                "redirect_uri": f"http://127.0.0.1:{SpotifyAPI._SERVER_PORT}/redirect",
            }
        )
        logging.info(f"Authorizing... (click if browser doesn't open)\n{url}\n")
        webbrowser.open(url)

        # Start a simple, local HTTP server to listen for the authorization token... (i.e. a hack).
        server = SpotifyAPI._AuthorizationServer("127.0.0.1", SpotifyAPI._SERVER_PORT)
        try:
            while True:
                server.handle_request()
        except SpotifyAPI._Authorization as auth:
            return SpotifyAPI(auth.access_token)

    # The port that the local server listens on. Don't change this,
    # as Spotify only will redirect to certain predefined URLs.
    _SERVER_PORT = 43019

    class _AuthorizationServer(http.server.HTTPServer):
        def __init__(self, host, port):
            http.server.HTTPServer.__init__(
                self, (host, port), SpotifyAPI._AuthorizationHandler
            )

        # Disable the default error handling.
        def handle_error(self, request, client_address):
            raise

    class _AuthorizationHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            # The Spotify API has redirected here, but access_token is hidden in the URL fragment.
            # Read it using JavaScript and send it to /token as an actual query string...
            if self.path.startswith("/redirect"):
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(
                    b'<script>location.replace("token?" + location.hash.slice(1));</script>'
                )

            # Read access_token and use an exception to kill the server listening...
            elif self.path.startswith("/token?"):
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(
                    b"<script>close()</script>Thanks! You may now close this window."
                )

                access_token = re.search("access_token=([^&]*)", self.path).group(1)
                logging.info("Received access token from Spotify")
                raise SpotifyAPI._Authorization(access_token)

            else:
                self.send_error(404)

        # Disable the default logging.
        def log_message(self, format, *args):
            pass

    class _Authorization(Exception):
        def __init__(self, access_token):
            self.access_token = access_token


# return formatted hh mm ss
def timematter(x):
    s = timedelta(seconds=x)

    if s.days < 1:
        if s.seconds <= 60 * 60:
            out = f'{s.seconds//60}m {s.seconds - (s.seconds//60)*60}s'
        else:
            out = f'{s.seconds//(60*60)}h {int(s.seconds/60 - (s.seconds//3600)*60)}m {s.seconds - (s.seconds//60)*60}s'
    else:
        out = f'{s.days}d {s.seconds//(60*60)}h {int(s.seconds/60 - (s.seconds//3600)*60)}m {s.seconds - (s.seconds//60)*60}s'
    return out

# save tracks to csv
def save_track(filename, track_list):
    file = open(filename, 'w')

    # init sheet rows
    fieldnames = [
        'Track ID',
        'Album ID',
        'Track Name',
        'Album Name',
        'Artist Name(s)',
        'Release Date',
        'Duration (ms)',
        'Explicity',
        'Album Type',
        'Popularity',
        'Added On',
        'Album Tracks',
        'Track URL',
        'Album URL',
    ]

    # init csv writer
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()

    # loop through tracks and add them as rows
    for track in track_list:
        writer.writerow({
            'Track ID': track['track']['id'],
            'Album ID': track['track']['album']['id'],
            'Track Name': track['track']['name'],
            'Album Name': track['track']['album']['name'],
            'Album Tracks': track['track']['album']['total_tracks'],
            'Artist Name(s)': ", ".join([artist['name'] for artist in track['track']['artists']]),
            'Release Date': track['track']['album']['release_date'],
            'Duration (ms)': timematter(int(track['track']['duration_ms']) / 1000),
            'Explicity': track['track']['explicit'],
            'Album Type': track['track']['album']['album_type'],
            'Popularity': track['track']['popularity'],
            'Added On': track['added_at'],
            'Track URL': track['track']['external_urls']['spotify'],
            'Album URL': track['track']['album']['external_urls']['spotify']
        })

    file.close()

# save artists to csv
def save_artist(filename, artist_list):
    file = open(filename, 'w')

    # init sheet rows
    fieldnames = [
        'ID',
        'Name',
        'Type',
        'Followers',
        'Popularity',
        'URL'
    ]

    # init csv writer
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()

    # loop through artists and add them as rows
    for artist in artist_list:
        writer.writerow({
            'ID': artist['id'],
            'Name': artist['name'],
            'Type': artist['type'],
            'Followers': artist['followers']['total'],
            'Popularity': artist['popularity'],
            'URL': artist['external_urls']['spotify'],
        })

    file.close()

# save albums to csv
def save_album(filename, album_list):
    file = open(filename, 'w')

    # init sheet rows
    fieldnames = [
        'ID',
        'Name',
        'Tracks',
        'Artist Name(s)',
        'Release Date',
        'Label',
        'Type',
        'Popularity',
        'Added On',
        'URL',
    ]

    # init csv writer
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()

    # loop through albums and add them as rows
    for album in album_list:
        writer.writerow({
            'ID': album['album']['id'],
            'Name': album['album']['name'],
            'Tracks': album['album']['total_tracks'],
            'Artist Name(s)': ", ".join([album['name'] for album in album['album']['artists']]),
            'Release Date': album['album']['release_date'],
            'Label': album['album']['label'],
            'Type': album['album']['album_type'],
            'Popularity': album['album']['popularity'],
            'Added On': album['added_at'],
            'URL': album['album']['external_urls']['spotify']
        })

    file.close()

# save podcasts to csv
def save_podcast(filename, podcast_list):
    file = open(filename, 'w')

    # init sheet rows
    fieldnames = [
        'ID',
        'Name',
        'Publisher',
        'Description',
        'Episodes',
        'Type',
        'Explicity',
        'Added On',
        'URL',
    ]

    # init csv writer
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()

    # loop through podcases and add them as rows
    for podcast in podcast_list:
        writer.writerow({
            'ID': podcast['show']['id'],
            'Name': podcast['show']['name'],
            'Description': podcast['show']['description'],
            'Episodes': podcast['show']['total_episodes'],
            'Publisher': podcast['show']['publisher'],
            'Type': podcast['show']['media_type'],
            'Explicity': podcast['show']['explicit'],
            'Added On': podcast['added_at'],
            'URL': podcast['show']['external_urls']['spotify']
        })

    file.close()

# save episodes to csv
def save_episode(filename, episode_list):
    file = open(filename, 'w')

    # init sheet rows
    fieldnames = [
        'Episode ID',
        'Show ID',
        'Episode Name',
        'Show Name',
        'Publisher',
        'Description',
        'Release Date',
        'Duration (ms)',
        'Explicity',
        'Show Type',
        'Added On',
        'Episode URL',
        'Show URL',
    ]

    # init csv writer
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()

    # loop through episodes and add them as rows
    for episode in episode_list:
        writer.writerow({
            'Episode ID': episode['episode']['id'],
            'Show ID': episode['episode']['show']['id'],
            'Episode Name': episode['episode']['name'],
            'Show Name': episode['episode']['show']['name'],
            'Publisher': episode['episode']['show']['publisher'],
            'Description': episode['episode']['description'],
            'Release Date': episode['episode']['release_date'],
            'Duration (ms)': timematter(int(episode['episode']['duration_ms']) / 1000),
            'Explicity': episode['episode']['explicit'],
            'Show Type': episode['episode']['show']['media_type'],
            'Added On': episode['added_at'],
            'Episode URL': episode['episode']['external_urls']['spotify'],
            'Show URL': episode['episode']['show']['external_urls']['spotify']
        })

    file.close()


# log into the Spotify API.
spotify = SpotifyAPI.authorize(
    client_id="fc84b0b659d64f568f72d0d6009ad965",
    scope="playlist-read-private playlist-read-collaborative user-library-read user-follow-read",
)


# get the ID of the logged in user.
logging.info('Loading user info...')
me = spotify.get('me')
logging.info(f"Logged in as {me['display_name']} ({me['id']})")


# create needed dirs
logging.info('Creating needed directories')
os.makedirs('./done/Playlists', exist_ok=True)


# save liked songs
logging.info('Loading liked songs...')
liked_tracks = spotify.list(f"users/{me['id']}/tracks", {'limit': 50})
logging.info('Saving liked songs')
save_track('done/Liked.csv', liked_tracks)


# playlist data
logging.info('Loading playlists...')
playlist_data = spotify.list('users/{user_id}/playlists'.format(user_id=me['id']), {'limit': 50})
user_playlists = [playlist for playlist in playlist_data if playlist['owner']['id'] == me['id']]
logging.info(f'Found {len(user_playlists)} playlists')

# saving playlist songs
for playlist in user_playlists:
    logging.info(f"Loading playlist: {playlist['name']} ({playlist['tracks']['total']} songs)")
    playlist_tracks = spotify.list(playlist['tracks']['href'], {'limit': 100})
    logging.info(f"Saving {playlist['name']}'s songs")
    save_track(f"done/Playlists/{playlist['name']}.csv", playlist_tracks)


# following artist data
logging.info('Loading followed artists...')
following_artist_data = spotify.list_artists('me/following', {'type': 'artist', 'limit': 50})
logging.info(f'Found {len(following_artist_data)} artists')
save_artist('done/Artists.csv', following_artist_data)


# saved album data
logging.info('Loading saved albums...')
saved_album_data = spotify.list('me/albums', {'limit': 50})
logging.info(f'Found {len(saved_album_data)} albums')
save_album('done/Albums.csv', saved_album_data)


# saved album data
logging.info('Loading saved podcasts...')
saved_podcast_data = spotify.list('me/shows', {'limit': 50})
logging.info(f'Found {len(saved_podcast_data)} podcasts')
save_podcast('done/Podcasts.csv', saved_podcast_data)


# save saved podcast episodes
logging.info('Loading saved podcast episodes...')
saved_episode_data = spotify.list("me/episodes", {'limit': 50})
logging.info('Saving episodes')
save_episode('done/Episodes.csv', saved_episode_data)
