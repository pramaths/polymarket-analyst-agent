# Polymarket Analyst Agent

This project is an AI-powered agent built with `uagents` that can answer natural language questions about market data from Polymarket.

It is supported by a lightweight Python FastAPI backend that queries a MongoDB database. The database is intended to be populated by a separate data ingestion service (e.g., a NestJS application).

## Architecture

The system is composed of three main parts:

1.  **Data Ingestion Service (External):** A service (e.g., written in NestJS) that is responsible for fetching data from the Polymarket API and storing it in a structured format in a MongoDB database.
2.  **Python Query Backend (This Repo):** A FastAPI application that connects to the MongoDB database and exposes a powerful, flexible API. It translates HTTP query parameters into MongoDB queries.
3.  **Python Analyst Agent (This Repo):** A `uagents` agent that provides a conversational interface. It parses natural language, calls the Python Query Backend to get data, and formats the results into a human-readable response.

```
┌──────────────────┐     ┌───────────────────┐     ┌────────────────┐
│ User via         │     │                   │     │ Python Query   │
│ Agentverse UI    │ ◀───▶ │ Python Analyst    │ ◀───▶ │ Backend        │
└──────────────────┘     │ Agent (main.py)   │     │ (FastAPI)      │
                         └───────────────────┘     └───────┬────────┘
                                                         │
                                                         ▼
                                                 ┌────────────────┐
                                                 │ MongoDB        │
                                                 │ Database       │
                                                 └────────────────┘
```

## Setup Instructions

You will need two separate terminal windows for this setup: one for the backend and one for the agent.

### 1. Backend Setup

The backend is a FastAPI server that queries the database.

1.  **Navigate to the Backend Directory:**
    ```bash
    cd backend
    ```

2.  **Create a Virtual Environment:**
    ```bash
    python3 -m venv venv
    ```

3.  **Activate the Virtual Environment:**
    ```bash
    source venv/bin/activate
    ```
    *(Your terminal prompt should now show `(venv)`)*

4.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Configure Environment:**
    Create a file named `.env` inside the `backend` directory. Its content should be one line:
    ```
    MONGODB_URL="your_mongodb_connection_string_here"
    ```
    Replace the placeholder with your actual MongoDB connection string.

### 2. Agent Setup

The agent is the conversational AI that you will interact with.

1.  **Navigate to the Project Root:**
    ```bash
    # If you are in the backend directory
    cd .. 
    ```

2.  **Create a Virtual Environment:**
    *(If you don't already have one for the agent)*
    ```bash
    python3 -m venv .venv
    ```

3.  **Activate the Virtual Environment:**
    ```bash
    source .venv/bin/activate
    ```

4.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Running the Application

1.  **Start the Backend:**
    In your first terminal (with the backend's `venv` activated), run the following command from the **project root directory**:
    ```bash
    uvicorn backend.app.main:app --reload --port 8000
    ```
    *(You can change the `--port` to any value, like 5000)*

2.  **Start the Agent:**
    In your second terminal (with the agent's `.venv` activated), run the following command from the **project root directory**:
    ```bash
    python main.py
    ```

3.  **Interact with the Agent:**
    When the agent starts, it will print an "Agent inspector available at..." URL. Open this link in your browser. The inspector UI will detect the agent's chat protocol and provide you with a chat interface to send messages.

## Example Agent Queries

You can ask the agent questions like:

-   "get market stats"
-   "show me the top 5 crypto markets by volume"
-   "find active politics markets"
-   "show me markets with liquidity over 50k"
-   "find the top 3 markets sorted by liquidity"
