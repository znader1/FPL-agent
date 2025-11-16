# tasks.py
from crewai import Task
from tools.news_tools import news_seed_urls

def task_news(event: int):
    return Task(
        description=(
            f"Scan latest this week for GW{event}. Focus injuries/returns/suspensions."
            f" Start with: {news_seed_urls()} and also search 'FPL GW{event} injuries press conference'."
            " Output: up to 15 bullets: Player — status — source link(s)."
        ),
        expected_output="Bulleted list with links."
    )

def task_experts(event: int):
    return Task(
        description=(
            f"Aggregate experts' picks and captaincy for GW{event}. "
            "Scrape multiple outlets, then output a consensus table "
            "(Top 8 names + short rationale + links) and a 3–5 sentence summary."
        ),
        expected_output="Consensus table + short summary with links."
    )

def task_team(event: int, entry_id: int):
    return Task(
        description=(
            f"You are given my FPL JSON for GW{event}.\n"
            "- BOOTSTRAP: {{context.bootstrap}}\n"
            "- ENTRY: {{context.entry}}\n"
            "- PICKS: {{context.picks}}\n\n"
            "Reconstruct XI/bench (names/positions/teams); flag injury/rotation risks; "
            "identify weak spots vs upcoming fixtures; propose bench order and 1–2 cheap fixes."
        ),
        expected_output="Bullets: strengths, weaknesses, risky spots, bench order, 1–2 transfer ideas."
    )

def task_opponents(event: int, h2h_league_id: int):
    return Task(
        description=(
            f"Use:\n- BOOTSTRAP: {{context.bootstrap}}\n- H2H_MATCHES: {{context.h2h_matches}}\n"
            f"Find my GW{event} opponent(s). Return a compact table: Opponent, Likely Captain, EO threats, Notable Transfers (guess)."
        ),
        expected_output="Table as described."
    )

def task_strategy(event: int, hit_cost: int = 4):
    return Task(
        description=(
            "Combine outputs: NEWS + EXPERTS + TEAM + OPPONENTS along with:\n"
            "- TEAM JSON: {{context.picks}}\n- BOOTSTRAP: {{context.bootstrap}}\n"
            "Choose Roll / 1FT / 2FT / Hit / Chip. Estimate expected gain vs hit cost. "
            "Output: transfers (in/out), captain/vice, starting XI, bench order, chip (if any), and a short risk note."
        ),
        expected_output="One clear plan + rationale + risk note."
    )
