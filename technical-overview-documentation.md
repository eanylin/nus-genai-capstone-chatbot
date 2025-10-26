# Project APIs, Services, and Key Libraries

This document provides a technical overview of the core frameworks, external APIs, and significant Python libraries used in this project.

## 1. Core Frameworks

These are the foundational libraries that provide the project's structure and core logic.

### LangChain
* **Library:** `langchain`, `langchain-openai`, `langchain_community`, `langchain-core`
* **What it is:** A comprehensive framework for developing applications powered by large language models (LLMs). It provides components for building, managing, and deploying complex agentic systems.
* **How it is used in this project:**
    * **Main Agent (`app.py`):** The primary agent is built using LangChain's `create_react_agent` and `AgentExecutor`. This "planner" agent (powered by GPT-4) is responsible for receiving all user queries and routing them to the correct tool.
    * **Sub-Agents (`sql_agent.py`, `recommender_system.py`):** The two specialized SQL agents are created using `create_sql_agent`. These agents (powered by GPT-3.5-Turbo) are "tools" that the main agent can call.
    * **Tool Definition:** The project uses LangChain's `Tool` class to wrap all functions, chains, and agents that the main planner can use. This includes the two SQL sub-agents, the RAG chain, the weather function, and the image generation function.
    * **Memory:** `ChatMessageHistory` is used to store the conversation, allowing the agent to have context from previous messages.
    * **Database Connection:** The `SQLDatabase` utility from `langchain_community` is used to provide the SQL agents with a safe and effective way to interact with the SQLite databases.

### Streamlit
* **Library:** `streamlit`
* **What it is:** A fast and easy-to-use Python framework for building and sharing interactive web applications for machine learning and data science.
* **How it is used in this project:**
    * **User Interface:** The entire frontend and chat interface is built with Streamlit (`app.py`).
    * **Chat Elements:** `st.chat_input` is used to capture user queries, and `st.chat_message` is used to display the conversation history (from both the user and the AI).
    * **Session Management:** `st.session_state` is critically important for persisting the chat history and the LangChain agent itself across user interactions and app re-runs.
    * **Displaying Content:** Used to render all types of responses from the agent, including standard text, data (like from a SQL query), and generated images.

---

## 2. External APIs & Services

These are the third-party services that provide the project's intelligence, data, and multi-modal capabilities. Access is managed via API keys.

### OpenAI API
* **Service:** Provides access to all of OpenAI's large language and generative models.
* **How it is used in this project:**
    * **`gpt-4` (`ChatOpenAI`):** This model is used for the **main planner agent**. It is chosen for its superior reasoning and function-calling capabilities, which are essential for correctly understanding user intent and routing to the right tool (e.g., distinguishing a weather request from an event request).
    * **`gpt-3.5-turbo` (`ChatOpenAI`):** This model is used for the two **SQL sub-agents**. It is highly capable of translating natural language to SQL queries and is faster and more cost-effective than GPT-4 for this specialized task.
    * **`dall-e` models:** Used by the **image generation tool**. When the main agent identifies an image request, it calls this API to generate an image from the user's text prompt.
    * **`text-embedding` models (`OpenAIEmbeddings`):** Used by the **RAG tool**. When setting up the vector database, this model converts all source documents into numerical vectors for efficient similarity search.

### Weather API
* **Service:** A third-party API using WeatherAPI that provides real-time meteorological data.
* **How it is used in this project:**
    * A simple Python function is written to call this API.
    * This function is wrapped in a LangChain `Tool` and given to the main agent.
    * The agent learns to call this tool whenever the user asks for the weather, passing the extracted city name as an argument.

---

## 3. Key Python Libraries & Utilities

### RAG (Retrieval-Augmented Generation)
* **Libraries:** (e.g., `faiss-cpu`, `chromadb`, `pypdf`, `unstructured`)
* **What it is:** A collection of libraries used to build the RAG pipeline, which allows the agent to answer questions from a private knowledge base.
* **How it is used in this project:**
    * **Document Loaders** (e.g., `pypdf`): Used in a setup script (like `setup_rag.py`) to read text from your custom files (PDFs, .txt, etc.).
    * **Text Splitters:** Used to break large documents into smaller, semantically meaningful chunks.
    * **Vector Store** (e.g., `faiss-cpu`): A database that stores the vector embeddings of the document chunks.
    * **Retriever:** The vector store is wrapped in a `create_retrieval_chain` which is then exposed as a `Tool` for the main agent. When called, it finds the most relevant document chunks and synthesizes an answer.

### SQLite3
* **Library:** `sqlite3`
* **What it is:** A built-in Python library for creating and interacting with serverless, file-based SQL databases.
* **How it is used in this project:**
    * **Database Setup:** Used in `setup_db.py` and `setup_events_db.py` to create the `company.db` and `events.db` files.
    * **Populating Data:** Used to execute `INSERT` statements to populate the tables with sample data.
    * **Agent Connection:** The LangChain `SQLDatabase` class connects to these `.db` files, allowing the SQL agents to run `SELECT` queries on them.

### Python-DotEnv
* **Library:** `python-dotenv`
* **What it is:** A simple utility that loads environment variables from a `.env` file into the application's environment.
* **How it is used in this project:**
    * `load_dotenv()` is called at the beginning of `app.py`.
    * This securely loads the `OPENAI_API_KEY` and `WEATHER_API_KEY` from the `.env` file, so they are not hard-coded in the source code.

### OS
* **Library:** `os`
* **What it is:** A built-in Python library for interacting with the operating system.
* **How it is used in this project:**
    * `os.getenv("OPENAI_API_KEY")` is used to read the API keys that were loaded by `python-dotenv`. This value is then passed to the OpenAI and LangChain clients.
