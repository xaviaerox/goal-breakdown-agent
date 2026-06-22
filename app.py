import os
import time
import requests
from flask import Flask, request, jsonify, session, redirect, url_for
from agent_runtime.runtime import ComposedAgentRuntime, AgentRuntimeError
from security.guardrails import GuardrailError

app = Flask(__name__, static_folder='static', static_url_path='')
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "capstone-agent-secret-key-192837")

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")

def get_user_access_token():
    """
    Retrieves the user's active Google OAuth access token from session.
    Refreshes it automatically if expired.
    Returns the token string, or None if the user is not authenticated.
    """
    access_token = session.get('google_access_token')
    if not access_token:
        return None
        
    expires_at = session.get('google_expires_at', 0)
    # If token is expired or expires in less than 60 seconds, refresh it
    if time.time() + 60 >= expires_at:
        refresh_token = session.get('google_refresh_token')
        if refresh_token and GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
            try:
                from services.calendar_client import refresh_access_token
                refreshed = refresh_access_token(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, refresh_token)
                session['google_access_token'] = refreshed['access_token']
                session['google_expires_at'] = refreshed['expires_at']
                return refreshed['access_token']
            except Exception as e:
                print(f"[OAuth Sync] Failed to refresh token: {str(e)}")
                # Clear invalid session tokens
                session.pop('google_access_token', None)
                return None
        else:
            return None
            
    return access_token

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/auth/login')
def auth_login():
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        return "GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET is missing from the environment.", 500
        
    redirect_uri = request.host_url.rstrip('/') + '/auth/callback'
    # Force HTTPS in production (non-localhost) environments
    if 'localhost' not in request.host and '127.0.0.1' not in request.host:
        redirect_uri = redirect_uri.replace('http://', 'https://')

    auth_url = (
        "https://accounts.google.com/o/oauth2/auth?"
        f"client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        "&response_type=code"
        "&scope=https://www.googleapis.com/auth/calendar.events%20https://www.googleapis.com/auth/userinfo.email"
        "&access_type=offline"
        "&prompt=consent"
    )
    return redirect(auth_url)

@app.route('/auth/callback')
def auth_callback():
    code = request.args.get('code')
    if not code:
        return "Missing authorization code from Google.", 400
        
    redirect_uri = request.host_url.rstrip('/') + '/auth/callback'
    # Force HTTPS in production (non-localhost) environments
    if 'localhost' not in request.host and '127.0.0.1' not in request.host:
        redirect_uri = redirect_uri.replace('http://', 'https://')
        
    token_url = "https://oauth2.googleapis.com/token"
    payload = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }
    
    response = requests.post(token_url, data=payload)
    if response.status_code != 200:
        return f"Failed to exchange authorization code: {response.text}", 400
        
    token_data = response.json()
    session['google_access_token'] = token_data.get('access_token')
    session['google_refresh_token'] = token_data.get('refresh_token') or session.get('google_refresh_token')
    session['google_expires_at'] = time.time() + token_data.get('expires_in', 3600)
    
    # Retrieve user's email for status visibility
    userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
    headers = {"Authorization": f"Bearer {token_data.get('access_token')}"}
    userinfo_res = requests.get(userinfo_url, headers=headers)
    if userinfo_res.status_code == 200:
        session['google_user_email'] = userinfo_res.json().get('email', '')
        
    return redirect('/')

@app.route('/auth/logout')
def auth_logout():
    session.clear()
    return redirect('/')

@app.route('/api/auth/status')
def api_auth_status():
    logged_in = 'google_access_token' in session
    email = session.get('google_user_email', '')
    return jsonify({
        "logged_in": logged_in,
        "email": email
    })

@app.route('/api/breakdown', methods=['POST'])
def api_breakdown():
    data = request.get_json() or {}
    goal = data.get('goal', '')
    deadline = data.get('deadline', '')
    availability = data.get('availability', '')
    sessions_pref = data.get('sessions', '')
    timezone_offset = data.get('timezone_offset', 'Z')
    
    # Get the user's OAuth access token from the session if logged in
    user_access_token = get_user_access_token()
    
    try:
        runtime = ComposedAgentRuntime()
        # Execute the agent planning & scheduling pipeline
        result = runtime.run(
            goal=goal,
            deadline=deadline,
            availability=availability,
            sessions_pref=sessions_pref,
            timezone_offset=timezone_offset,
            user_access_token=user_access_token
        )
        return jsonify({
            "status": "success",
            "data": result
        }), 200
    except GuardrailError as e:
        return jsonify({
            "status": "error",
            "message": f"Security Guardrail Blocked: {str(e)}"
        }), 400
    except AgentRuntimeError as e:
        return jsonify({
            "status": "error",
            "message": f"Agent Runtime Error: {str(e)}"
        }), 500
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"An unexpected error occurred: {str(e)}"
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True, threaded=False)


