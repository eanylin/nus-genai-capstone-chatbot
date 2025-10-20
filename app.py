import json
import os
import requests
import streamlit as st
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.chains import ConversationalRetrievalChain, LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.vectorstores import FAISS
from langchain.document_loaders import UnstructuredFileLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate, ChatPromptTemplate

# Import Agent and Tool components
from langchain.agents import AgentExecutor, Tool, create_openai_functions_agent
from langchain_community.tools.ddg_search import DuckDuckGoSearchRun
from langchain_community.utilities.dalle_image_generator import DallEAPIWrapper
from langchain_core.messages import SystemMessage

# Import custom agents
from sql_agent import query_agent 
from recommender_system import run_event_recommender

# Page Configuration
st.set_page_config(
    page_title="🤖 Multi-Tool AI Agent",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 Multi-Tool AI Agent")
st.markdown("This agent can query your documentation, get weather, find events or draw images")

# API Key Setup
st.sidebar.header("Configuration")
api_key = st.sidebar.text_input("Enter your OpenAI API Key:", type="password")
weather_api_key = st.sidebar.text_input("Enter your WeatherAPI Key:", type="password")

if not api_key or not weather_api_key:
    st.info("Please enter your OpenAI API key and WeatherAPI key in the sidebar to start.")
    st.stop()

os.environ["OPENAI_API_KEY"] = api_key

# Document Upload
st.sidebar.header("Upload Documents for RAG")
uploaded_files = st.sidebar.file_uploader(
    "Upload your documents (PDF, TXT, etc.)", 
    type=["pdf", "txt", "md", "docx"], 
    accept_multiple_files=True
)

# Caching Function for Vector Store
@st.cache_resource
def create_vectorstore(files):
    """Create a FAISS vector store from uploaded files."""
    if not files:
        return None
    
    with st.spinner("Processing documents, creating embeddings..."):
        try:
            docs = []
            temp_dir = "temp_docs"
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)

            for file in files:
                temp_path = os.path.join(temp_dir, file.name)
                with open(temp_path, "wb") as f:
                    f.write(file.getvalue())
                loader = UnstructuredFileLoader(temp_path)
                docs.extend(loader.load())

            text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
            splits = text_splitter.split_documents(docs)
            
            if not splits:
                st.error("Could not split documents. Please check file content.")
                return None

            embeddings = OpenAIEmbeddings()
            vectorstore = FAISS.from_documents(splits, embeddings)
            
            for file in files:
                os.remove(os.path.join(temp_dir, file.name))
            os.rmdir(temp_dir)
            
            st.success("Knowledge base created successfully!")
            return vectorstore

        except Exception as e:
            st.error(f"Error creating vector store: {e}")
            return None

# Create RAG Chain (will be wrapped in a tool)
vectorstore = create_vectorstore(uploaded_files)

# Initialize LLM
llm = ChatOpenAI(model_name="gpt-4-turbo", temperature=0.1)

# Initialize Memory
if "memory" not in st.session_state:
    st.session_state.memory = ConversationBufferMemory(
        memory_key="chat_history", 
        return_messages=True
    )
memory = st.session_state.memory

# Create the RAG chain
if vectorstore:
    retriever = vectorstore.as_retriever()
    rag_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        verbose=True
    )
else:
    rag_chain = None


# Agent and Tools Setup
# Tool Function 1: RAG
def run_rag_chain(query: str) -> str:
    """Runs the RAG chain for document questions."""
    st.write(f"🧠 *Querying knowledge base for: '{query}'*")
    print(f"--- RAG TOOL CALLED with query: {query} ---")
    
    if not rag_chain:
        print("--- RAG Tool FAILED: rag_chain not initialized. ---")
        return "Error: The document knowledge base is not initialized. Please tell the user to upload documents first."
    
    try:
        response = rag_chain.invoke({"question": query})
        answer = response.get("answer")

        if not answer or "don't know" in answer.lower() or "no information" in answer.lower():
             print("--- RAG Tool found no relevant documents. ---")
             return f"The documents do not contain specific information about: '{query}'. Tell the user you couldn't find the answer in their files."
        
        print(f"--- RAG Tool SUCCESS, returning answer. ---")
        return answer
    except Exception as e:
        print(f"--- RAG Tool FAILED: {e} ---")
        return f"Error occurred while searching documents: {e}"

# Tool Function 2: Image Generation
image_prompt_template = PromptTemplate(
    input_variables=["image_desc"],
    template=(
        "You are a helpful prompt-engineering assistant. A user wants to generate an image based on this description: '{image_desc}'. "
        "Generate a highly detailed, vivid, and specific prompt for the DALL-E 3 image generation model."
    )
)
prompt_engineering_chain = LLMChain(llm=llm, prompt=image_prompt_template)

def generate_engineered_image(prompt: str) -> str:
    """Generates an image and returns a Markdown string."""
    st.write(f"🖌️ *Crafting a detailed image prompt...*")
    engineered_prompt = prompt_engineering_chain.run(prompt)
    st.write(f"**Detailed Prompt:** {engineered_prompt}")
    
    st.write(f"🎨 *Sending to DALL-E 3...*")
    dalle_wrapper = DallEAPIWrapper()
    try:
        image_url = dalle_wrapper.run(engineered_prompt)
        st.write("✅ Image generated!")
        return f"![Generated image: {prompt}]({image_url})"
        
    except Exception as e:
        print(f"--- DALL-E Tool FAILED: {e} ---")
        return f"Error generating image: {e}. The prompt might have been rejected by the safety system."

