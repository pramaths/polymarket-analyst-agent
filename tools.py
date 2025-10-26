import requests
import urllib.parse
from typing import List, Dict, Any

BASE_URL = "http://127.0.0.1:5000" 

def _make_request(endpoint: str, api_key: str, params: Dict = None) -> Dict | List:
    headers = {
        "X-API-KEY": api_key
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
        return [] if endpoint == "/markets/" else {}

def query_markets(api_key: str, params: Dict) -> List[Dict[str, Any]]:
    return _make_request("/markets/", api_key, params)

def get_market_stats(api_key: str) -> Dict[str, Any]:
    return _make_request("/stats/market", api_key)

def get_category_stats(api_key: str) -> List[Dict[str, Any]]:
    return _make_request("/stats/category", api_key)
