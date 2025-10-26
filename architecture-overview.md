# Project Architecture Overview

This project uses a **hierarchical agent** (also known as an "agent-of-agents") architecture. This modern design pattern involves a high-level "planner" agent that delegates tasks to a set of specialized "worker" tools.

This approach is more robust, modular, and efficient than using a single, monolithic agent. It allows for a clear separation of concerns, where specialized tasks (like SQL queries or RAG) are handled by fine-tuned components, while a powerful reasoning model (GPT-4) manages the overall conversation and task routing.


---

## Core Components

The system is composed of four main layers: the User Interface, the Main Agent (Planner), the Toolset (Workers), and the Data Sources.

### 1. User Interface (Streamlit)
* **File:** `app.py`
* **Framework:** **Streamlit**
* **Purpose:** Provides the web-based chat interface for the user.
* **Key Functions:**
    * Renders the chat history.
    * Accepts user input using `st.chat_input`.
    * Persists the conversation history and the agent instance across re-runs using `st.session_state`.
    * Displays all forms of output, including text, data, and images.

### 2. Main Agent (The "Planner")
* **File:** `app.py`
* **Framework:** LangChain (`create_react_agent`, `AgentExecutor`)
* **Model:** **GPT-4**
* **Purpose:** This is the "brain" of the operation. It does not answer questions directly. Instead, its sole purpose is to analyze the user's query (and the chat history) and decide which tool from its toolset is best suited to handle the request. It is basically acting as a router.

### 3. The Toolset (The "Workers")
This is the collection of specialized tools that the Main Agent can choose from. These tools are a mix of sub-agents, chains, and simple Python functions.

* **Company SQL Agent (Agent-as-Tool)**
    * **File:** `sql_agent.py`
    * **Framework:** LangChain (`create_sql_agent`)
    * **Model:** **GPT-3.5-Turbo**
    * **Function:** A specialized agent that can translate natural language into SQL queries to run against the `company.db`.

* **Events Recommender Agent (Agent-as-Tool)**
    * **File:** `recommender_system.py`
    * **Framework:** LangChain (`create_sql_agent`)
    * **Model:** **GPT-3.5-Turbo**
    * **Function:** A specialized agent that translates natural language into SQL queries to run against the `events.db`.

* **Knowledge Base Retriever (Chain-as-Tool)**
    * **Framework:** LangChain (`create_retrieval_chain`)
    * **Function:** A Retrieval-Augmented Generation (RAG) pipeline. It retrieves relevant text chunks from a pre-built vector database and synthesizes an answer.

* **Weather Tool (Function-as-Tool)**
    * **Framework:** A standard Python function wrapped in a LangChain `Tool`.
    * **Function:** Takes a city name, calls an external Weather API, and returns the current weather data.

* **Image Generation Tool (Function-as-Tool)**
    * **Framework:** A Python function wrapped in a LangChain `Tool`.
    * **Function:** Takes a text prompt, calls the OpenAI **DALL-E** API, and returns the URL of a generated image.

### 4. Data Sources
* **`company.db` (SQLite):** A SQL database containing employee information (salaries, departments, etc.).
* **`events.db` (SQLite):** A SQL database containing event information (dates, locations, topics).
* **Vector Database (Chroma/FAISS):** A vector store containing the embeddings of our private documents for the RAG tool.
* **External APIs:** The OpenAI API (for all LLM and DALL-E calls) and the Weather API.

---

## Step-by-Step Data Flow

Here is the lifecycle of a single user query:

1.  A user types a message (e.g., "What's the weather in London?") into the Streamlit UI.
2.  Streamlit (`app.py`) takes this prompt and the chat history from `st.session_state`.
3.  The prompt and history are passed to the **Main Agent (GPT-4)**.
4.  The agent *reasons* about the query. It thinks: "The user is asking for the weather. I should use the `Weather Tool`. The city is 'Singapore'."
5.  The agent invokes the **`Weather Tool`** with the argument `"Singapore"`.
6.  The `Weather Tool` (a Python function) executes: it calls the external Weather API and gets back a JSON response (e.g., `{"temp": 31, "conditions": "Cloudy"}`).
7.  This JSON response is returned to the **Main Agent**.
8.  The Main Agent *reasons* again: "The tool gave me `{'temp': 31, 'conditions': 'Cloudy'}`. I need to format this as a nice, human-readable answer."
9.  The Main Agent formulates the final response: "The weather in Singapore is currently 31°C and cloudy."
10. This final response is sent back to Streamlit, which displays it in the chat window.

---

## Architectural Justification

* **Separation of Concerns:** Each tool is an expert at one job. The SQL agent doesn't know how to get weather, and the weather tool doesn't know what's in the database. This makes the system easy to debug and extend.
* **Performance & Cost:** We use the expensive, powerful **GPT-4** *only* for the high-level routing. The more frequent, specialized tasks (like generating SQL) are offloaded to the faster, cheaper **GPT-3.5-Turbo** model, optimizing both speed and cost.
* **Scalability:** To add a new capability (e.g., a stock market API), we can simply create a new Python function, wrap it as a `Tool`, and add it to the Main Agent's tool list. The rest of the architecture remains unchanged.
