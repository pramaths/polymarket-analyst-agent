import logging
import json
from typing import Any, Dict, Optional, List
from datetime import datetime
from fastapi import APIRouter, Body, Query
from starlette.concurrency import run_in_threadpool

from .memory import get_session_context, update_session_context
from .tool_planner import plan_with_tools
from .llm import asi_chat
from .polymarket_client import (
    get_markets_normalized,
    get_trades_by_condition,
    summarize_trader_details,
    get_order_book,
    get_top_holders,
    get_top_traders_by_pnl,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


router = APIRouter(prefix="/agent", tags=["agent"])


def _format_markets_text(markets: List[Dict[str, Any]]) -> str:
    if not markets:
        return "No markets found."
    lines = ["Top Markets:"]
    for i, market in enumerate(markets, 1):
        lines.append(
            f"\n{i}. {market.get('question')}\n"
            f"   ID: {market.get('conditionId')}\n"
            f"   Category: {market.get('category')}\n"
            f"   Volume: ${market.get('volume', 0):,.2f}\n"
            f"   Liquidity: ${market.get('liquidity', 0):,.2f}\n"
            f"   Ends: {market.get('endDate')}"
        )
    return "\n".join(lines)

def _format_trades_text(trades: List[Dict[str, Any]]) -> str:
    if not trades:
        return "No trades found for this market."
    
    title = trades[0].get('title', 'N/A')
    lines = [f"Recent Trades for '{title}':"]
    for i, trade in enumerate(trades[:10], 1): # show top 10
        ts_val = trade.get('timestamp', 0)
        ts = datetime.fromtimestamp(ts_val) if ts_val else datetime.now()
        lines.append(
            f"\n{i}. {ts.strftime('%Y-%m-%d %H:%M')}\n"
            f"   Side: {trade.get('side')}\n"
            f"   Outcome: {trade.get('outcome')}\n"
            f"   Size: {trade.get('size', 0):.2f}\n"
            f"   Price: ${trade.get('price', 0):.2f}\n"
            f"   Trader: {trade.get('proxyWallet')}"
        )
    return "\n".join(lines)

def _format_trader_details_text(details: Dict[str, Any]) -> str:
    if not details:
        return "No details found for this trader."
    
    pnl = details.get('pnl', {})
    total_pnl = pnl.get('all_time', 0)
    
    positions = details.get('positions', [])
    trades = details.get('trades', [])
    
    lines = [
        f"Trader Details for {details.get('address')}",
        f"All-time PNL: ${total_pnl:,.2f}",
        f"Total Volume: ${details.get('total_volume', 0):,.2f}",
        "\nRecent Positions:",
    ]
    if not positions:
        lines.append("  None")
    else:
        for pos in positions[:5]:
            lines.append(f"  - Market: '{pos.get('market_title', 'N/A')}', PNL: ${pos.get('pnl', 0):,.2f}")

    lines.append("\nRecent Trades:")
    if not trades:
        lines.append("  None")
    else:
        for trade in trades[:5]:
            ts_val = trade.get('timestamp', 0)
            ts = datetime.fromtimestamp(ts_val) if ts_val else datetime.now()
            lines.append(f"  - {ts.strftime('%Y-%m-%d %H:%M')}: {trade.get('side')} {trade.get('size')} of '{trade.get('outcome')}' @ ${trade.get('price')}")
            
    return "\n".join(lines)


def _format_order_book_text(order_book: Dict[str, Any]) -> str:
    if not order_book:
        return "Order book data is not available."

    lines = [f"Order Book Summary for Market: {order_book.get('market')}"]
    lines.append(f"  Tick Size: {order_book.get('tick_size')}")
    lines.append(f"  Min Order Size: {order_book.get('min_order_size')}")

    lines.append("\nBids (Price | Size):")
    bids = sorted(order_book.get('bids', []), key=lambda x: float(x.get('price', 0)), reverse=True)
    if not bids:
        lines.append("  - No bids")
    for order in bids[:5]:
        lines.append(f"  - ${float(order.get('price', 0)):.2f} | {float(order.get('size', 0)):.2f}")

    lines.append("\nAsks (Price | Size):")
    asks = sorted(order_book.get('asks', []), key=lambda x: float(x.get('price', 0)))
    if not asks:
        lines.append("  - No asks")
    for order in asks[:5]:
        lines.append(f"  - ${float(order.get('price', 0)):.2f} | {float(order.get('size', 0)):.2f}")
        
    return "\n".join(lines)


def _format_top_holders_text(top_holders: Dict[str, Any]) -> str:
    if not top_holders or not (top_holders.get('yes') or top_holders.get('no')):
        return "No holder information available."

    lines = ["Top Holders:"]
    
    lines.append("\nTop 5 'Yes' Holders (Username | Address | Amount):")
    for holder in top_holders.get('yes', []):
        lines.append(f"  - {holder.get('username', 'N/A')} | {holder.get('address', 'N/A')} | {holder.get('amount', 0):.2f}")

    lines.append("\nTop 5 'No' Holders (Username | Address | Amount):")
    for holder in top_holders.get('no', []):
        lines.append(f"  - {holder.get('username', 'N/A')} | {holder.get('address', 'N/A')} | {holder.get('amount', 0):.2f}")
        
    return "\n".join(lines)


def _format_top_traders_text(traders: List[Dict[str, Any]]) -> str:
    if not traders:
        return "No top trader information available."

    lines = ["Top 5 Traders by PNL:"]
    for i, trader in enumerate(traders, 1):
        username = trader.get('username') or trader.get('address')
        lines.append(f"\n{i}. Trader: {username}")
        lines.append(f"   Total PNL: ${trader.get('total_pnl', 0):,.2f}")
        lines.append(f"   Most Profitable Market: '{trader.get('most_profitable_market', 'N/A')}'")
        
    return "\n".join(lines)


async def _summarize_trader_with_ai(details: Dict[str, Any]) -> str:
    if not details:
        return "Not enough data to generate a summary."

    # Prepare a condensed version of the data for the prompt
    prompt_data = {
        "address": details.get("address"),
        "total_volume": details.get("total_volume"),
        "pnl": details.get("pnl", {}).get("all_time"),
        "recent_positions": [
            {"market": p.get("market_title"), "pnl": p.get("pnl")}
            for p in details.get("positions", [])[:3]
        ],
        "recent_trades": [
            {"market": t.get("title"), "outcome": t.get("outcome"), "side": t.get("side"), "size": t.get("size")}
            for t in details.get("trades", [])[:3]
        ]
    }

    prompt = (
        "You are a crypto market analyst. "
        "Summarize the trading activity of the following Polymarket user in a few sentences. "
        "Mention their profitability (PNL), total volume, and the types of markets they trade in based on their recent activity. "
        f"Trader Data: {json.dumps(prompt_data, indent=2)}"
    )

    messages = [{"role": "user", "content": prompt}]
    try:
        response = await run_in_threadpool(asi_chat, messages=messages)
        summary = response.get("choices", [{}])[0].get("message", {}).get("content", "Could not generate summary.")
        return summary
    except Exception as e:
        logger.error(f"Error generating AI summary for trader: {e}")
        return "Could not generate AI summary due to an error."


@router.post("/ask")
async def agent_ask(
    payload: Dict[str, Any] = Body(..., example={"query": "Show me top 5 markets"}),
    execute: bool = Query(True, description="Execute the decided action and return results"),
    fmt: str = Query("text", description="text | json"),
):
    query: str = payload.get("query", "").strip()
    session_id: Optional[str] = payload.get("session_id")

    logger.info(f"Received query: '{query}' for session_id: {session_id}")

    if not query:
        return {"error": "Missing 'query' in body"}

    context = get_session_context(session_id) if session_id else {}
    
    # Plan the tool call using the new planner
    tool_calls = await run_in_threadpool(plan_with_tools, query, context)
    
    if not tool_calls:
        return {"error": "No tool call planned by the AI."}

    # For simplicity, we'll execute the first tool call
    tool_call = tool_calls[0]
    function_call = tool_call.get("function", {})
    tool_name = function_call.get("name")
    
    try:
        arguments = json.loads(function_call.get("arguments", "{}"))
    except json.JSONDecodeError:
        return {"error": "Failed to parse tool arguments from AI."}

    logger.info(f"AI Planner decision: action='{tool_name}', params={arguments}")

    if not execute:
        return {"plan": {"action": tool_name, "params": arguments}}

    # Execute the chosen tool
    result: Any = None
    formatted_result: Any = None

    if tool_name == "get_markets":
        limit = arguments.get("limit", 5)
        result = await run_in_threadpool(get_markets_normalized, {"limit": str(limit)})
        if session_id and result:
            update_session_context(session_id, {"last_markets": result, "last_condition_id": result[0].get("conditionId")})
        formatted_result = _format_markets_text(result)
    
    elif tool_name == "get_trades_for_condition":
        condition_id = arguments.get("condition_id")
        if not condition_id:
            return {"error": "condition_id is required for get_trades_for_condition."}
        limit = arguments.get("limit", 100)
        result = await run_in_threadpool(get_trades_by_condition, condition_id, limit)
        if session_id:
            update_session_context(session_id, {"last_condition_id": condition_id})
        formatted_result = _format_trades_text(result)

    elif tool_name == "get_order_book":
        condition_id = arguments.get("condition_id")
        if not condition_id:
            return {"error": "condition_id is required for get_order_book."}
        result = await run_in_threadpool(get_order_book, condition_id)
        if session_id:
            update_session_context(session_id, {"last_condition_id": condition_id})
        formatted_result = _format_order_book_text(result)

    elif tool_name == "get_top_holders":
        condition_id = arguments.get("condition_id")
        if not condition_id:
            return {"error": "condition_id is required for get_top_holders."}
        result = await run_in_threadpool(get_top_holders, condition_id)
        if session_id:
            update_session_context(session_id, {"last_condition_id": condition_id})
        formatted_result = _format_top_holders_text(result)

    elif tool_name == "get_top_traders_by_pnl":
        result = await run_in_threadpool(get_top_traders_by_pnl)
        formatted_result = _format_top_traders_text(result)

    elif tool_name == "get_trader_details":
        address = arguments.get("address")
        if not address:
            return {"error": "address is required for get_trader_details."}
        result = await run_in_threadpool(summarize_trader_details, address)
        if session_id:
            update_session_context(session_id, {"last_trader_address": address})
        
        formatted_result = _format_trader_details_text(result)
        ai_summary = await _summarize_trader_with_ai(result)
        formatted_result += f"\n\nAI Summary:\n{ai_summary}"
            
    elif tool_name == "unsupported":
        result = {"error": "Query not supported by available tools."}
        formatted_result = "Sorry, I can't answer that question."
        
    else:
        return {"error": f"Unknown tool: {tool_name}"}

    final_result = formatted_result if fmt == "text" else result
    return {"plan": {"action": tool_name, "params": arguments}, "result": final_result}


