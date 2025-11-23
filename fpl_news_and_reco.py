# fpl_news_and_reco.py

import os
import requests
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


# ---------- FPL API + Data preparation ----------

def get_bootstrap():
    r = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/", timeout=30)
    r.raise_for_status()
    return r.json()


def build_players_df() -> pd.DataFrame:
    data = get_bootstrap()
    teams = {t["id"]: t["name"] for t in data["teams"]}

    rows = []
    for p in data["elements"]:
        rows.append({
            "id": p["id"],
            "player": p["web_name"],
            "full_name": f'{p["first_name"]} {p["second_name"]}',
            "team": teams.get(p["team"]),
            "pos_code": p["element_type"],
            "position": {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}[p["element_type"]],
            "now_cost": p.get("now_cost", 0) / 10.0,
            "form": float(p.get("form", "0") or 0.0),
            "ep_next": float(p.get("ep_next", "0") or 0.0),
            "status": p.get("status", ""),
            "news": p.get("news") or "",
            "total_points": p.get("total_points", 0),
            "transfers_in_event": p.get("transfers_in_event", 0),
        })
    return pd.DataFrame(rows)


# ---------- Helper builders ----------

def build_news_text(df: pd.DataFrame, max_players: int = 25) -> str:
    """List players with issues (injury/doubt/suspension/news)."""
    status_priority = {"i": 0, "s": 1, "d": 2, "a": 3}  # injured, suspended, doubtful, available

    issues = df[(df["status"] != "a") | (df["news"].str.len() > 0)].copy()
    if issues.empty:
        return "No major issues found."

    issues["status_rank"] = issues["status"].map(status_priority).fillna(4)
    issues = issues.sort_values(["status_rank", "form"], ascending=[True, False]).head(max_players)

    lines = []
    for _, r in issues.iterrows():
        lines.append(
            f"{r['player']} ({r['team']}, {r['position']}) "
            f"- status={r['status']} - form={r['form']:.2f} - news={r['news']}"
        )
    return "\n".join(lines)


def build_reco_df(
    df: pd.DataFrame,
    position: str = "MID",
    max_price: float = 9.0,
    top_n: int = 15,
) -> pd.DataFrame:
    """
    Filter and score candidates for the recommender.
    score = 0.6 * ep_next + 0.3 * form + 0.0001 * transfers_in_event
    """
    sub = df[(df["position"] == position) & (df["now_cost"] <= max_price)].copy()
    if sub.empty:
        return sub  # empty df

    sub["transfers_in_event"] = sub["transfers_in_event"].fillna(0).astype(float)
    sub["score"] = (
        0.6 * sub["ep_next"] +
        0.3 * sub["form"] +
        0.0001 * sub["transfers_in_event"]
    )
    sub = sub.sort_values("score", ascending=False).head(top_n)
    return sub


def df_to_table_text(df: pd.DataFrame) -> str:
    if df.empty:
        return "No candidates found for these filters."
    cols = [
        "player", "team", "position", "now_cost",
        "form", "ep_next", "total_points", "transfers_in_event", "score"
    ]
    return df[cols].to_string(index=False, float_format=lambda x: f"{x:.2f}")


# ---------- "Agents" (LLM calls) ----------

def summarise_news(news_text: str) -> str:
    """News agent: summarise FPL issues into bullets."""
    prompt = f"""
You are an assistant for Fantasy Premier League managers.

Here is a list of players, their teams, status and short news (from the official game):

{news_text}

Summarise this in 8–12 bullet points, focusing only on FPL-relevant news:
- big attackers/defenders with injuries or doubts
- suspensions
- returns from injury

Group bullets by team if possible. Be concise.
"""
    completion = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You summarise FPL player news for fantasy managers."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    return completion.choices[0].message.content


def recommend_from_table(position: str, max_price: float, table_text: str) -> str:
    """Recommender agent: pick best players from the score table."""
    prompt = f"""
You are an FPL recommendation assistant.

You are given a shortlist of FPL players in position {position}, with a maximum price cap of {max_price}M. Each player has:
- price (now_cost, in millions)
- form
- expected points next gameweek (ep_next)
- total_points
- transfers_in_event
- a pre-computed score

The shortlist table is:

{table_text}

Task:
- Recommend 5 players for this gameweek.
- Return a ranked list 1–5: player, team, price.
- For each player, add 1–2 sentences explaining why they are a good pick
  (mention form, ep_next, and optionally popularity or value).
- Finish with a 2–3 sentence summary of the overall strategy
  (e.g. safe template vs punty picks, balance of floors vs ceilings).

Be concrete and avoid generic fluff.
"""
    completion = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You recommend FPL players given stats and a shortlist."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )
    return completion.choices[0].message.content


# ---------- Orchestrator for Streamlit ----------

def get_news_summary():
    """
    Cached function to get news summary.
    This only depends on FPL data, not on position/price parameters.
    """
    df = build_players_df()
    news_text = build_news_text(df)
    news_summary = summarise_news(news_text)
    return news_summary


def get_recommendations(
    position: str = "MID",
    max_price: float = 9.0,
    top_n: int = 15,
):
    """
    Get recommendations for a given position and price cap.
    This can be run multiple times with different parameters without recomputing news.
    """
    df = build_players_df()
    reco_df = build_reco_df(df, position=position, max_price=max_price, top_n=top_n)
    reco_table_text = df_to_table_text(reco_df)
    reco_summary = recommend_from_table(position, max_price, reco_table_text)
    
    return {
        "reco_summary": reco_summary,
        "shortlist_df": reco_df,
    }


def run_news_and_reco(
    position: str = "MID",
    max_price: float = 9.0,
    top_n: int = 15,
):
    """
    Full pipeline for one click:
    - load FPL data
    - build news list (cached)
    - build shortlist with scores
    - call LLM for news summary (cached)
    - call LLM for recommendations
    - return everything for UI
    
    Note: This function is kept for backward compatibility.
    For better performance, use get_news_summary() and get_recommendations() separately.
    """
    news_summary = get_news_summary()
    reco_result = get_recommendations(position=position, max_price=max_price, top_n=top_n)
    
    return {
        "news_summary": news_summary,
        "reco_summary": reco_result["reco_summary"],
        "shortlist_df": reco_result["shortlist_df"],
    }


if __name__ == "__main__":
    # quick CLI test
    out = run_news_and_reco(position="MID", max_price=9.0, top_n=15)
    print("=== NEWS ===")
    print(out["news_summary"])
    print("\n=== RECO ===")
    print(out["reco_summary"])
