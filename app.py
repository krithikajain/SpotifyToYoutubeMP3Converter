from flask import Flask, request, url_for, session, redirect
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time  # Import time module for token expiration checks
from flask import render_template  # Import render_template

app = Flask(__name__)

# Configuration
app.secret_key = "abc123cdef0000"
app.config['SESSION_COOKIE_NAME'] = 'My Cookie'
TOKEN_INFO = "token_info"


def create_spotify_oauth():
    """
    Creates SpotifyOAuth object with client credentials and scope.
    """
    return SpotifyOAuth(
        client_id=os.getenv("CLIENT_ID"),
        client_secret=os.getenv("CLIENT_SECRET"),
        redirect_uri=url_for('redirectPage', _external=True),
        scope="user-library-read"
    )


def get_token():
    """
    Retrieves and refreshes the access token if necessary.
    """
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        raise Exception("User not logged in or token not available")
    
    now = int(time.time())
    is_expired = token_info['expires_at'] - now < 60

    if is_expired:
        sp_oauth = create_spotify_oauth()
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        session[TOKEN_INFO] = token_info  # Save updated token in session
    
    return token_info


@app.route('/')
def login():
    """
    Login route that redirects the user to Spotify's authorization page.
    """
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return render_template('home.html', title="Home")


@app.route('/redirect')
def redirectPage():
    """
    Callback route after Spotify login.
    Exchanges the authorization code for an access token.
    """
    sp_oauth = create_spotify_oauth()
    session.clear()
    code = request.args.get('code')

    if not code:
        return "Authorization code not found in redirect request", 400

    token_info = sp_oauth.get_access_token(code)
    session[TOKEN_INFO] = token_info
    return redirect(url_for('getTracks', _external=True))


@app.route('/getTracks')
def getTracks():
    """
    Retrieves and displays the user's saved tracks from Spotify.
    """
    try:
        token_info = get_token()
    except Exception as e:
        print("Error:", e)
        return redirect("/")
    
    sp = spotipy.Spotify(auth=token_info['access_token'])
    results = sp.current_user_saved_tracks(limit=20)  # Fetch 20 saved tracks
    tracks = [
            {"name": item['track']['name'], "artist": item['track']['artists'][0]['name']}
            for item in results['items']]
    return render_template('tracks.html', title="Saved Tracks", tracks=tracks)

@app.route('/playlists')
def playlists():
    """ Display the user's spotify playlists. """
    try:
        token_info = get_token()
    except Exception as e:
        print("Error: ", e)
        return redirect("/")
    
    sp = spotipy.Spotify(auth=token_info['access_token'])
    results = sp.current_user_playlists(limit=20)
    playlists = [
        {"name": playlist['name'],"tracks": playlist['tracks']['total']}
        for playlist in results['items']
    ]
    return render_template('playlists.html', title="Playlists", playlists=playlists)




if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
