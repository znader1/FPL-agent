from crewai import Task
from tools.news_tools import news_seed_urls

def task_news(event: int):
    return Task(
        description=(
            f"Scan the latest **this week** news for GW{event}. "
            "Focus on injuries, returns, suspensions, and minutes risk. "
            f"Start with these URLs: {news_seed_urls()} "
            "Also perform a web search like: 'FPL GW{event} injuries press conference'. "
            "Output: bullet list: Player — status — source link(s). Keep to ~15 bullets max."
        ),
        expected_output="A compact bullets list with player status and source links."
    )

def task_experts(event: int):
    return Task(
        description=(
            f"Aggregate experts' picks and captaincy for GW{event}. "
            "Search/scrape multiple outlets, then produce a **consensus table** with "
            "Top 8 players and typical captain choices. Include brief rationale + links."
        ),
        expected_output="Consensus table + 3-5 sentence summary, with links."
    )

def task_team(event: int, entry_id: int):
    return Task(
        description=(
            f"Using the provided helper (outside the LLM) we will fetch picks for entry {entry_id} "
            f"and GW{event}. You will receive a JSON blob with current XI/bench/value/ITB/FT if available. "
            "Analyse fixture difficulty, weak spots (injury/rotation risk), and bench order."
        ),
        expected_output="Bullets: strengths, weaknesses, risky spots, cheap fixes."
    )

def task_opponents(event: int, h2h_league_id: int):
    return Task(
        description=(
            f"Using helper outputs, examine H2H {h2h_league_id} for GW{event}. "
            "Identify likely captains and EO threats among my upcoming opponent(s) "
            "based on their squad core and recent behavior."
        ),
        expected_output="Table: Opponent, Likely Captain, Notable Transfers, EO threats."
    )

def task_strategy(event: int, hit_cost: int = 4):
    return Task(
        description=(
            "Combine news, experts, my team analysis, and opponents intel. "
            "Propose: (A) Roll, (B) 1FT, (C) 2FT, (D) Hit, (E) Chip. "
            f"Estimate expected points gain vs {hit_cost}-point hit where relevant. "
            "Return a final recommendation: transfers (in/out), captain/vice, starting XI, bench order, and chip if any."
        ),
        expected_output="One clear plan with justification and a short risk note."
    )
