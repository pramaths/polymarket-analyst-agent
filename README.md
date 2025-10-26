# Polymarket Analyst Agent 🔮

An AI-powered conversational agent that provides intelligent insights from Polymarket prediction markets. This project combines a modular, tool-based agent architecture with a powerful symbolic reasoning engine to go beyond simple data retrieval.

## How It Works: The Architecture

This project is built on a clean, decoupled architecture that separates data processing, querying, and agent logic. This design makes the system scalable, maintainable, and highly extensible.

```
┌──────────────────┐     ┌───────────────────┐     ┌────────────────┐
│ User via         │     │                   │     │ Python Query   │
│ Agentverse UI    │ ◀───▶ │ Python Analyst    │ ◀───▶ │ Backend        │
└──────────────────┘     │ Agent (main.py)   │     │ (FastAPI)      │
                         └───────┬───────────┘     └───────┬────────┘
                                 │                         │
            (Calls Tools & Reasoners)                      ▼
                                 │                 ┌────────────────┐
                         ┌───────▼───────────┐     │ MongoDB        │
                         │ Agent "Brain"     │     │ Database       │
                         │ (dispatcher.py)   │     └────────────────┘
                         └───────────────────┘
```

1.  **Python Query Backend (`/backend`):** A lightweight FastAPI server whose only job is to connect to the database and expose a powerful API. It translates simple HTTP requests into complex MongoDB queries.
2.  **Agent Runtimes (`main.py`):** A lean entrypoint for the `uagents` agent. Its only jobs are to handle the connection to the Agentverse and pass messages to the agent's "brain".
3.  **The Agent's "Brain" (`dispatcher.py`, `parser.py`, `tools.py`):** This is the core of the agent's intelligence.
    *   **Parser:** Translates natural language into structured commands.
    *   **Tools:** A collection of functions that perform specific actions, like calling the backend API.
    *   **Dispatcher:** The central router that understands the user's intent and decides which tool to use.
4.  **The Reasoning Engine (`reasoning.py`):** This is where the magic happens. This module uses **SingularityNET's MeTTa (Hyperon)** knowledge graph to perform symbolic reasoning on the market data. Instead of just filtering data, it can understand and deduce complex relationships between markets.

## The Possibilities: Beyond Simple Queries

This architecture opens the door to truly intelligent analysis. While you can ask simple questions, the real power lies in leveraging the reasoning engine.

### Example Queries

*   **Simple Data Retrieval:**
    *   `get market stats`
    *   `show me the top 5 crypto markets by volume`
    *   `find active politics markets with liquidity under 10k`
*   **Symbolic Reasoning with MeTTa:**
    *   `recommendations for will-donald-trump-win-the-2024-election`

The "recommendations" query doesn't just filter a database; it builds a knowledge graph of markets and their relationships (category, tags) and uses logical rules to *deduce* which markets are relevant.

### Future Expansion

This modular design makes it easy to add new capabilities:
*   **Add New Tools:** Create a new function in `tools.py` to call a different API (e.g., a sentiment analysis API for news articles).
*   **Add New Reasoning Rules:** Expand `reasoning.py` with more complex MeTTa rules. For example, you could define a rule for "contrarian markets" (markets with high volume but lopsided odds) or "trending markets" (markets with a recent spike in volume). The possibilities are endless.

## Setup and Running

*(Instructions for setting up the backend and agent remain the same as before.)*
