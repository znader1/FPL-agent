from crewai import Agent
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

# Existing: DataAgent, AnalystAgent, ExplainerAgent ...

"""NewsAgent = Agent(
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
"""
from crewai import Agent
from tools.news_tools import search_tool, scrape_tool
from tools import fpl_api

NewsAgent = Agent(
    role="FPL News & Injury Curator",
    goal="Gather reliable, **fresh** player news (injuries/returns/flags), plus pressers.",
    backstory="You keep it concise and source-based. You avoid rumor.",
    tools=[search_tool, scrape_tool],
    allow_delegation=False,
    verbose=True
)

ExpertsAgent = Agent(
    role="Experts Consensus Summarizer",
    goal="Summarize recurring recommendations from reputable FPL outlets.",
    backstory="You look for overlapping opinions and flag high-confidence picks.",
    tools=[search_tool, scrape_tool],
    allow_delegation=False,
    verbose=True
)

TeamAgent = Agent(
    role="My Team & Fixtures Analyst",
    goal="Inspect my current squad, fixtures, and obvious weak spots this GW.",
    backstory="You combine FPL API data with simple heuristics.",
    tools=[],
    allow_delegation=False,
    verbose=True
)

OpponentsAgent = Agent(
    role="Mini-League Opponents Scout",
    goal="Identify likely moves/captains of upcoming H2H opponents (or top rivals).",
    backstory="You use FPL API H2H endpoints and basic patterning.",
    tools=[],
    allow_delegation=False,
    verbose=True
)

StrategistAgent = Agent(
    role="Strategy Decider",
    goal="Choose between rolling, transfer(s), or chip with a clear starting XI.",
    backstory="You weigh expected points vs hit costs and chip equity.",
    tools=[],
    allow_delegation=False,
    verbose=True
)
