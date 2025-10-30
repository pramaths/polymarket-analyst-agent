from typing import Any, Dict, Optional, List
from fastapi import APIRouter, Query, Body
from fastapi.responses import PlainTextResponse
from starlette.concurrency import run_in_threadpool

from .polymarket_client import (
    get_events,
    get_events_normalized,
    get_markets_normalized,
    get_positions,
    get_trades,
    get_trades_by_condition,
    get_holders,
    get_closed_positions,
    markets_above_volume,
    summarize_trader_details,
    infer_yes_no_from_price,
)


router = APIRouter(prefix="/polymarket", tags=["polymarket"])


def _to_float(value: Any) -> float:
    try:
        if isinstance(value, str):
            return float(value)
        if isinstance(value, (int, float)):
            return float(value)
    except Exception:
        return 0.0
    return 0.0


def _first(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    return items[0] if items else {}


def _summarize_event(ev: Dict[str, Any]) -> Dict[str, Any]:
    markets = ev.get("markets") if isinstance(ev.get("markets"), list) else []
    m0 = _first(markets or [])

    title = ev.get("title") or ev.get("question") or m0.get("question")
    slug = ev.get("slug") or m0.get("slug")
    category = ev.get("category") or m0.get("category")

    vol = (
        ev.get("volumeNum")
        or ev.get("volume")
        or (ev.get("pricing") or {}).get("volume")
        or m0.get("volumeNum")
        or m0.get("volume")
    )
    liq = (
        ev.get("liquidityNum")
        or ev.get("liquidity")
        or (ev.get("pricing") or {}).get("liquidity")
        or m0.get("liquidityNum")
        or m0.get("liquidity")
    )
    end_date = ev.get("endDate") or ev.get("endDateIso") or m0.get("endDate")

    return {
        "title": title,
        "slug": slug,
        "category": category,
        "volume": _to_float(vol),
        "liquidity": _to_float(liq),
        "endDate": end_date,
    }


def _summarize_events_payload(raw: Any) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    if isinstance(raw, list):
        events = [x for x in raw if isinstance(x, dict)]
    elif isinstance(raw, dict):
        events = raw.get("data") or raw.get("events") or []
        if isinstance(events, dict):
            events = [events]
        events = [x for x in events if isinstance(x, dict)]
    summarized = [_summarize_event(e) for e in events]
    summarized.sort(key=lambda x: x.get("volume") or 0.0, reverse=True)
    return summarized


def _format_events_text(rows: List[Dict[str, Any]]) -> str:
    lines: List[str] = ["Top markets:"]
    for i, r in enumerate(rows[:5], 1):
        title_or_slug = r.get('title') or r.get('slug') or ''
        slug = r.get('slug') or ''
        cat = r.get('category') or ''
        vol = r.get('volume') or 0
        liq = r.get('liquidity') or 0
        endd = r.get('endDate') or ''
        lines.append(
            f"\n{i}. {title_or_slug}\n"
            f"   slug: {slug}\n"
            f"   category: {cat}\n"
            f"   volume: ${vol:,.0f}\n"
            f"   liquidity: ${liq:,.0f}\n"
            f"   end: {endd}"
        )
    return "\n".join(lines) + "\n"


@router.get("/events")
async def list_events(
    ascending: bool = Query(False),
    related_tags: bool = Query(True),
    start_date_max: Optional[str] = Query(None, description="ISO8601 date-time"),
    extra: Optional[str] = Query(None, description="Additional raw query, e.g. key1=val&key2=val"),
):
    params: Dict[str, Any] = {
        "limit": "10",  # fetch enough, we will always return 5
        "ascending": str(ascending).lower(),
        "related_tags": str(related_tags).lower(),
    }
    if start_date_max:
        params["start_date_max"] = start_date_max
    if extra:
        for kv in extra.split("&"):
            if "=" in kv:
                k, v = kv.split("=", 1)
                params[k] = v
    normalized = await run_in_threadpool(get_events_normalized, params)
    # Always return only 5 items
    # Choose top 5 by volume if available
    def _vol_key(ev: Dict[str, Any]) -> float:
        return float((ev.get("financials") or {}).get("liquidity") or 0.0)
    # Prefer sorting by liquidity if volume24hr may be 0 frequently
    sorted_list = sorted(normalized, key=_vol_key, reverse=True)
    return sorted_list[:5]


@router.get("/positions")
async def list_positions(
    sizeThreshold: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    sortBy: Optional[str] = None,
    sortDirection: Optional[str] = None,
    user: Optional[str] = None,
):
    params: Dict[str, Any] = {"limit": str(limit)}
    if sizeThreshold is not None:
        params["sizeThreshold"] = sizeThreshold
    if sortBy is not None:
        params["sortBy"] = sortBy
    if sortDirection is not None:
        params["sortDirection"] = sortDirection
    if user is not None:
        params["user"] = user
    return await run_in_threadpool(get_positions, params)


@router.get("/trades")
async def list_trades(
    limit: int = Query(100, ge=1, le=1000),
    takerOnly: Optional[bool] = None,
    filterType: Optional[str] = None,
    user: Optional[str] = None,
):
    params: Dict[str, Any] = {"limit": str(limit)}
    if takerOnly is not None:
        params["takerOnly"] = str(takerOnly).lower()
    if filterType is not None:
        params["filterType"] = filterType
    if user is not None:
        params["user"] = user
    return await run_in_threadpool(get_trades, params)


@router.get("/holders")
async def list_holders(
    limit: int = Query(100, ge=1, le=1000),
    minBalance: Optional[str] = None,
    market: Optional[str] = Query(None, description="Optional market identifier if supported by upstream API"),
):
    params: Dict[str, Any] = {"limit": str(limit)}
    if minBalance is not None:
        params["minBalance"] = minBalance
    if market is not None:
        params["market"] = market
    return await run_in_threadpool(get_holders, params)


@router.get("/closed-positions")
async def list_closed_positions(
    limit: int = Query(50, ge=1, le=1000),
    sortBy: Optional[str] = None,
    sortDirection: Optional[str] = None,
    user: Optional[str] = None,
):
    params: Dict[str, Any] = {"limit": str(limit)}
    if sortBy is not None:
        params["sortBy"] = sortBy
    if sortDirection is not None:
        params["sortDirection"] = sortDirection
    if user is not None:
        params["user"] = user
    return await run_in_threadpool(get_closed_positions, params)


@router.get("/markets/above-volume", response_class=PlainTextResponse)
async def list_markets_above_volume(
    min_volume: float = Query(..., ge=0.0, description="Minimum USD volume to include"),
    limit_fetch: int = Query(500, ge=1, le=1000),
):
    raw_list = await run_in_threadpool(markets_above_volume, min_volume, limit_fetch)
    rows = _summarize_events_payload(raw_list)
    return _format_events_text(rows)


@router.get("/markets")
async def list_markets(
    limit: int = Query(10, ge=1, le=100),
):
    normalized = await run_in_threadpool(get_markets_normalized, {"limit": str(limit)})
    # Always return only essential fields (already normalized), trimmed to 5
    return normalized[:5]


@router.get("/market/{condition_id}/trades")
async def trades_for_condition(
    condition_id: str,
    limit: int = Query(100, ge=1, le=1000),
):
    # Proxy to trades with condition filter (best-effort)
    return await run_in_threadpool(get_trades_by_condition, condition_id, limit)


@router.get("/trader/{address}")
async def trader_details(
    address: str,
    positions_limit: int = Query(100, ge=1, le=1000),
    trades_limit: int = Query(100, ge=1, le=1000),
    closed_limit: int = Query(50, ge=1, le=1000),
):
    return await run_in_threadpool(
        summarize_trader_details,
        address,
        {"limit": str(positions_limit)},
        {"limit": str(trades_limit)},
        {"limit": str(closed_limit)},
    )


@router.post("/ai/yesno")
async def ai_yes_no(
    payload: Dict[str, Any] = Body(..., example={"yesPrice": 0.62}),
):
    yes_price: Optional[float] = None

    # direct price if provided
    if "yesPrice" in payload:
        yes_price = payload.get("yesPrice")

    # attempt to fetch price from an event if identifiers provided
    if yes_price is None and ("eventId" in payload or "slug" in payload):
        params: Dict[str, Any] = {"limit": "10"}
        if "eventId" in payload:
            params["ids"] = str(payload["eventId"])  # best-effort, depends on upstream support
        if "slug" in payload:
            params["slug"] = str(payload["slug"])    # best-effort
        events_response = await run_in_threadpool(get_events, params)
        events = events_response if isinstance(events_response, list) else events_response.get("data") or events_response.get("events") or []
        if events:
            event = events[0]
            # Try multiple common locations for yes price
            pricing = event.get("pricing") or {}
            yes_price = pricing.get("outcomeYesPrice")
            if yes_price is None:
                # try other common keys
                yes_price = pricing.get("yesPrice") or event.get("yesPrice")

    decision, meta = await run_in_threadpool(infer_yes_no_from_price, yes_price)
    return {"decision": decision, "meta": meta}


