import requests
import urllib.parse
from typing import List, Dict, Any

# This would be loaded from a config file in a real application
# For now, it's here for demonstration.
BASE_URL = "http://127.0.0.1:5000" 

def _make_request(endpoint: str, api_key: str, params: Dict = None) -> Dict | List:
    """A helper function to make authenticated requests to the backend."""
    headers = {
        "X-API-KEY": api_key  # Example of how an API key would be used
    }
    
    url = f"{BASE_URL}{endpoint}"
    if params:
        url += f"?{urllib.parse.urlencode(params)}"
        
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error calling backend: {e}")
        # Fallback to an empty response
        return [] if endpoint == "/markets/" else {}

# --- Tool Definitions ---

def query_markets(api_key: str, params: Dict) -> List[Dict[str, Any]]:
    """Tool to query the /markets endpoint with filters, sorting, and pagination."""
    return _make_request("/markets/", api_key, params)

def get_market_stats(api_key: str) -> Dict[str, Any]:
    """Tool to get overall market statistics."""
    return _make_request("/stats/market", api_key)

def get_category_stats(api_key: str) -> List[Dict[str, Any]]:
    """Tool to get statistics for all categories."""
    return _make_request("/stats/category", api_key)
