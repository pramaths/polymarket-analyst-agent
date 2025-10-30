import requests
import urllib.parse
from typing import List, Dict, Any
from config import BACKEND_URL

def _make_request(endpoint: str, api_key: str, params: Dict = None, method: str = "GET", data: Dict = None) -> Dict | List:
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }
    
    url = f"{BACKEND_URL}{endpoint}"
    # Always encode params into the URL, regardless of method
    if params:
        url += f"?{urllib.parse.urlencode(params)}"
        
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error calling backend: {e}")
        return {}

def agent_ask(api_key: str, query: str, execute: bool = True, session_id: str | None = None, fmt: str = "text") -> Dict | List:
    params = {"execute": str(execute).lower(), "fmt": fmt}
    payload = {"query": query}
    if session_id:
        payload["session_id"] = session_id
    return _make_request("/agent/ask", api_key, params=params, method="POST", data=payload)
