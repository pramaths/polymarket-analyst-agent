import json
from typing import Any, Dict
from tools import agent_ask


def _format_result(result: Dict[str, Any]) -> str:
    plan = result.get("plan", {})
    action = plan.get("action", "N/A")
    params = plan.get("params", {})
    reasoning = plan.get("reasoning", {})
    ai_raw = reasoning.get("ai_raw")

    output_lines = []
    output_lines.append(f"AI Decision: Calling '{action}' API.")

    if params:
        output_lines.append(f"Parameters: {json.dumps(params)}")
    
    if ai_raw:
        # The raw output can be a string containing JSON, so we format it nicely
        try:
            parsed_raw = json.loads(ai_raw)
            output_lines.append(f"AI Raw Output: {json.dumps(parsed_raw)}")
        except Exception:
            output_lines.append(f"AI Raw Output: {ai_raw}")

    output_lines.append("--------------------")

    if "result" in result:
        res = result["result"]
        if isinstance(res, str):
            output_lines.append(res)
        elif isinstance(res, (dict, list)):
            output_lines.append(json.dumps(res, indent=2))
    elif "error" in result:
        output_lines.append(f"Error: {result['error']}")
    
    return "\n".join(output_lines)


def handle_request(text: str, api_key: str, session_id: str) -> str:
    try:
        result = agent_ask(api_key, text, execute=True, session_id=session_id, fmt="text")
        return _format_result(result)
    except Exception as e:
        return f"Planner error: {e}"
