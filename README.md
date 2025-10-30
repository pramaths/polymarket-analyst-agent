# 🔮 Polymarket Analyst Agent

![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)
![tag:domain/prediction-markets](https://img.shields.io/badge/domain-prediction%20markets-blue)

## Overview

This AI Agent is a specialized analyst for the Polymarket prediction markets. It provides on-demand insights by answering natural language questions about market trends, volume, liquidity, and relationships between different markets. It is designed for users who want to quickly query and understand market data without manually browsing the Polymarket website.

## Use Case Examples

You can interact with the agent to perform tasks like:

*   **Get a high-level summary of market activity:**
    > "get market stats"
*   **Find specific markets based on criteria:**
    > "show me the top 5 crypto markets by volume"
*   **Get AI-powered analysis for any market:**
    > "analyze market will-bitcoin-reach-100k"
    > "insights for trump-2024-election"
*   **Get real-time election analysis with historical data:**
    > "analyze election 2026 presidential candidates"
    > "election analysis who will qualify for senate 2026"
*   **Discover related markets using symbolic reasoning:**
    > "recommendations for will-donald-trump-win-the-2024-election"

## Capabilities and APIs

The agent has several core capabilities, powered by a modular, tool-based architecture:

*   **Market Querying:** The agent can filter and sort markets based on a variety of parameters, including category, volume, liquidity, and active status. This is powered by a flexible backend API that queries a MongoDB database.
*   **AI-Powered Market Analysis:** Get comprehensive insights including risk assessment, probability analysis, and trading recommendations for any market.
*   **Real-Time Election Research:** Advanced analysis of election markets using real-time news, historical patterns, candidate tracking, and qualification predictions.
*   **Market Intelligence:** Deep analysis of market health, pricing trends, category context, and similar market comparisons.
*   **Statistical Analysis:** It can provide high-level statistics for the entire market (e.g., total volume) and for individual categories.
*   **Symbolic Reasoning (MeTTa):** Using SingularityNET's MeTTa/Hyperon, the agent can deduce complex relationships between markets. Its primary reasoning capability is to recommend markets that are thematically related (share the same category and tags) to a given market.

## Interaction Modes

This Agent is designed to be used via **direct message** through the Agentverse UI or a compatible interface like ASI:One.

## Limitations and Scope

*   This agent **provides data analysis only**. It does not offer financial advice, predictions, or opinions.
*   It **cannot execute trades** or interact with user wallets.
*   The data is based on a snapshot in the database and is updated by a separate ingestion service. It should not be used for high-frequency trading.
*   The natural language understanding is based on keyword matching and may not understand all queries.

## How It Works: The Architecture

This project is built on a clean, decoupled architecture that separates data processing, querying, and agent logic. This design makes the system scalable, maintainable, and highly extensible.

```