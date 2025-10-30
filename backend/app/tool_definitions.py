from typing import Any, Dict

# Schemas for ASI:One tool-calling

GET_MARKETS_TOOL = {
    "type": "function",
    "function": {
        "name": "get_markets",
        "description": "Get a list of top markets with essential data. Use for general queries about markets.",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {"type": "number", "default": 5, "description": "Number of markets to return."}
            },
            "required": [],
        },
    }
}

GET_TRADES_TOOL = {
    "type": "function",
    "function": {
        "name": "get_trades_for_condition",
        "description": "Get trades for a specific market condition. Requires a conditionId.",
        "parameters": {
            "type": "object",
            "properties": {
                "condition_id": {"type": "string", "description": "The unique identifier for the market condition."},
                "limit": {"type": "number", "default": 100, "description": "Number of trades to return."}
            },
            "required": ["condition_id"],
        },
    }
}


GET_TRADER_DETAILS_TOOL = {
    "type": "function",
    "function": {
        "name": "get_trader_details",
        "description": "Get a summary of a trader's activity, including positions and trade history.",
        "parameters": {
            "type": "object",
            "properties": {
                "address": {"type": "string", "description": "The public key (0x...) of the trader."}
            },
            "required": ["address"],
        },
    }
}

# Future tool for orderbook
GET_ORDERBOOK_TOOL = {
    "type": "function",
    "function": {
        "name": "get_order_book",
        "description": "Get a summary of the order book for a specific market ID, including top bids and asks, tick size, and minimum order size.",
        "parameters": {
            "type": "object",
            "properties": {
                "market_id": {"type": "string", "description": "The unique identifier for the market (e.g., a number like '618023')."}
            },
            "required": ["market_id"],
        },
    }
}

GET_TOP_HOLDERS_TOOL = {
    "type": "function",
    "function": {
        "name": "get_top_holders",
        "description": "Get the top 5 holders for a specific market condition, separated by YES and NO outcomes.",
        "parameters": {
            "type": "object",
            "properties": {
                "condition_id": {"type": "string", "description": "The unique identifier for the market condition."}
            },
            "required": ["condition_id"],
        },
    }
}

GET_TOP_TRADERS_TOOL = {
    "type": "function",
    "function": {
        "name": "get_top_traders_by_pnl",
        "description": "Get the top 5 traders by profit and loss (PNL), summarizing their total PNL and most profitable market.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    }
}

GET_CLOSED_POSITIONS_TOOL = {
    "type": "function",
    "function": {
        "name": "get_closed_positions_for_user",
        "description": "Get a list of closed positions for a specific trader, showing the market and realized PNL.",
        "parameters": {
            "type": "object",
            "properties": {
                "address": {"type": "string", "description": "The public key (0x...) of the trader."}
            },
            "required": ["address"],
        },
    }
}

ALL_TOOLS = [
    GET_MARKETS_TOOL,
    GET_TRADES_TOOL,
    GET_TRADER_DETAILS_TOOL,
    GET_ORDERBOOK_TOOL,
    GET_TOP_HOLDERS_TOOL,
    GET_TOP_TRADERS_TOOL,
    GET_CLOSED_POSITIONS_TOOL,
]

def get_tool_schemas() -> list[dict[str, Any]]:
    return ALL_TOOLS
