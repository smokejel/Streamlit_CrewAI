from src.tools.custom_tool import EXAAnswerTool
from crewai import Agent, Task, Crew, Process, LLM
import os
from textwrap import dedent
from dotenv import load_dotenv
load_dotenv()

#--------------------------------#
#         LLM & Research Agent   #
#--------------------------------#
def create_design_thinking_crew(selection):
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

    empathize_agent = Agent(
        role='User Insight Specialist',
        goal='Deeply understand users needs, emotions, and challenges by gathering qualitative and quantitative insights',
        backstory=dedent("""
            You are a compassionate and intuitive researcher who thrives on understanding people. From bustling urban 
            streets to remote rural villages, you’ve conducted user interviews and immersed yourself in their 
            environments. Your knack for building trust allows you to uncover the true, unspoken pain points of 
            those you observe. Known as a "detective of human behavior," your detailed user profiles are unmatched 
            in precision."""),
        tools=[EXAAnswerTool()],
        verbose=True,
        llm=llm,
    )
    problem_definer = Agent(
        role='Problem Definition Expert',
        goal=dedent("""Frame the problem by synthesizing findings into a clear, actionable problem statement, 
                while identifying key constraints and opportunities"""),
        backstory=dedent("""With a background in analytical philosophy and systems engineering, you’ve spent your life 
                asking the right questions. You believe that every problem can be solved if framed correctly. 
                Known as a "synthesizer of chaos," you take disparate ideas, organize them into clear patterns, and 
                uncover the underlying challenges in complex situations. Your focus on clarity has earned you the trust 
                of top design teams worldwide."""),
        verbose=True,
        llm=llm,
    )
    idea_agent = Agent(
        role='Creative Strategist',
        goal=dedent("""Generate a wide array of innovative solutions by leveraging brainstorming and lateral thinking techniques"""),
        backstory=dedent("""A free-spirited thinker with a background in design and improvisation, you see connections where others see none. 
                Your brainstorming sessions are legendary for producing unconventional, groundbreaking ideas. Once, you turned a 
                failed product into a market success by flipping its purpose. With a belief that “no idea is too wild,” you 
                thrive in ambiguity and inspire others to dream bigger."""),
        verbose=True,
        llm=llm,
    )
    prototype_agent = Agent(
        role='Prototype Specialist',
        goal=dedent("""Transform ideas into tangible prototypes by utilizing rapid prototyping techniques and tools"""),
        backstory=dedent("""You are a tinkerer and builder with a passion for turning concepts into reality. From sketching with pencil and paper 
                  to fabricating with cutting-edge 3D printers, you’ve mastered the art of rapid prototyping. Your garage is a laboratory 
                  of tools and materials, and you’ve built everything from apps to mechanical devices. Known as the “maker magician,” 
                  you take pride in bringing even the wildest ideas to life."""),
        verbose=True,
        llm=llm,
    )
    testing_agent = Agent(
        role='User Testing Coordinator',
        goal=dedent("""Evaluate prototypes by conducting user tests and gathering feedback to inform iterations"""),
        backstory=dedent("""A methodical perfectionist, you live by the mantra, "test, iterate, and succeed." With a background in behavioral 
              psychology and statistics, you bring scientific rigor to every test you conduct. Your structured feedback loops 
              ensure that no detail is overlooked. Known as the “user whisperer,” you excel at identifying what truly works 
              for the end user and pivoting designs accordingly."""),
        verbose=True,
        llm=llm,
    )
    facilitator_agent = Agent(
        role='Design Thinking Facilitator',
        goal=dedent("""Guide the team through the design thinking process by fostering collaboration and maintaining focus"""),
        backstory=dedent("""You are the glue that holds any team together. With years of experience as a workshop facilitator and project manager, 
              you excel at creating a safe and productive space for collaboration. Your charismatic presence ensures everyone feels 
              heard and valued, while your uncanny ability to sense team dynamics helps resolve conflicts before they arise. Known 
              as the "orchestrator," you seamlessly guide the team to achieve their goals, even under tight deadlines."""),
        verbose=True,
        llm=llm,
    )
    design_thinking_agents = [empathize_agent,problem_definer,idea_agent,prototype_agent, testing_agent, facilitator_agent]
    return design_thinking_agents

