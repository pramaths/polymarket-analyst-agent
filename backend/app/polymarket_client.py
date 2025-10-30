from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode
import requests


GAMMA_BASE_URL = "https://gamma-api.polymarket.com"
DATA_BASE_URL = "https://data-api.polymarket.com"
CLOB_BASE_URL = "https://clob.polymarket.com"


class PolymarketAPIError(Exception):
    pass


def _request_json(base_url: str, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
    response = requests.get(url, params=params or {}, timeout=30)
    if response.status_code != 200:
        raise PolymarketAPIError(f"HTTP {response.status_code} for {url}?{urlencode(params or {})}")
    try:
        return response.json()
    except Exception as exc:
        raise PolymarketAPIError(f"Failed to parse JSON for {url}") from exc


# Gamma API wrappers
def get_events(params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return _request_json(GAMMA_BASE_URL, "/events", params)


def get_markets(params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return _request_json(GAMMA_BASE_URL, "/markets", params)


# Data API wrappers
def get_positions(params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return _request_json(DATA_BASE_URL, "/positions", params)


def get_trades(params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return _request_json(DATA_BASE_URL, "/trades", params)


def get_holders(params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return _request_json(DATA_BASE_URL, "/holders", params)


def get_closed_positions(params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return _request_json(DATA_BASE_URL, "/closed-positions", params)


def get_order_book(condition_id: str) -> Dict[str, Any]:
    """Get the order book for a given market condition."""
    return _request_json(CLOB_BASE_URL, f"/markets/{condition_id}/orders")


def get_top_holders(condition_id: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get top 5 holders for YES and NO outcomes for a given market,
    sorted by amount.
    """
    raw_data = get_holders(params={"market": condition_id})

    if not isinstance(raw_data, list):
        return {"yes": [], "no": []}

    yes_holders = []
    no_holders = []

    for token_data in raw_data:
        holders = token_data.get("holders", [])
        if not isinstance(holders, list):
            continue
        
        for holder in holders:
            outcome_index = holder.get("outcomeIndex")
            
            minimal_holder = {
                "address": holder.get("proxyWallet"),
                "username": holder.get("name") or holder.get("pseudonym"),
                "amount": holder.get("amount", 0)
            }

            if outcome_index == 1:
                yes_holders.append(minimal_holder)
            elif outcome_index == 0:
                no_holders.append(minimal_holder)

    yes_holders.sort(key=lambda x: x.get("amount", 0), reverse=True)
    no_holders.sort(key=lambda x: x.get("amount", 0), reverse=True)

    return {
        "yes": yes_holders[:5],
        "no": no_holders[:5]
    }


def get_top_traders_by_pnl() -> List[Dict[str, Any]]:
    """
    Get top traders by PNL from the top 100 positions.
    Returns a summary of their total PNL and most profitable market.
    """
    from collections import defaultdict

    positions = get_positions(params={
        "limit": "100",
        "sortBy": "CASHPNL",
        "sortDirection": "DESC"
    })

    if not isinstance(positions, list):
        return []

    trader_pnl = defaultdict(lambda: {'total_pnl': 0, 'most_profitable_market': None, 'max_pnl': -float('inf'), 'username': None})

    for pos in positions:
        address = pos.get("proxyWallet")
        pnl = pos.get("cashPnl", 0)
        market_title = pos.get("title")
        username = pos.get("name") or pos.get("pseudonym")

        if not address:
            continue

        trader_pnl[address]['total_pnl'] += pnl
        if not trader_pnl[address]['username'] and username:
            trader_pnl[address]['username'] = username
        
        if pnl > trader_pnl[address]['max_pnl']:
            trader_pnl[address]['max_pnl'] = pnl
            trader_pnl[address]['most_profitable_market'] = market_title

    summary = []
    for address, data in trader_pnl.items():
        summary.append({
            "address": address,
            "username": data['username'],
            "total_pnl": data['total_pnl'],
            "most_profitable_market": data['most_profitable_market']
        })

    summary.sort(key=lambda x: x.get("total_pnl", 0), reverse=True)

    return summary[:5]


# Helper utilities for common queries
def markets_above_volume(
    min_volume_usd: float,
    limit_fetch: int = 500,
) -> List[Dict[str, Any]]:
    """
    Fetch events and return those whose volume-like fields exceed threshold.
    Since Polymarket event schemas can vary, we look for common keys.
    """
    raw = get_events({
        "limit": str(limit_fetch),
        "ascending": "false",
        "related_tags": "true",
    })
    events = raw if isinstance(raw, list) else raw.get("data") or raw.get("events") or []

    def extract_volumes(event: Dict[str, Any]) -> List[float]:
        candidates: List[float] = []
        for key, value in event.items():
            if not isinstance(value, (int, float)):
                continue
            # include numeric fields that look like volume
            lowered = key.lower()
            if "volume" in lowered or lowered in {"vol", "vol24h", "volume24h"}:
                candidates.append(float(value))
        # also check nested pricing-like dicts
        for nested_key in ("pricing", "stats", "metrics"):
            nested = event.get(nested_key)
            if isinstance(nested, dict):
                for k, v in nested.items():
                    if isinstance(v, (int, float)) and ("volume" in k.lower() or k.lower() in {"vol", "vol24h", "volume24h"}):
                        candidates.append(float(v))
        return candidates

    qualified: List[Dict[str, Any]] = []
    for ev in events:
        volumes = extract_volumes(ev)
        if any(v >= min_volume_usd for v in volumes):
            qualified.append(ev)
    return qualified


# -------------------- Normalization helpers --------------------

def _safe_str(val: Any) -> str:
    try:
        if val is None:
            return ""
        return str(val)
    except Exception:
        return ""


def _safe_float(val: Any) -> float:
    try:
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, str):
            return float(val)
    except Exception:
        return 0.0
    return 0.0


def _normalize_event(ev: Dict[str, Any]) -> Dict[str, Any]:
    markets = ev.get("markets") if isinstance(ev.get("markets"), list) else []
    normalized_markets: List[Dict[str, Any]] = []
    for m in markets or []:
        normalized_markets.append({
            "id": _safe_str(m.get("id")),
            "slug": _safe_str(m.get("slug")),
            "title": _safe_str(m.get("question") or m.get("title")),
            "liquidity": _safe_float(m.get("liquidityNum") or m.get("liquidity")),
            "volume": _safe_float(m.get("volumeNum") or m.get("volume")),
        })

    tags = []
    # upstream sometimes has a tags array or nested tag objects
    if isinstance(ev.get("tags"), list):
        for t in ev.get("tags"):
            if isinstance(t, dict):
                lbl = t.get("label") or t.get("name") or t.get("slug")
                if lbl:
                    tags.append(_safe_str(lbl))
            else:
                tags.append(_safe_str(t))

    return {
        "id": _safe_str(ev.get("id")),
        "slug": _safe_str(ev.get("slug")),
        "title": _safe_str(ev.get("title") or ev.get("question")),
        "subtitle": _safe_str(ev.get("ticker")),  # no strict subtitle upstream; using ticker-like text
        "description": _safe_str(ev.get("description")),
        "ticker": _safe_str(ev.get("ticker")),
        "category": _safe_str(ev.get("category")),
        "subcategory": _safe_str(ev.get("subcategory")),
        "tags": tags,
        "status": {
            "active": bool(ev.get("active", False)),
            "closed": bool(ev.get("closed", False)),
        },
        "timestamps": {
            "startDate": _safe_str(ev.get("startDate")),
            "endDate": _safe_str(ev.get("endDate") or ev.get("endDateIso")),
        },
        "financials": {
            "liquidity": _safe_float(ev.get("liquidityNum") or ev.get("liquidity")),
            "volume24hr": _safe_float(ev.get("volume24hr")),
        },
        "markets": normalized_markets,
        "media": {
            "imageOptimized": {
                "url": _safe_str(ev.get("image") or ev.get("icon")),
            }
        },
    }


def get_events_normalized(params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    raw = get_events(params)
    events: List[Dict[str, Any]] = []
    if isinstance(raw, list):
        events = [x for x in raw if isinstance(x, dict)]
    elif isinstance(raw, dict):
        events = raw.get("data") or raw.get("events") or []
        if isinstance(events, dict):
            events = [events]
        events = [x for x in events if isinstance(x, dict)]
    normalized = [_normalize_event(e) for e in events]
    return normalized


# -------------------- Markets normalization --------------------

def _normalize_market(m: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": _safe_str(m.get("id")),
        "question": _safe_str(m.get("question") or m.get("title")),
        "conditionId": _safe_str(m.get("conditionId")),
        "slug": _safe_str(m.get("slug")),
        "category": _safe_str(m.get("category")),
        "liquidity": _safe_float(m.get("liquidityNum") or m.get("liquidity")),
        "volume": _safe_float(m.get("volumeNum") or m.get("volume")),
        "startDate": _safe_str(m.get("startDate") or m.get("startDateIso")),
        "endDate": _safe_str(m.get("endDate") or m.get("endDateIso")),
        "active": bool(m.get("active", False)),
        "closed": bool(m.get("closed", False)),
        # keep 8-10 fields max; skip the rest
    }


def get_markets_normalized(params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    raw = get_markets(params)
    markets: List[Dict[str, Any]] = []
    if isinstance(raw, list):
        markets = [x for x in raw if isinstance(x, dict)]
    elif isinstance(raw, dict):
        markets = raw.get("data") or raw.get("markets") or []
        if isinstance(markets, dict):
            markets = [markets]
        markets = [x for x in markets if isinstance(x, dict)]
    return [_normalize_market(m) for m in markets]


def get_trades_by_condition(condition_id: str, limit: int = 100) -> Dict[str, Any]:
    # Best-effort: pass condition or market selector if supported by upstream
    params: Dict[str, Any] = {
        "limit": str(limit),
        "filterType": "CASH",
    }
    # Common parameter names tried
    params["conditionId"] = condition_id
    return get_trades(params)


def summarize_trader_details(address: str, positions_params: Optional[Dict[str, Any]] = None,
                              trades_params: Optional[Dict[str, Any]] = None,
                              closed_positions_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Aggregate a trader's info from positions, trades, and closed-positions.
    """
    base_positions_params = {"user": address}
    if positions_params:
        base_positions_params.update(positions_params)

    base_trades_params = {"user": address}
    if trades_params:
        base_trades_params.update(trades_params)

    base_closed_params = {"user": address}
    if closed_positions_params:
        base_closed_params.update(closed_positions_params)

    positions = get_positions(base_positions_params)
    trades = get_trades(base_trades_params)
    closed_positions = get_closed_positions(base_closed_params)

    return {
        "address": address,
        "positions": positions,
        "trades": trades,
        "closed_positions": closed_positions,
    }


def infer_yes_no_from_price(yes_price: Optional[float]) -> Tuple[str, Dict[str, Any]]:
    """
    Simple inference: YES if price > 0.5, NO if < 0.5, UNKNOWN otherwise.
    Returns (decision, meta)
    """
    if yes_price is None:
        return "UNKNOWN", {"reason": "Missing yes price"}
    try:
        price = float(yes_price)
    except Exception:
        return "UNKNOWN", {"reason": "Invalid yes price"}
    if price > 0.5:
        return "YES", {"threshold": 0.5, "yesPrice": price}
    if price < 0.5:
        return "NO", {"threshold": 0.5, "yesPrice": price}
    return "UNKNOWN", {"threshold": 0.5, "yesPrice": price}


