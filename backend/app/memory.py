from __future__ import annotations

from typing import Any, Dict

SESSION_MEMORY: Dict[str, Dict[str, Any]] = {}


def get_session_context(session_id: str) -> Dict[str, Any]:
    if session_id not in SESSION_MEMORY:
        SESSION_MEMORY[session_id] = {}
    return SESSION_MEMORY[session_id]


def update_session_context(session_id: str, updates: Dict[str, Any]) -> None:
    if session_id not in SESSION_MEMORY:
        SESSION_MEMORY[session_id] = {}
    SESSION_MEMORY[session_id].update(updates)


def clear_session_context(session_id: str) -> None:
    if session_id in SESSION_MEMORY:
        del SESSION_MEMORY[session_id]
