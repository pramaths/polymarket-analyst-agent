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

def query_markets(api_key: str, params: Dict) -> List[Dict[str, Any]]:
    return _make_request("/markets/", api_key, params)

def get_market_stats(api_key: str) -> Dict[str, Any]:
    return _make_request("/stats/market", api_key)

def get_category_stats(api_key: str) -> List[Dict[str, Any]]:
    return _make_request("/stats/category", api_key)

def analyze_market(api_key: str, market_slug: str) -> str:
    """Get AI analysis for a specific market"""
    result = _make_request("/analyze/market", api_key, method="POST", data={"slug": market_slug})
    if "error" in result:
        return f"Error: {result['error']}"
    return result.get("analysis", "No analysis available")

def analyze_election(api_key: str, market_slug: str, market_question: str) -> str:
    """Get election analysis for a specific market"""
    result = _make_request("/analyze/election", api_key, method="POST", data={"slug": market_slug, "question": market_question})
    if "error" in result:
        return f"Error: {result['error']}"
    return result.get("analysis", "No analysis available")

def get_recommendations(api_key: str, target_slug: str) -> List[str]:
    """Get market recommendations using MeTTa reasoning"""
    result = _make_request("/recommendations", api_key, method="POST", data={"slug": target_slug})
    if "error" in result:
        return []
    return result.get("recommendations", [])

# -------------------- Polymarket proxied endpoints --------------------

def polymarket_events(api_key: str, params: Dict | None = None) -> Dict | List:
    return _make_request("/polymarket/events", api_key, params or {})


def polymarket_markets_above_volume(api_key: str, min_volume: float, limit_fetch: int = 500) -> List[Dict[str, Any]]:
    params = {"min_volume": min_volume, "limit_fetch": limit_fetch}
    return _make_request("/polymarket/markets/above-volume", api_key, params)


def polymarket_positions(api_key: str, user: str, limit: int = 100, sortBy: str | None = None, sortDirection: str | None = None) -> Dict | List:
    params: Dict[str, Any] = {"user": user, "limit": limit}
    if sortBy:
        params["sortBy"] = sortBy
    if sortDirection:
        params["sortDirection"] = sortDirection
    return _make_request("/polymarket/positions", api_key, params)


def polymarket_trades(api_key: str, user: str, limit: int = 100, takerOnly: bool = True, filterType: str = "CASH") -> Dict | List:
    params: Dict[str, Any] = {"user": user, "limit": limit, "takerOnly": str(takerOnly).lower(), "filterType": filterType}
    return _make_request("/polymarket/trades", api_key, params)


def polymarket_holders(api_key: str, limit: int = 100, minBalance: str | None = None, market: str | None = None) -> Dict | List:
    params: Dict[str, Any] = {"limit": limit}
    if minBalance is not None:
        params["minBalance"] = minBalance
    if market is not None:
        params["market"] = market
    return _make_request("/polymarket/holders", api_key, params)


def polymarket_closed_positions(api_key: str, user: str, limit: int = 50, sortBy: str | None = None, sortDirection: str | None = None) -> Dict | List:
    params: Dict[str, Any] = {"user": user, "limit": limit}
    if sortBy:
        params["sortBy"] = sortBy
    if sortDirection:
        params["sortDirection"] = sortDirection
    return _make_request("/polymarket/closed-positions", api_key, params)


def polymarket_trader_details(api_key: str, address: str, positions_limit: int = 100, trades_limit: int = 100, closed_limit: int = 50) -> Dict | List:
    params = {"positions_limit": positions_limit, "trades_limit": trades_limit, "closed_limit": closed_limit}
    # Path param included inside endpoint; _make_request handles query, not path; use requests directly
    endpoint = f"/polymarket/trader/{address}"
    return _make_request(endpoint, api_key, params)


def polymarket_ai_yesno(api_key: str, yes_price: float | None = None, eventId: str | None = None, slug: str | None = None) -> Dict:
    body: Dict[str, Any] = {}
    if yes_price is not None:
        body["yesPrice"] = yes_price
    if eventId is not None:
        body["eventId"] = eventId
    if slug is not None:
        body["slug"] = slug
    return _make_request("/polymarket/ai/yesno", api_key, method="POST", data=body)


# -------------------- Agent endpoint --------------------

def agent_ask(api_key: str, query: str, execute: bool = True, session_id: str | None = None, fmt: str = "text") -> Dict | List:
    params = {"execute": str(execute).lower(), "fmt": fmt}
    payload = {"query": query}
    if session_id:
        payload["session_id"] = session_id
    return _make_request("/agent/ask", api_key, params=params, method="POST", data=payload)
