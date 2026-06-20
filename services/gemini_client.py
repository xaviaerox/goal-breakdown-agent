import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if api_key:
    # Initialize the client with the API key
    client = genai.Client(api_key=api_key)
    _is_configured = True
else:
    client = None
    _is_configured = False

def is_gemini_configured() -> bool:
    """
    Returns True if the Gemini API key is configured in the environment.
    """
    return _is_configured

def call_gemini(prompt: str, system_instruction: str = None) -> str:
    """
    Calls the Gemini 2.5 Flash model with the given prompt and optional system instructions.
    Raises RuntimeError if the client is not configured or if the API call fails.
    """
    if not _is_configured or client is None:
        raise RuntimeError("Gemini API Key is missing. Configure GEMINI_API_KEY in your environment.")
        
    try:
        config = types.GenerateContentConfig(
            system_instruction=system_instruction
        ) if system_instruction else None
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=config
        )
        return response.text
    except Exception as e:
        raise RuntimeError(f"Gemini API call failed: {str(e)}")

