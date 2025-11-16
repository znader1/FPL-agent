# week1_news_reco.py

import argparse
import os

from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

from tools.fpl_api import players_df

load_dotenv()

# --- LLM ---
llm = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    temperature=0.2,
)

# --- Data helpers ---

def build_news_lines(df, max_players: int = 25) -> str:
    """
    Build a text list of players with issues (injured, doubtful, suspended, flagged).
    """
    issues = df[
        (df["status"] != "a") | (df["news"].str.len() > 0)
    ].copy()

    # Put worst statuses first, then higher form
    status_priority = {"i": 0, "s": 1, "d": 2, "a": 3}
    issues["status_rank"] = issues["status"].map(status_priority).fillna(4)
    issues = issues.sort_values(["status_rank", "form"], ascending=[True, False])
    issues = issues.head(max_players)

    lines = []
    for _, r in issues.iterrows():
        lines.append(
            f"{r['player']} ({r['team']}, {r['position']}) "
            f"- status={r['status']} - form={r['form']} - news={r['news']}"
        )
    if not lines:
        return "No major injury/flag issues found."
    return "\n".join(lines)


def build_reco_table(
    df,
    position: str = "MID",
    max_price: float = 9.0,
    max_players: int = 15,
) -> str:
    """
    Simple recommender input: shortlist of candidates based on:
    - position
    - price cap
    - form, ep_next, and transfers_in_event
    """
    sub = df[(df["position"] == position) & (df["now_cost"] <= max_price)].copy()

    if sub.empty:
        return f"No players found for {position} under {max_price}M."

    # Normalise transfers a bit so huge numbers don't dominate
    sub["transfers_in_event"] = sub["transfers_in_event"].fillna(0).astype(float)
    sub["score"] = (
        2.0 * sub["form"]            # recent form (FPL's form is roughly last 4 GWs) :contentReference[oaicite:1]{index=1}
        + 1.0 * sub["ep_next"]       # FPL's own expected points next GW
        + 0.0001 * sub["transfers_in_event"]  # bandwagon/bias towards popular picks
    )

    sub = sub.sort_values("score", ascending=False).head(max_players)

    # Keep a compact table
    cols = ["player", "team", "position", "now_cost", "form", "ep_next",
            "total_points", "transfers_in_event", "score"]
    return sub[cols].to_string(index=False, float_format=lambda x: f"{x:.2f}")


# --- Agents ---

NewsAgent = Agent(
    role="FPL News & Injury Summarizer",
    goal=(
        "Highlight the most important injury/flag news and availability risks "
        "for FPL managers."
    ),
    backstory=(
        "You look at FPL's official player status and news field and summarise "
        "who is injured, doubtful, or suspended, focusing on relevant FPL assets."
    ),
    llm=llm,
    allow_delegation=False,
    verbose=True,
)

RecoAgent = Agent(
    role="Simple FPL Recommender",
    goal=(
        "From a shortlist of players and their basic stats (form, ep_next, transfers in), "
        "pick the best options for this week."
    ),
    backstory=(
        "You help an FPL manager choose players based on form, expected points next GW, "
        "and how popular they are (transfers in this gameweek)."
    ),
    llm=llm,
    allow_delegation=False,
    verbose=True,
)


def build_crew(position: str, max_price: float, top_n: int):
    df = players_df()

    news_text = build_news_lines(df, max_players=25)
    reco_text = build_reco_table(df, position=position, max_price=max_price, max_players=top_n)

    news_task = Task(
        description=(
            "You are given a list of FPL players with their status and short news "
            "(directly from the official game).\n\n"
            "List:\n"
            f"{news_text}\n\n"
            "Summarise the key availability news in ~8–12 bullet points. Focus on:\n"
            "- Big-name attackers and defenders with issues\n"
            "- New injuries or returns from injury\n"
            "- Suspensions and major doubts\n"
            "Group bullets by team if possible."
        ),
        expected_output="8–12 bullets highlighting the most important FPL-relevant news.",
        agent=NewsAgent,
    )

    reco_task = Task(
        description=(
            "You are given a shortlist of FPL players in a single position, "
            "with price, form, expected points next GW, total points, and "
            "transfers in this gameweek.\n\n"
            "Table:\n"
            f"{reco_text}\n\n"
            "From this table:\n"
            f"- Recommend 5 players for position {position}\n"
            f"- Assume max price per player is {max_price}M\n"
            "- Strongly prefer higher form and ep_next, but you can give some weight "
            "to players with many transfers_in_event (they might be popular bandwagons).\n\n"
            "Output:\n"
            "- A ranked list 1–5 with player name, team, price\n"
            "- 1–2 sentences per player explaining why\n"
            "- A final 2–3 sentence summary of the overall strategy (safe vs punty picks)."
        ),
        expected_output="Ranked list of 5 recommended players with explanations.",
        agent=RecoAgent,
    )

    crew = Crew(
        agents=[NewsAgent, RecoAgent],
        tasks=[news_task, reco_task],
        process=Process.sequential,
        verbose=True,
    )

    return crew


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--position", type=str, default="MID",
                        help="GK, DEF, MID, FWD")
    parser.add_argument("--max-price", type=float, default=9.0,
                        help="Maximum price (in millions) per player.")
    parser.add_argument("--top-n", type=int, default=12,
                        help="How many candidates to show the LLM before picking 5.")
    args = parser.parse_args()

    crew = build_crew(
        position=args.position,
        max_price=args.max_price,
        top_n=args.top_n,
    )
    result = crew.kickoff()
    print("\n================ FINAL OUTPUT ================\n")
    print(result)


if __name__ == "__main__":
    main()
