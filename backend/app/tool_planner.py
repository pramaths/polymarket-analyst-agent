from __future__ import annotations
import json
from typing import Any, Dict, List, Optional

from .llm import asi_chat
from .tool_definitions import get_tool_schemas

SYSTEM_PROMPT = (
    "You are a helpful assistant for Polymarket data retrieval. "
    "Given a user query, identify the correct tool and arguments to call. "
    "If the user asks a follow-up question that requires context (e.g., 'get trades for that market'), "
    "and you are provided with context like 'last_condition_id', use it to fill in the missing arguments."
)

def plan_with_tools(
    query: str,
    session_context: Dict[str, Any],
    model: str = "asi1-fast",
    api_key: Optional[str] = None
) -> List[Dict[str, Any]]:
    
    context_injection = ""
    if session_context.get("last_condition_id"):
        context_injection += f" The user's last-viewed market has conditionId '{session_context['last_condition_id']}'. "
    if session_context.get("last_trader_address"):
        context_injection += f" The user's last-viewed trader has address '{session_context['last_trader_address']}'. "

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": query + context_injection},
    ]

    tools = get_tool_schemas()
    
    response = asi_chat(
        messages=messages,
        tools=tools,
        model=model,
        api_key=api_key
    )

    choice = response.get("choices", [{}])[0].get("message", {})
    if not choice or "tool_calls" not in choice:
        # If the model doesn't call a tool, we'll treat it as unsupported for now
        return [{"function": {"name": "unsupported", "arguments": "{}"}}]
        
    return choice["tool_calls"]
