from src.tools.custom_tool import EXAAnswerTool
from crewai import Agent, Task, Crew, Process, LLM
import os
from dotenv import load_dotenv
load_dotenv()

#--------------------------------#
#         LLM & Research Agent   #
#--------------------------------#
def create_researcher(selection):
    """Create a research agent with the specified LLM configuration.
    
    Args:
        selection (dict): Contains provider and model information
            - provider (str): The LLM provider ("OpenAI", "GROQ", or "Ollama")
            - model (str): The model identifier or name
    
    Returns:
        Agent: A configured CrewAI agent ready for research tasks
    
    Note:
        Ollama models have limited function-calling capabilities. When using Ollama,
        the agent will rely more on its base knowledge and may not effectively use
        external tools like web search.
    """
    provider = selection["provider"]
    model = selection["model"]
    if provider == "Anthropic":
        llm = LLM(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            model=f"anthropic/{model}",
            temperature=0.7
        )
    elif provider == "Ollama":
        llm = LLM(
            base_url="http://localhost:11434",
            model=f"ollama/{model}",
        )
    elif provider == "Gemini":
        llm = LLM(
            api_key=os.getenv("GEMINI_API_KEY"),
            model=f"gemini/{model}",
        )
    else:
        # Map friendly names to concrete model names for OpenAI
        if model == "GPT-3.5":
            model = "gpt-3.5-turbo"
        elif model == "GPT-4":
            model = "gpt-4"
        elif model == "o1":
            model = "o1"
        elif model == "o1-mini":
            model = "o1-mini"
        elif model == "o1-preview":
            model = "o1-preview"
        # If model is custom but empty, fallback
        if not model:
            model = "o1"
        llm = LLM(
            api_key=os.getenv("OPENAI_API_KEY"),
            model=f"openai/{model}"
        )

    researcher = Agent(
        role='Research Analyst',
        goal='Conduct thorough research on given topics for the current year 2025',
        backstory='Expert at analyzing and summarizing complex information',
        tools=[EXAAnswerTool()],
        llm=llm,
        verbose=True
    )
    return researcher

#--------------------------------#
#         Research Task          #
#--------------------------------#
def create_research_task(researcher, task_description):
    """Create a research task for the agent to execute.
    
    Args:
        researcher (Agent): The research agent that will perform the task
        task_description (str): The research query or topic to investigate
    
    Returns:
        Task: A configured CrewAI task with expected output format
    """
    return Task(
        description=task_description,
        expected_output="""A comprehensive research report for the year 2025. 
        The report must be detailed yet concise, focusing on the most significant and impactful findings.
        
        Format the output in clean markdown (without code block markers or backticks) using the following structure:

        # Executive Summary
        - Brief overview of the research topic (2-3 sentences)
        - Key highlights and main conclusions
        - Significance of the findings

        # Key Findings
        - Major discoveries and developments
        - Market trends and industry impacts
        - Statistical data and metrics (when available)
        - Technological advancements
        - Challenges and opportunities

        # Analysis
        - Detailed examination of each key finding
        - Comparative analysis with previous developments
        - Industry expert opinions and insights
        - Market implications and business impact

        # Future Implications
        - Short-term impacts (next 6-12 months)
        - Long-term projections
        - Potential disruptions and innovations
        - Emerging trends to watch

        # Recommendations
        - Strategic suggestions for stakeholders
        - Action items and next steps
        - Risk mitigation strategies
        - Investment or focus areas

        # Citations
        - List all sources with titles and URLs
        - Include publication dates when available
        - Prioritize recent and authoritative sources
        - Format as: "[Title] (URL) - [Publication Date if available]"

        Note: Ensure all information is current and relevant to 2025. Include specific dates, 
        numbers, and metrics whenever possible to support findings. All claims should be properly 
        cited using the sources discovered during research.
        """,
        agent=researcher,
        output_file="output/researcher/research_report.md"
    )

#--------------------------------#
#         Research Crew          #
#--------------------------------#
def run_research(researcher, task):
    """Execute the research task using the configured agent.
    
    Args:
        researcher (Agent): The research agent to perform the task
        task (Task): The research task to execute
    
    Returns:
        str: The research results in markdown format
    """
    crew = Crew(
        agents=[researcher],
        tasks=[task],
        verbose=True,
        process=Process.sequential,
    )
    return crew.kickoff()
