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
    get_closed_positions_for_user,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


router = APIRouter(prefix="/agent", tags=["agent"])


def _format_markets_text(markets: List[Dict[str, Any]]) -> str:
    if not markets:
        return "No markets found."
    lines = ["**📊 Top Markets:**\n"]
    for i, market in enumerate(markets, 1):
        lines.append(
            f"**{i}. {market.get('question')}**\n"
            f"   - **Market ID:** `{market.get('id')}`\n"
            f"   - **Condition ID:** `{market.get('conditionId')}`\n"
            f"   - **Category:** {market.get('category')}\n"
            f"   - **Volume:** ${market.get('volume', 0):,.2f} 💹\n"
            f"   - **Liquidity:** ${market.get('liquidity', 0):,.2f} 💧\n"
            f"   - **Prices:** Yes: ${market.get('yes_price', 0):.2f} | No: ${market.get('no_price', 0):.2f}\n"
            f"   - **Ends:** {market.get('endDate')} ⏳\n"
        )
    return "\n".join(lines)

def _format_trades_text(trades: List[Dict[str, Any]]) -> str:
    if not trades:
        return "No trades found for this market."
    
    title = trades[0].get('title', 'N/A')
    lines = [f"**📈 Recent Trades for '{title}':**\n"]
    for i, trade in enumerate(trades[:10], 1):
        ts_val = trade.get('timestamp', 0)
        ts = datetime.fromtimestamp(ts_val) if ts_val else datetime.now()
        side_emoji = "🟢" if trade.get('side') == 'buy' else "🔴"
        lines.append(
            f"**{i}. {ts.strftime('%Y-%m-%d %H:%M')}**\n"
            f"   - **Side:** {trade.get('side')} {side_emoji}\n"
            f"   - **Outcome:** {trade.get('outcome')}\n"
            f"   - **Size:** {trade.get('size', 0):.2f}\n"
            f"   - **Price:** ${trade.get('price', 0):.2f}\n"
            f"   - **Trader:** `{trade.get('proxyWallet')}`\n"
        )
    return "\n".join(lines)

def _format_trader_details_text(details: Dict[str, Any]) -> str:
    if not details:
        return "No details found for this trader."
    
    pnl = details.get('pnl', {})
    total_pnl = pnl.get('all_time', 0)
    pnl_emoji = "🚀" if total_pnl > 0 else "📉"
    
    positions = details.get('positions', [])
    trades = details.get('trades', [])
    
    lines = [
        f"**👤 Trader Details for `{details.get('address')}`**\n",
        f"   - **All-time PNL:** ${total_pnl:,.2f} {pnl_emoji}\n",
        f"   - **Total Volume:** ${details.get('total_volume', 0):,.2f}\n",
        "**📊 Recent Positions:**",
    ]
    if not positions:
        lines.append("  - None")
    else:
        for pos in positions[:5]:
            pos_pnl_emoji = "🟢" if pos.get('pnl', 0) > 0 else "🔴"
            lines.append(f"  - **Market:** '{pos.get('market_title', 'N/A')}', **PNL:** ${pos.get('pnl', 0):,.2f} {pos_pnl_emoji}")

    lines.append("\n**📈 Recent Trades:**")
    if not trades:
        lines.append("  - None")
    else:
        for trade in trades[:5]:
            ts_val = trade.get('timestamp', 0)
            ts = datetime.fromtimestamp(ts_val) if ts_val else datetime.now()
            lines.append(f"  - {ts.strftime('%Y-%m-%d %H:%M')}: {trade.get('side')} {trade.get('size')} of '{trade.get('outcome')}' @ ${trade.get('price')}")
            
    return "\n".join(lines)


