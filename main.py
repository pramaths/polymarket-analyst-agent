import requests
import re
from datetime import datetime
from uuid import uuid4
import urllib.parse
import httpx

from uagents import Agent, Context, Protocol
from uagents.setup import fund_agent_if_low
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement, ChatMessage, EndSessionContent,
    StartSessionContent, TextContent, chat_protocol_spec,
)
from datetime import datetime
from uuid import uuid4
import re
from tools import query_markets, get_market_stats, analyze_market, analyze_election, get_recommendations
from dispatcher import handle_request
from config import ASI_API_KEY, AGENT_NAME, AGENT_SEED, BACKEND_URL

agent = Agent(name=AGENT_NAME, seed=AGENT_SEED, port=8001, mailbox=True)
fund_agent_if_low(agent.wallet.address())
chat_proto = Protocol(name=chat_protocol_spec.name, version=chat_protocol_spec.version)

@agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info(f"Agent {ctx.name} starting up.")

@agent.on_interval(period=60.0)
async def health_check(ctx: Context):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BACKEND_URL}/health")
            if response.status_code == 200:
                ctx.logger.info("Backend health check successful.")
            else:
                ctx.logger.warning(f"Backend health check failed with status {response.status_code}.")
    except Exception as e:
        ctx.logger.error(f"An error occurred during backend health check: {e}")

def create_text_chat(text: str) -> ChatMessage:
    content = [TextContent(type="text", text=text)]
    return ChatMessage(timestamp=datetime.utcnow(), msg_id=uuid4(), content=content)

@chat_proto.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    await ctx.send(sender, ChatAcknowledgement(timestamp=datetime.utcnow(), acknowledged_msg_id=msg.msg_id))
    for item in msg.content:
        if isinstance(item, StartSessionContent):
            await ctx.send(sender, create_text_chat("Hello! I am the Polymarket Analyst Agent. How can I help?"))
            return
        if isinstance(item, TextContent):
            try:
                response_text = handle_request(item.text, ASI_API_KEY, session_id=sender)
            except Exception as e:
                ctx.logger.error(f"Error handling request: {e}")
                response_text = "Sorry, I encountered an error."
            await ctx.send(sender, create_text_chat(response_text))

agent.include(chat_proto, publish_manifest=True)

if __name__ == "__main__":
    agent.run()
