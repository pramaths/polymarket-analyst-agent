import re
from typing import Dict

def parse_text_to_market_params(text: str) -> Dict:
    """
    Parses natural language text to extract query parameters for the /markets endpoint.
    """
    params = {}
    text = text.lower()
    
    # Category
    match = re.search(r"(?:in|for|about) (\w+) markets", text)
    if match:
        params["category"] = match.group(1)
    
    # Active status
    if "active" in text:
        params["active"] = "true"
    if "closed" in text:
        params["closed"] = "true"

    # Volume and Liquidity
    for metric in ["volume", "liquidity"]:
        match = re.search(rf"{metric} (?:over|greater than|>) (\d+[kKmM]?)", text)
        if match:
            value = match.group(1)
            num = int(value.lower().replace('k', '000').replace('m', '000000'))
            params[f"{metric}_gt"] = num
        
        match = re.search(rf"{metric} (?:under|less than|<) (\d+[kKmM]?)", text)
        if match:
            value = match.group(1)
            num = int(value.lower().replace('k', '000').replace('m', '000000'))
            params[f"{metric}_lt"] = num

    # Sorting
    match = re.search(r"(?:sorted|ordered) by (\w+)", text)
    if match:
        sort_key = match.group(1)
        if sort_key in ["volume", "liquidity"]:
            params["sortBy"] = f"pricing.{sort_key}"
    
    if "lowest" in text or "ascending" in text:
        params["sortOrder"] = "asc"

    # Limit
    match = re.search(r"(?:top|show me|get|find) (\d+)", text)
    if match:
        params["limit"] = int(match.group(1))

    return params