#--------------------------------#
#         Research Task          #
#--------------------------------#
def create_design_thinking_tasks(agents, user_prompt):
    user_research_task = Task(
        description=dedent(f"""User Input: {user_prompt}
                    Conduct in-depth research to understand users’ needs, pain points, and behaviors. 
                    Use interviews, observations, and surveys to gather insights. Synthesize findings 
                    into user personas and journey maps."""),
        expected_output=dedent(f"""A detailed user research report including:
                                    - User personas.
                                    - Key pain points.
                                    - Journey maps highlighting challenges and opportunities."""),
        output_file='output/design_thinking/user_research_report.md',
        agent=agents[0]
    )
    problem_framing_task = Task(
        description=dedent(f"""User Input: {user_prompt}
                    Analyze the insights from the Empathize stage to articulate a clear and actionable 
                    problem statement. Ensure the statement captures the core challenge and inspires 
                    innovative solutions."""),
        expected_output=dedent(f"""A problem statement document that includes:
                    - A concise problem statement.
                    - Supporting evidence from research.
                    - Constraints and criteria for solutions."""),
        output_file="output/design_thinking/problem_framing_report.md",
        agent=agents[1]
    )
    idea_generation_task = Task(
        description=dedent(f"""User Input: {user_prompt}
                    Facilitate a brainstorming session to generate a wide array of potential solutions. 
                    Encourage out-of-the-box thinking and build on each other's ideas. Organize and 
                    prioritize solutions based on feasibility and impact."""),
        expected_output=dedent(f"""A list of at least 10 creative ideas, prioritized with a short justification for each."""),
        output_file="output/design_thinking/idea_generation_report.md",
        agent=agents[2]
    )
    solution_development_task = Task(
        description=dedent(f"""User Input: {user_prompt}
                    Create tangible prototypes for the top ideas from the Ideate stage. These could be 
                    sketches, mockups, or models depending on the nature of the problem. Ensure the 
                    prototypes are ready for user feedback."""),
        expected_output=dedent(f"""A minimum of two prototypes with:
                    - Visual or functional representation.
                    - Notes on how they address the problem statement."""),
        output_file="output/design_thinking/solution_development_report.md",
        agent=agents[3]
    )
    feedback_iteration_task = Task(
        description=dedent(f"""User Input: {user_prompt}
                    Present prototypes to users and stakeholders. Gather feedback through structured 
                    testing sessions. Identify strengths, weaknesses, and opportunities for improvement. 
                    Refine solutions based on feedback."""),
        expected_output=dedent(f"""A feedback report including:
                    - User feedback.
                    - Iteration recommendations.
                    - Next steps for the solution."""),
        output_file="output/design_thinking/feedback_iteration_report.md",
        agent=agents[4]
    )
    reflection_task = Task(
        description=dedent(f"""Reflect on the process as a team to document learnings, challenges, and successes. 
                    Identify what worked well and what could be improved for future projects."""),
        expected_output=dedent(f"""A retrospective document that includes:
                    - Key learnings.
                    - Successes and challenges.
                    - Suggestions for improvement."""),
        agent=agents[5]
    )
    design_thinking_tasks = [user_research_task, problem_framing_task, idea_generation_task, solution_development_task,
                             feedback_iteration_task, reflection_task]
    return design_thinking_tasks


#--------------------------------#
#         Research Crew          #
#--------------------------------#
def run_design_thinking(design_thinking_agents, design_thinking_tasks):
    crew = Crew(
        agents=design_thinking_agents,
        tasks=design_thinking_tasks,
        verbose=True,
        process=Process.sequential
    )
    return crew.kickoff()
