from crewai import Agent, Task, Crew, Process, LLM
from crewai_tools import FileReadTool
from crewai.knowledge.source.pdf_knowledge_source import PDFKnowledgeSource
import os
from textwrap import dedent
from dotenv import load_dotenv
load_dotenv()

#--------------------------------#
#         LLM & Research Agent   #
#--------------------------------#
def create_code_extractor_crew(selection, files):
    # Instantiate knowledge source
    pdf_knowledge_source = PDFKnowledgeSource(
        file_paths=['37_Requirements_10_Best_Practices.pdf'])

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
    code_parser_agent = Agent(
        role='Code Parser',
        goal=dedent(f"""Parse and extract structural information from C code files.
            Code:
            {files}"""),
        backstory=dedent("""
            You are a meticulous code parser, expert in dissecting C code and extracting key structural elements. 
            You have an eagle eye for detail and can identify even the most subtle nuances in code syntax and 
            organization."""),
        verbose=True,
        llm=llm,
    )
    control_flow_analyzer_agent = Agent(
        role='Control Flow Analyzer Agent',
        goal='Analyze the control flow within the C code.',
        backstory=dedent("""
            You are a seasoned control flow expert, capable of tracing the execution paths of complex C code. 
            You have a deep understanding of program behavior and can identify potential issues and predict outcomes."""),
        verbose=True,
        llm=llm,
    )
    data_flow_analyzer_agent = Agent(
        role='Data Flow Analyzer Agent',
        goal='Track the flow of data through the C code.',
        backstory=dedent("""You are a master of data flow analysis, able to track how information moves through C code. 
            You can identify dependencies, transformations, and potential bottlenecks in the data flow."""),
        verbose=True,
        llm=llm,
    )
    requirement_synthesizer_agent = Agent(
        role='Requirement Synthesizer Agent',
        goal='Generate requirement statements based on the analysis from other agents.',
        backstory=dedent("""You are a skilled requirement engineer, adept at translating technical details into clear, 
            concise, and testable requirements. You can synthesize information from various sources to create a 
            comprehensive set of requirements. You are known for your ability to bridge the gap between code and 
            documentation. You understand the difference between functional and non-functional requirements and can 
            capture them accurately. You are familiar with requirements engineering best practices."""),
        verbose=True,
        knowledge_sources=[pdf_knowledge_source],
        llm=llm,
    )
    requirement_validator_agent = Agent(
        role='Requirement Validator Agent',
        goal='Verify the generated requirements against the original C code.',
        backstory=dedent("""You are a rigorous quality assurance expert, dedicated to ensuring the accuracy and 
            completeness of requirements. You have a keen eye for inconsistencies and can identify gaps between code 
            and documentation."""),
        verbose=True,
        knowledge_sources=[pdf_knowledge_source],
        llm=llm,
    )
    code_extractor_agents = [code_parser_agent, control_flow_analyzer_agent, data_flow_analyzer_agent,
                             requirement_synthesizer_agent, requirement_validator_agent]
    return code_extractor_agents

#--------------------------------#
#         Research Task          #
#--------------------------------#
def create_code_extractor_tasks(agents, user_prompt):
    parse_code_task = Task(
        description=dedent(f"""User Input: {user_prompt}
                    Parse all of the C code files in the directory and extract the Abstract Syntax Tree (AST). 
                    The AST should capture the structure and relationships between different elements in the code."""),
        expected_output=dedent(f"""A JSON representation of the AST."""),
        output_file='output/code_extractor/ast.json',
        agent=agents[0]
    )
    analyze_control_flow_task = Task(
        description=dedent(f"""User Input: {user_prompt}
                    Analyze the control flow of the code using the AST. Identify loops, conditionals, and 
                    function calls. Determine the possible execution paths."""),
        expected_output=dedent(f"""A description of the control flow paths and dependencies."""),
        output_file="output/code_extractor/control_flow_analysis.md",
        agent=agents[1]
    )
    analyze_data_flow_task = Task(
        description=dedent(f"""User Input: {user_prompt}
                    Analyze the data flow of the code using the AST. Identify variable assignments,
                    data dependencies, and data transformations."""),
        expected_output=dedent(f"""A list of at least 10 creative ideas, prioritized with a short justification for each."""),
        output_file="output/code_extractor/data_flow_analysis.md",
        agent=agents[2]
    )
    synthesize_requirements_task = Task(
        description=dedent(f"""User Input: {user_prompt}
                    Using the control and data flow analysis, generate a set of initial requirement statements. 
                    Requirements should be clear,concise, and testable. Include both functional and non-functional 
                    requirements. Use requirements engineering best practices."""),
        expected_output=dedent(f"""A set of requirement statements. Each requirement should be formatted as follows:
                    - Requirement ID: A unique identifier for the requirement.
                    - Requirement Statement: A clear and concise description of the requirement.
                    - Priority: The importance or urgency of the requirement (e.g., high, medium, low).
                    - Type: The type of requirement (e.g., functional, non-functional).
                    - Source: The analysis or code element that the requirement is derived from."""),
        output_file="output/code_extractor/code_requirements.md",
        agent=agents[3]
    )
    validate_requirements_task = Task(
        description=dedent(f"""User Input: {user_prompt}
                    Validate the generated requirement statements against the original code. Ensure that each
                    requirement is traceable to a specific code element and accurately reflects the intended behavior.
                    Identify any discrepancies or missing requirements."""),
        expected_output=dedent(f"""A set of validated requirement statements. Each requirement should be formatted as follows:
                    - Requirement ID: A unique identifier for the requirement.
                    - Requirement Statement: A clear and concise description of the requirement.
                    - Priority: The importance or urgency of the requirement (e.g., high, medium, low).
                    - Type: The type of requirement (e.g., functional, non-functional).
                    - Source: The analysis or code element that the requirement is derived from."""),
        output_file="output/code_extractor/validated_requirements.md",
        agent=agents[4]
    )
    code_extractor_tasks = [parse_code_task, analyze_control_flow_task, analyze_data_flow_task,
                            synthesize_requirements_task, validate_requirements_task]
    return code_extractor_tasks


#--------------------------------#
#         Research Crew          #
#--------------------------------#
def run_code_extractor(code_extractor_agents, code_extractor_tasks):
    crew = Crew(
        agents=code_extractor_agents,
        tasks=code_extractor_tasks,
        verbose=True,
        process=Process.sequential
    )
    return crew.kickoff()
