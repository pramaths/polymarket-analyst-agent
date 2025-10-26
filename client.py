from uagents import Agent, Context
from uagents.setup import fund_agent_if_low
from uagents_core.contrib.protocols.chat import (
    ChatMessage,
    StartSessionContent,
    TextContent,
    ChatAcknowledgement,
    EndSessionContent
)
from datetime import datetime
from uuid import uuid4

# The address of the polymarket_analyst agent
# Replace this with the actual address printed by main.py
AGENT_ADDRESS = "agent1qgss4sfwpgxjx2k5tkauuwzaqtsdher6zdk7rmz4d5dyjrw39t7tvxeh9gm"  # PASTE AGENT ADDRESS HERE

# Create a client agent
client_agent = Agent(
    name="test_client",
    seed="a_very_different_client_seed_phrase",
    port=8002,
    endpoint="http://127.0.0.1:8002/submit",
)
fund_agent_if_low(client_agent.wallet.address())

# Define the message content
content = [
    StartSessionContent(),
    TextContent(type="text", text="markets"),
]

# Create the ChatMessage
chat_message = ChatMessage(
    timestamp=datetime.utcnow(),
    msg_id=uuid4(),
    content=content,
)

@client_agent.on_event('startup')
async def send_test_message(ctx: Context):
    ctx.logger.info(f"Sending test message to {AGENT_ADDRESS}")
    await ctx.send(AGENT_ADDRESS, chat_message)
    ctx.logger.info("Message sent. Now waiting for acknowledgement...")

@client_agent.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(f"Received acknowledgement from {sender} for message {msg.acknowledged_msg_id}")
    ctx.logger.info("Test successful! Stopping agent.")
    client_agent.stop()

@client_agent.on_message(ChatMessage)
async def handle_response(ctx: Context, sender: str, msg: ChatMessage):
    for item in msg.content:
        if isinstance(item, TextContent):
            ctx.logger.info(f"Received response from {sender}:")
            print(f"\nAGENT RESPONSE:\n{item.text}\n")

            # If this is the response for 'markets', send the 'orderbook' request
            if "slugs for orderbook lookup" in item.text:
                ctx.logger.info("Markets received, now testing orderbook.")
                orderbook_msg = create_text_chat("orderbook will-joe-biden-get-coronavirus-before-the-election")
                await ctx.send(AGENT_ADDRESS, orderbook_msg)

def create_text_chat(text: str, end_session: bool = False) -> ChatMessage:
    """Utility function to wrap plain text into a ChatMessage."""
    content = [TextContent(type="text", text=text)]
    if end_session:
        content.append(EndSessionContent())
    return ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=content,
    )

if __name__ == "__main__":
    if "agent1..." in AGENT_ADDRESS:
        print("="*60)
        print("Please open client.py and replace 'agent1...'")
        print("with the actual address of the polymarket_analyst agent.")
        print("="*60)
    else:
        client_agent.run()
