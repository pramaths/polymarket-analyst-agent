from __future__ import annotations
import json
from typing import Any, Dict, List, Optional

from .llm import asi_chat
from .tool_definitions import get_tool_schemas

SYSTEM_PROMPT = (
    "You are an expert at calling tools based on user queries. Your task is to select the single best tool to answer the user's question about Polymarket and provide the necessary arguments.\n"
    "- You MUST select a tool. Do not respond conversationally.\n"
    "- If the query provides a unique identifier like a conditionId or address, use it.\n"
    "- Use context when provided to answer follow-up questions.\n"
    "- Return ONLY the tool call."
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
