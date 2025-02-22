import streamlit as st
import os
import requests
from dotenv import load_dotenv
load_dotenv()

#--------------------------------#
#      Ollama Integration        #
#--------------------------------#
def get_ollama_models():
    """Get list of available Ollama models from local instance.
    
    Returns:
        list: Names of available Ollama models, or empty list if Ollama is not running
    """
    try:
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            models = response.json()
            return [model["name"] for model in models["models"]]
        return []
    except:
        return []

#--------------------------------#
#      Sidebar Configuration     #
#--------------------------------#
def render_sidebar():
    """Render the sidebar and handle API key & model configuration.
    
    The sidebar allows users to:
    1. Select an LLM provider (OpenAI, Anthropic, or Ollama)
    2. Choose or input a specific model
    3. Enter necessary API keys
    
    Returns:
        dict: Contains selected provider and model information
    """
    with st.sidebar:
        st.markdown("### ⚙️ Configuration")
        st.write("")

        with st.expander("🔍 Agentic Crew", expanded=True):
            agentic_crew = st.radio(
                "Select Crew",
                ["Research Assistant", "Design Thinking", "Code Extractor"],
                horizontal=True
            )

            if agentic_crew == "Research Assistant":
                agentic_option = "research_assistant"
            elif agentic_crew == "Design Thinking":
                agentic_option = "design_thinking"
            else:
                agentic_option = "code_extractor"

        with st.expander("🤖 Model Selection", expanded=True):
            provider = st.radio(
                "Select LLM Provider",
                ["OpenAI", "Anthropic", "Gemini", "Ollama"],
                help="Choose which Large Language Model provider to use",
                horizontal=True
            )
            
            if provider == "OpenAI":
                model_option = st.selectbox(
                    "Select OpenAI Model",
                    ["gpt-4o-mini", "gpt-4o", "o1", "o1-mini", "o1-preview", "o3-mini", "Custom"],
                    index=0
                )
                if model_option == "Custom":
                    model = st.text_input("Enter your custom OpenAI model:", value="", help="Specify your custom model string")
                else:
                    model = model_option
            elif provider == "Ollama":
                # Get available Ollama models
                ollama_models = get_ollama_models()
                if not ollama_models:
                    st.warning("⚠️ No Ollama models found. Make sure Ollama is running locally.")
                    model = None
                else:
                    st.warning("⚠️ Note: Most Ollama models have limited function-calling capabilities. This may affect research quality as they might not effectively use web search tools.")
                    model = st.selectbox(
                        "Select Ollama Model",
                        ollama_models,
                        help="Choose from your locally available Ollama models. For best results, use models known to handle function calling well (e.g., mixtral, openhermes)."
                    )
            elif provider == "Anthropic":
                model_option = st.selectbox(
                    "Select Anthropic Model",
                    ["claude-3-haiku-20240307", "claude-3-sonnet-20240229", "claude-3-opus-20240229",
                     "claude-3-5-haiku-20241022", "claude-3-5-sonnet-20241022"],
                    index=0
                )
                if model_option == "Custom":
                    model = st.text_input("Enter your custom Anthropic model:", value="", help="Specify your custom model string")
                else:
                    model = model_option
            elif provider == "Gemini":
                model_option = st.selectbox(
                    "Select Gemini Model",
                    ["gemini-1.5-pro", "gemini-1.5-flash-8b", "gemini-1.5-flash",
                     "gemini-2.0-flash-lite-preview-02-05", "gemini-2.0-flash"],
                    index=0
                )
                if model_option == "Custom":
                    model = st.text_input("Enter your custom Anthropic model:", value="", help="Specify your custom model string")
                else:
                    model = model_option
            else:
                # For Anthropic, use the default model string
                model = "claude-3-haiku-20240307"
        
        with st.expander("🔑 API Keys", expanded=True):
            st.info("API keys are stored temporarily in memory and cleared when you close the browser.")
            if provider == "OpenAI":
                openai_api_key = st.text_input(
                    "OpenAI API Key",
                    type="password",
                    value=os.getenv("OPENAI_API_KEY"),
                    help="Enter your OpenAI API key"
                )
                if openai_api_key:
                    os.environ["OPENAI_API_KEY"] = openai_api_key
            elif provider == "Anthropic":
                anthropic_api_key = st.text_input(
                    "ANTHROPIC API Key",
                    type="password",
                    value=os.getenv("ANTHROPIC_API_KEY"),
                    help="Enter your ANTHROPIC API key"
                )
                if anthropic_api_key:
                    os.environ["ANTHROPIC_API_KEY"] = anthropic_api_key
            elif provider == "Gemini":
                gemini_api_key = st.text_input(
                    "GEMINI API Key",
                    type="password",
                    value=os.getenv("GEMINI_API_KEY"),
                    help="Enter your Gemini API key"
                )
                if gemini_api_key:
                    os.environ["GEMINI_API_KEY"] = gemini_api_key
            
            # Only show EXA key input if not using Ollama
            if provider != "Ollama":
                exa_api_key = st.text_input(
                    "EXA API Key",
                    type="password",
                    value=os.getenv("EXA_API_KEY"),
                    help="Enter your EXA API key for web search capabilities"
                )
                if exa_api_key:
                    os.environ["EXA_API_KEY"] = exa_api_key

        st.write("")
        with st.expander("ℹ️ About", expanded=False):
            st.markdown("""
                This research assistant uses advanced AI models to help you:
                - Research any topic in depth
                - Analyze and summarize information
                - Provide structured reports
                
                Choose your preferred model and enter the required API keys to get started.
                
                **Note on Model Selection:**
                - OpenAI and Anthropic models provide full functionality with web search capabilities
                - Ollama models run locally but have limited function-calling abilities
                  and will rely more on their base knowledge
                
                For Ollama users:
                - Make sure Ollama is running locally with your desired models loaded
                - Best results with models that handle function calling (e.g., mixtral, openhermes)
                - Web search functionality is disabled for Ollama models
            """)
    return {
        "provider": provider,
        "model": model,
        "agentic_option": agentic_option
    }