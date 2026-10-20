"""CrewAI starter: a four-agent crew (researcher -> writer -> fact checker -> editor).

Change for the assignment: added a Fact Checker agent and task between the
writer and the editor, so specific claims are audited before final editing.

Run:  uv run python main.py "your topic here"

CrewAI's big idea: you describe a TEAM of role-playing agents and the TASKS they
own. CrewAI handles passing each task's output to the next agent.
"""
import os
import sys
from pathlib import Path

from crewai import LLM, Agent, Crew, Process, Task
from dotenv import load_dotenv

load_dotenv()

# --- 1. The model --------------------------------------------------------
# CrewAI has no built-in Groq provider, but Groq speaks the OpenAI API, so we
# point CrewAI's OpenAI client at Groq's endpoint. Change GROQ_MODEL in .env
# to swap models without touching this file.
MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
llm = LLM(
    model=f"openai/{MODEL}",  # the leading "openai/" only selects the client
    base_url=os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
    api_key=os.environ["GROQ_API_KEY"],
    temperature=0.3,
)

# --- 2. The agents: WHO is on the team -----------------------------------
researcher = Agent(
    role="Research Analyst",
    goal="Collect the key facts and tensions about {topic}",
    backstory="You are a careful analyst who separates evidence from hype and "
    "says plainly when you are unsure.",
    llm=llm,
    allow_delegation=False,
)
writer = Agent(
    role="Technical Writer",
    goal="Explain {topic} to a smart reader outside the field",
    backstory="You turn dense technical material into clear, jargon-free prose.",
    llm=llm,
    allow_delegation=False,
)
fact_checker = Agent(
    role="Fact Checker",
    goal="Audit every specific claim in the draft explainer on {topic} before it is edited",
    backstory="You are a skeptical legal-research librarian. You know that this "
    "team has no web access, so every named law, case, study, statistic and date "
    "came from model memory. You never invent a citation, and you would rather "
    "delete a claim than let a doubtful one through.",
    llm=llm,
    allow_delegation=False,
)
editor = Agent(
    role="Editor",
    goal="Tighten the draft and flag any claim that needs a source",
    backstory="You cut filler, fix unclear sentences, and never let an "
    "unsupported claim through unmarked.",
    llm=llm,
    allow_delegation=False,
)

# --- 3. The tasks: WHAT each person owns ---------------------------------
research_task = Task(
    description="Research {topic}. List 5 key facts and 2 open questions.",
    expected_output="A bulleted research brief: 5 facts, 2 open questions.",
    agent=researcher,
)
writing_task = Task(
    description="Using the research brief, write a 250-word explainer on {topic}.",
    expected_output="A 250-word explainer in plain language.",
    agent=writer,
)
fact_check_task = Task(
    description="Fact-check the draft explainer on {topic}. List every specific "
    "claim (named laws, court cases, studies, reports, statistics, dates). Label "
    "each one VERIFIED-LIKELY, UNCERTAIN, or LIKELY-WRONG, with a one-line reason. "
    "Then rewrite the draft so that LIKELY-WRONG claims are removed or corrected "
    "and UNCERTAIN claims are hedged. Do not add any new citations.",
    expected_output="1) A claim-by-claim fact-check table with labels and reasons. "
    "2) A corrected draft explainer of about 250 words.",
    agent=fact_checker,
)
editing_task = Task(
    description="Edit the fact-checked explainer. Tighten it, keep the fact "
    "checker's corrections, and mark any remaining claim needing a source. "
    "End with a short 'Fact-check notes' list of the claims that were removed "
    "or hedged.",
    expected_output="The final edited explainer, with [source needed] flags, "
    "followed by a short 'Fact-check notes' list.",
    agent=editor,
)

# --- 4. The crew: HOW they work together ---------------------------------
crew = Crew(
    agents=[researcher, writer, fact_checker, editor],
    tasks=[research_task, writing_task, fact_check_task, editing_task],
    process=Process.sequential,  # each task sees the previous task's output
    verbose=True,  # print each agent's work as it happens
)

if __name__ == "__main__":
    topic = " ".join(sys.argv[1:]) or "how small teams can use AI agents in data science"
    result = crew.kickoff(inputs={"topic": topic})

    out = Path("output")
    out.mkdir(exist_ok=True)
    (out / "explainer.md").write_text(result.raw, encoding="utf-8")
    print("\n=== FINAL OUTPUT (also saved to output/explainer.md) ===\n")
    print(result.raw)
