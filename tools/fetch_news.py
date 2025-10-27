import requests
import pandas as pd

BOOTSTRAP = "https://fantasy.premierleague.com/api/bootstrap-static/"
ELEMENT = "https://fantasy.premierleague.com/api/element-summary/{id}/"

def fetch_fpl_bootstrap():
    r = requests.get(BOOTSTRAP, timeout=30)
    r.raise_for_status()
    return r.json()

def latest_player_status_df():
    """Return DataFrame with player name, team, status, news, chance_of_playing_next_round, ep_next, form, now_cost."""
    j = fetch_fpl_bootstrap()
    teams = {t["id"]: t["name"] for t in j["teams"]}
    rows = []
    for p in j["elements"]:
        rows.append({
            "player": f'{p["web_name"]}',
            "full_name": f'{p["first_name"]} {p["second_name"]}',
            "team": teams.get(p["team"]),
            "status": p["status"],  # 'a' available, 'i' injured, 'd' doubt, 's' suspended, etc.
            "news": p.get("news") or "",
            "chance_next": p.get("chance_of_playing_next_round"),
            "form": p.get("form"),
            "ep_next": p.get("ep_next"),
            "now_cost": p.get("now_cost", 0)/10.0
        })
    df = pd.DataFrame(rows)
    return df

def annotate_with_status(preds_df):
    """Join predictions with latest status & flags by player short name match."""
    status_df = latest_player_status_df()
    # simple join on short web name; you can improve with fuzzy match if needed
    merged = preds_df.merge(status_df[["player","status","news","chance_next","form"]], on="player", how="left")
    return merged
