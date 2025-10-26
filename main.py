import requests
import re
from datetime import datetime
from uuid import uuid4
from config import BACKEND_API_URL
import urllib.parse

from uagents import Agent, Context, Protocol
from uagents.setup import fund_agent_if_low
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement, ChatMessage, EndSessionContent,
    StartSessionContent, TextContent, chat_protocol_spec,
)
from datetime import datetime
from uuid import uuid4
import re
import json

from tools import query_markets, get_market_stats
from reasoning import recommend_markets
from dispatcher import handle_request

AGENT_NAME = "polymarket_analyst"
AGENT_SEED = "a_new_polymarket_analyst_agent_secret_seed_phrase"
ASI_API_KEY = "your_asi_api_key_here"

agent = Agent(name=AGENT_NAME, seed=AGENT_SEED, port=8001, mailbox=True)
fund_agent_if_low(agent.wallet.address())
chat_proto = Protocol(name=chat_protocol_spec.name, version=chat_protocol_spec.version)

def create_text_chat(text: str) -> ChatMessage:
    content = [TextContent(type="text", text=text)]
    return ChatMessage(timestamp=datetime.utcnow(), msg_id=uuid4(), content=content)

@agent.on_event("startup")
async def run_startup_tests(ctx: Context):
    ctx.logger.info("--- RUNNING STARTUP INTEGRATION TESTS ---")
    
    stats = get_market_stats(ASI_API_KEY)
    if stats and stats.get('totalVolume'):
        ctx.logger.info("Success! Market stats tool is working.")
    else:
        ctx.logger.error("Failed: Market stats tool.")

    markets = query_markets(ASI_API_KEY, {"limit": 1})
    if markets:
        ctx.logger.info("Success! Market query tool is working.")
        target_slug = markets[0].get("slug")
        all_markets = query_markets(ASI_API_KEY, {"limit": 100})
        if all_markets and target_slug:
            recommendations = recommend_markets(all_markets, target_slug)
            if recommendations is not None:
                ctx.logger.info("Success! Reasoning engine is working.")
            else:
                ctx.logger.error("Failed: Reasoning engine.")
    else:
        ctx.logger.error("Failed: Market query tool. Cannot proceed with reasoning test.")
    
    ctx.logger.info("--- STARTUP TESTS COMPLETE ---")

@chat_proto.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    await ctx.send(sender, ChatAcknowledgement(timestamp=datetime.utcnow(), acknowledged_msg_id=msg.msg_id))
    for item in msg.content:
        if isinstance(item, StartSessionContent):
            await ctx.send(sender, create_text_chat("Hello! I am the Polymarket Analyst Agent. How can I help?"))
            return
        if isinstance(item, TextContent):
            try:
                response_text = handle_request(item.text, ASI_API_KEY)
            except Exception as e:
                ctx.logger.error(f"Error handling request: {e}")
                response_text = "Sorry, I encountered an error."
            await ctx.send(sender, create_text_chat(response_text))

agent.include(chat_proto, publish_manifest=True)

if __name__ == "__main__":
    agent.run()
