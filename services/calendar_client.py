import os
import time
import requests
import sys

def refresh_access_token(client_id: str, client_secret: str, refresh_token: str) -> dict:
    """
    Refreshes the Google OAuth access token using the refresh token.
    Returns a dictionary containing access_token and expires_at, or raises an exception.
    """
    url = "https://oauth2.googleapis.com/token"
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }
    
    response = requests.post(url, data=payload)
    if response.status_code != 200:
        raise RuntimeError(f"Failed to refresh access token: {response.text}")
        
    data = response.json()
    access_token = data.get("access_token")
    expires_in = data.get("expires_in", 3600)
    expires_at = time.time() + expires_in
    
    return {
        "access_token": access_token,
        "expires_at": expires_at
    }

def create_calendar_events_direct(events_list: list, access_token: str) -> list:
    """
    Creates multiple calendar events sequentially on the user's primary calendar
    using their Google OAuth access token.
    Returns a list of dictionaries with creation status.
    """
    url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    results = []
    for ev in events_list:
        title = ev["title"]
        start_time = ev["start_time"]
        end_time = ev["end_time"]
        description = ev.get("description", "")
        
        payload = {
            "summary": title,
            "description": description,
            "start": {
                "dateTime": start_time
            },
            "end": {
                "dateTime": end_time
            }
        }
        
        print(f"[OAuth Sync] Creating event: '{title}'...", file=sys.stderr)
        try:
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code in [200, 201]:
                res_data = response.json()
                results.append({
                    "title": title,
                    "status": "success",
                    "result": res_data.get("id", "success")
                })
            else:
                results.append({
                    "title": title,
                    "status": f"failed: HTTP {response.status_code} - {response.text}",
                    "result": ""
                })
        except Exception as e:
            results.append({
                "title": title,
                "status": f"failed: {str(e)}",
                "result": ""
            })
            
    return results
