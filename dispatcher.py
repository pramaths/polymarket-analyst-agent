import json
from typing import Any, Dict
from tools import agent_ask

def handle_request(text: str, api_key: str, session_id: str) -> str:
    try:
        result = agent_ask(api_key, text, execute=True, session_id=session_id, fmt="text")
        
        print(f"--- Response from Backend ---\n{json.dumps(result, indent=2)}")

        if "result" in result:
            res = result["result"]
            if isinstance(res, str):
                return res
            elif isinstance(res, (dict, list)):
                return json.dumps(res, indent=2)
        elif "error" in result:
            return f"Error: {result['error']}"
            
        return "Error: An unexpected error occurred."
    except Exception as e:
        return f"An error occurred: {e}"
