from flask import Flask, request, redirect
import requests
from dotenv import load_dotenv
import os
import urllib


app = Flask(__name__)

load_dotenv()

#  Client Keys
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

# Server-side
port = 8888
redirect_uri = f"http://localhost:8888/callback"
scope = "playlist-read-private playlist-read-collaborative user-library-read user-follow-read"


@app.route("/")
def index():
    auth_url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode({
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": scope,
        "client_id": CLIENT_ID
    })

    return redirect(auth_url)


@app.route("/callback/")
def callback():
    code_payload = {
        "grant_type": "authorization_code",
        "code": str(request.args['code']),
        "redirect_uri": redirect_uri,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }

    resp = requests.post(
        "https://accounts.spotify.com/api/token",
        data=code_payload)

    return resp.json()["refresh_token"]


if __name__ == "__main__":
    app.run(debug=True, port=port)