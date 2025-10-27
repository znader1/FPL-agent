from crewai import Agent
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

# Existing: DataAgent, AnalystAgent, ExplainerAgent ...

NewsAgent = Agent(
    role="FPL News & Status Analyst",
    goal="Combine FPL status flags and short news items to highlight availability risks and late-breaking info.",
    backstory=(
        "You read availability status, doubts, and form. You warn about injury risks and suspensions."
    ),
    allow_delegation=False,
    verbose=True,
    llm=llm,
)

OpponentAgent = Agent(
    role="Opponent Analyst",
    goal="Compare my squad vs an opponent, identify differentials and captaincy risks, recommend moves to maximize edge.",
    backstory=(
        "You understand head-to-head risk management. You surface high-impact differentials."
    ),
    allow_delegation=False,
    verbose=True,
    llm=llm,
)