# Tool Function 3: Simple Weather
def get_current_weather(location: str) -> str:
    """Gets the *current* weather for a location using weatherapi.com."""
    st.write(f"🌦️ *Checking weather for: '{location}'*")
    print(f"--- Weather Tool CALLED with location: {location} ---")
    
    base_url = "https://api.weatherapi.com/v1/current.json"
    params = {
        "key": weather_api_key, 
        "q": location
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status() 
        data = response.json()
        
        loc_name = data['location']['name']
        region = data['location']['region']
        country = data['location']['country']
        temp_c = data['current']['temp_c']
        temp_f = data['current']['temp_f']
        condition = data['current']['condition']['text']
        
        result = (
            f"Current weather in {loc_name}, {region}, {country}: "
            f"{temp_c}°C / {temp_f}°F, {condition}."
        )
        print(f"--- Weather Tool SUCCESS: {result} ---")
        return result
        
    except requests.exceptions.HTTPError as http_err:
        print(f"--- Weather Tool HTTP Error: {http_err} ---")
        try:
            error_msg = response.json()['error']['message']
            return f"Error getting weather: {error_msg}"
        except Exception:
            return f"Error getting weather: HTTP {http_err.response.status_code}"
    except Exception as e:
        print(f"--- Weather Tool FAILED: {e} ---")
        return f"An error occurred while trying to get the weather: {e}"

# Initialize Tools List
tools = []

# Tool 1: RAG
if rag_chain:
    tools.append(
        Tool(
            name="DocumentKnowledgeBase",
            func=run_rag_chain,
            description=(
                "Use this tool ONLY for questions about the user's **uploaded files** (PDFs, TXT, DOCX). "
                "This is for querying **unstructured text**. "
                "This tool has access to the user's private files."
            )
        )
    )

# Tool 2: SQL Database
tools.append(
    Tool(
        name="DatabaseQuery",
        # Use a lambda function to pass the 'llm' object to your agent
        func=lambda q: query_agent(question=q, llm=llm),
        description=(
            "Use this tool ONLY for questions about employees, departments, salaries, or budgets. "
            "Examples: 'Who has the highest salary?', 'What is the budget for the Engineering department?'"
        )
    )
)

# Tool 3: Event Recommender
tools.append(
    Tool(
        name="EventRecommender",
        # Use a lambda to pass all required arguments
        func=lambda location: run_event_recommender(
            location=location, 
            llm=llm, 
            weather_key=weather_api_key
        ),
        description=(
            "Use this tool ONLY when the user asks for event recommendations, "
            "'what to do', or 'things to do' for **today**. "
            "This tool will find events from a database and check the weather. "
            "The input must be a location (e.g., 'Singapore')."
        )
    )
)

# Tool 4: Simple Weather
tools.append(
    Tool(
        name="CurrentWeather",
        func=get_current_weather,
        description=(
            "Use this tool ONLY when the user asks *just* for the current weather, "
            "weather forecast, or temperature for a specific location. "
            "Do NOT use this if they are also asking for event recommendations."
        )
    )
)

# Tool 5: Image Generation
tools.append(
    Tool(
        name="ImageGenerator",
        func=generate_engineered_image,
        description="Use this tool ONLY when a user explicitly asks to create, draw, generate, show an image, picture or drawing."
    )
)

# Tool 6: General Search for anything else
tools.append(DuckDuckGoSearchRun())


# System Prompt
system_prompt = SystemMessage(
    content=(
        "You are a helpful, multi-function assistant. You must follow this priority list for every user query:\n\n"
        
        "1.  **Check for Document Question:** Is the user asking a specific question *about* their uploaded documents? "
        "If YES, you MUST use the `DocumentKnowledgeBase` tool.\n"

        "2.  **Check for Database Question:** Is the user asking about *employees, departments, salaries or budgets*? "
        "If YES, you MUST use the `DatabaseQuery` tool.\n"
        
        "3.  **Check for Event Recommendation:** Is the user asking for event recommendations, 'what to do' or 'things to do' for **today**? "
        "If YES, you MUST use the `EventRecommender` tool.\n"

        "4.  **Check for *only* Weather:** Is the user asking *just* for the current weather? "
        "If YES, you MUST use the `CurrentWeather` tool.\n"
        
        "5.  **Check for Image Request:** Is the user asking to create or draw an image? "
        "If YES, you MUST use the `ImageGenerator` tool.\n"
        
        "6.  **General Knowledge (Fallback):** If the request is a general question NOT covered by any other tool, "
        "you MUST use the `DuckDuckGoSearch` tool.\n"
        
        "7.  **No Tool:** If you can answer without any tools (like 'hello'), do so directly."
    )
)

# Initialize Agent
agent_prompt = ChatPromptTemplate.from_messages([
    system_prompt,
    ("placeholder", "{chat_history}"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])

try:
    agent = create_openai_functions_agent(llm, tools, agent_prompt)
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=tools, 
        memory=memory, 
        verbose=True,
        handle_parsing_errors=True 
    )
except Exception as e:
    st.error(f"Error initializing the agent: {e}")
    st.stop()


# Chat History Display
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# Chat Input and Response
if prompt := st.chat_input("Ask about docs, DB, weather, events, or request a drawing..."):
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Agent is thinking..."):
            try:
                response = agent_executor.invoke({"input": prompt})
                ai_response = response["output"]

                st.markdown(ai_response)
                st.session_state.messages.append({"role": "assistant", "content": ai_response})
            
            except Exception as e:
                error_message = f"An error occurred: {e}"
                st.error(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})