def _format_order_book_text(order_book: Dict[str, Any]) -> str:
    if not order_book:
        return "Order book data is not available."
    if "error" in order_book:
        return order_book.get("error")

    lines = ["**📖 Order Book Summary:**\n"]

    for outcome in ["yes", "no"]:
        lines.append(f"**--- {outcome.upper()} Outcome ---**")
        book = order_book.get(outcome, {})
        
        if "error" in book:
            lines.append(f"  - {book['error']}")
            continue

        lines.append(f"  - **Market:** `{book.get('market')}`")
        lines.append(f"  - **Tick Size:** {book.get('tick_size')}")
        lines.append(f"  - **Min Order Size:** {book.get('min_order_size')}")

        lines.append("\n  **🟢 Bids (Price | Size):**")
        bids = sorted(book.get('bids', []), key=lambda x: float(x.get('price', 0)), reverse=True)
        if not bids:
            lines.append("    - No bids")
        for order in bids[:5]:
            lines.append(f"    - `${float(order.get('price', 0)):.2f}` | `{float(order.get('size', 0)):.2f}`")

        lines.append("\n  **🔴 Asks (Price | Size):**")
        asks = sorted(book.get('asks', []), key=lambda x: float(x.get('price', 0)))
        if not asks:
            lines.append("    - No asks")
        for order in asks[:5]:
            lines.append(f"    - `${float(order.get('price', 0)):.2f}` | `{float(order.get('size', 0)):.2f}`")
        
    return "\n".join(lines)


def _format_top_holders_text(top_holders: Dict[str, Any]) -> str:
    if not top_holders or not (top_holders.get('yes') or top_holders.get('no')):
        return "No holder information available."

    lines = ["**🏆 Top Holders:**\n"]
    
    lines.append("**👍 Top 5 'Yes' Holders:**")
    for holder in top_holders.get('yes', []):
        lines.append(f"  - **User:** {holder.get('username', 'N/A')} (`{holder.get('address', 'N/A')}`) | **Amount:** {holder.get('amount', 0):.2f}")

    lines.append("\n**👎 Top 5 'No' Holders:**")
    for holder in top_holders.get('no', []):
        lines.append(f"  - **User:** {holder.get('username', 'N/A')} (`{holder.get('address', 'N/A')}`) | **Amount:** {holder.get('amount', 0):.2f}")
        
    return "\n".join(lines)


def _format_top_traders_text(traders: List[Dict[str, Any]]) -> str:
    if not traders:
        return "No top trader information available."

    lines = ["**🥇 Top 5 Traders by PNL:**\n"]
    for i, trader in enumerate(traders, 1):
        username = trader.get('username') or trader.get('address')
        pnl_emoji = "🚀" if trader.get('total_pnl', 0) > 0 else "📉"
        lines.append(f"**{i}. Trader: {username}**")
        lines.append(f"   - **Total PNL:** ${trader.get('total_pnl', 0):,.2f} {pnl_emoji}")
        lines.append(f"   - **Most Profitable Market:** '{trader.get('most_profitable_market', 'N/A')}'")
        
    return "\n".join(lines)


def _format_closed_positions_text(positions: List[Dict[str, Any]]) -> str:
    if not positions:
        return "No closed positions found for this trader."

    lines = ["**📜 Closed Positions & PNL:**\n"]
    for pos in positions:
        pnl = pos.get('realizedPnl', 0)
        pnl_emoji = "🟢" if pnl > 0 else "🔴" if pnl < 0 else "⚪"
        lines.append(
            f"- **Market:** '{pos.get('title', 'N/A')}'\n"
            f"  - **Condition ID:** `{pos.get('conditionId')}`\n"
            f"  - **Realized PNL:** ${pnl:,.2f} {pnl_emoji}\n"
        )
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
        market_id = arguments.get("market_id")
        if not market_id:
            return {"error": "market_id is required for get_order_book."}
        
        result_data = await run_in_threadpool(get_order_book, market_id)

        if "error" in result_data:
            result = result_data
        else:
            result = result_data.get("order_books")
            condition_id = result_data.get("condition_id")
            if session_id and condition_id:
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

    elif tool_name == "get_closed_positions_for_user":
        address = arguments.get("address")
        if not address:
            return {"error": "address is required for get_closed_positions_for_user."}
        result = await run_in_threadpool(get_closed_positions_for_user, address)
        if session_id:
            update_session_context(session_id, {"last_trader_address": address})
        formatted_result = _format_closed_positions_text(result)

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
    response_payload = {"result": final_result}
    
    try:
        logger.info(f"--- Sending Response to Agent ---\n{json.dumps(response_payload, indent=2)}")
    except TypeError:
        logger.info(f"--- Sending Response to Agent (unserializable) ---\n{str(response_payload)}")
        
    return response_payload


