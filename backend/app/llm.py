from __future__ import annotations

import os
import uuid
from typing import Any, Dict, List, Optional
import requests


ASI_API_URL = "https://api.asi1.ai/v1/chat/completions"


def asi_chat(
    messages: List[Dict[str, str]],
    model: str = "asi1-fast",
    api_key: Optional[str] = None,
    temperature: float = 0.2,
    max_tokens: Optional[int] = 800,
    stream: bool = False,
    tools: Optional[List[Dict[str, Any]]] = None,
    web_search: Optional[bool] = None,
    agent_address: Optional[str] = None,
) -> Dict[str, Any]:
    key = api_key or os.getenv("ASI_API_KEY")
    if not key:
        raise RuntimeError("ASI_API_KEY not set in environment")

    headers = {
        "Authorization": f"Bearer {key}",
        "x-session-id": str(uuid.uuid4()),
        "Content-Type": "application/json",
    }

    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    if stream:
        payload["stream"] = True
    if tools is not None:
        payload["tools"] = tools
    if web_search is not None:
        payload["web_search"] = web_search
    if agent_address is not None:
        payload["agent_address"] = agent_address

    resp = requests.post(ASI_API_URL, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()


