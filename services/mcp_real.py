import os
import sys
import json
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

def ensure_credentials_file():
    """
    Ensures that the credentials.json file is correctly formatted and located
    in the path expected by the Google Workspace MCP server:
    C:\\Users\\<username>\\.google-workspace-mcp\\credentials.json
    """
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise ValueError("Missing GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET in .env file.")
        
    home_dir = os.path.expanduser("~")
    target_dir = os.path.join(home_dir, ".google-workspace-mcp")
    os.makedirs(target_dir, exist_ok=True)
    
    target_file = os.path.join(target_dir, "credentials.json")
    
    # Standard OAuth installed credentials structure
    creds_data = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": ["http://localhost"]
        }
    }
    
    with open(target_file, "w", encoding="utf-8") as f:
        json.dump(creds_data, f, indent=2)

def run_async(coro):
    """
    Runs the given coroutine synchronously, handling existing event loops
    and thread contexts safely.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Only apply nest_asyncio if there is already a running loop
        import nest_asyncio
        nest_asyncio.apply()
        return loop.run_until_complete(coro)
    else:
        # Standard asyncio.run which handles creating and cleaning up the loop
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        return asyncio.run(coro)

async def async_create_calendar_event(title: str, start_time: str, end_time: str, description: str = None) -> dict:
    """
    Connects to the Google Workspace MCP server using python mcp SDK
    and creates a calendar event on your Google Calendar.
    """
    results = await async_create_calendar_events([{
        "title": title,
        "start_time": start_time,
        "end_time": end_time,
        "description": description
    }])
    if not results:
        raise RuntimeError("No response from Google Workspace MCP server batch.")
    res = results[0]
    if "failed" in res["status"]:
        raise RuntimeError(res["status"])
    return {"summary": title, "result": res["result"]}

async def async_create_calendar_events(events_list: list) -> list:
    """
    Connects to the Google Workspace MCP server using python mcp SDK
    and creates multiple calendar events sequentially in a single session.
    """
    ensure_credentials_file()
    
    # Use cmd.exe /c npx on Windows to avoid subprocess execution issues
    if sys.platform == "win32":
        command = "cmd.exe"
        args = ["/c", "npx", "-y", "@alanxchen/google-workspace-mcp"]
    else:
        command = "npx"
        args = ["-y", "@alanxchen/google-workspace-mcp"]
        
    # Configure MCP Server parameters, copying parent environment to preserve paths
    env = os.environ.copy()
    server_params = StdioServerParameters(
        command=command,
        args=args,
        env=env
    )
    
    results = []
    # Start the stdio connection to the server
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            
            for ev in events_list:
                title = ev["title"]
                start_time = ev["start_time"]
                end_time = ev["end_time"]
                description = ev.get("description")
                
                # Google Workspace MCP server 'create_event' tool arguments
                arguments = {
                    "calendarId": "primary",
                    "summary": title,
                    "start": start_time,
                    "end": end_time
                }
                if description:
                    arguments["description"] = description
                    
                print(f"[Real MCP] Calling create_event tool for '{title}'...", file=sys.stderr)
                try:
                    result = await session.call_tool("create_event", arguments=arguments)
                    
                    # Parse result
                    if not result.content or len(result.content) == 0:
                        raise ValueError("Received empty result from Google Workspace MCP server.")
                        
                    response_text = result.content[0].text
                    print(f"[Real MCP] Server response: {response_text}", file=sys.stderr)
                    
                    if "Error" in response_text or "credentials" in response_text.lower():
                        raise RuntimeError(response_text)
                        
                    results.append({"title": title, "status": "success", "result": response_text})
                except Exception as e:
                    results.append({"title": title, "status": f"failed: {str(e)}", "result": ""})
                    
    # Force garbage collection of subprocess transport/sockets before event loop exits
    import gc
    gc.collect()
    
    return results

def create_real_event(title: str, start_time: str, end_time: str, description: str = None) -> dict:
    """
    Synchronous wrapper to call the async Google Workspace MCP event creation.
    """
    return run_async(async_create_calendar_event(title, start_time, end_time, description))

def create_real_events(events_list: list) -> list:
    """
    Synchronous wrapper to call the async Google Workspace MCP events creation.
    """
    return run_async(async_create_calendar_events(events_list))
