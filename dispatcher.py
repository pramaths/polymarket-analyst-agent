import json
from tools import query_markets, get_market_stats, get_category_stats
from reasoning import recommend_markets
from parser import parse_text_to_market_params

def handle_request(text: str, api_key: str) -> str:
    """
    Routes the user's text request to the appropriate tool or reasoning function
    and formats the response.
    """
    text = text.lower()

    # --- Intent Routing ---
    # Tool: Get Market Stats
    if "market stats" in text:
        stats = get_market_stats(api_key)
        return f"Here are the latest market stats:\n{json.dumps(stats, indent=2)}"
    
    # Tool: Get Category Stats
    if "category stats" in text:
        stats = get_category_stats(api_key)
        return f"Here are the latest category stats:\n{json.dumps(stats, indent=2)}"

    # Reasoning: Find Recommendations (MeTTa)
    if text.startswith("recommendations for"):
        target_slug = text.replace("recommendations for", "").strip()
        all_markets = query_markets(api_key, {"limit": 100})
        if all_markets:
            recommendations = recommend_markets(all_markets, target_slug)
            if recommendations:
                return f"Based on category and shared tags, I recommend these markets for '{target_slug}':\n- " + "\n- ".join(recommendations)
            return f"I couldn't find any good recommendations for '{target_slug}'."
        return "I couldn't fetch market data to base my recommendations on."

    # Tool: Query Markets (Default)
    params = parse_text_to_market_params(text)
    markets = query_markets(api_key, params)
    if markets:
        response_text = "Here are the markets I found:\n"
        for i, market in enumerate(markets):
            question = market.get("question", "N/A")
            volume = market.get("pricing", {}).get("volume", 0)
            liquidity = market.get("pricing", {}).get("liquidity", 0)
            response_text += f"{i+1}. {question} (Volume: ${volume:,.0f}, Liq: ${liquidity:,.0f})\n"
        return response_text
    
    return "I couldn't find any markets matching your query."
