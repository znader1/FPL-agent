import requests, pandas as pd

BOOTSTRAP = "https://fantasy.premierleague.com/api/bootstrap-static/"
FIXTURES  = "https://fantasy.premierleague.com/api/fixtures/"

def _get(url):
    r = requests.get(url, timeout=30); r.raise_for_status(); return r.json()

def get_bootstrap():
    return _get(BOOTSTRAP)

def get_fixtures():
    return pd.DataFrame(_get(FIXTURES))

def players_df():
    j = get_bootstrap()
    team_map = {t["id"]: t["name"] for t in j["teams"]}
    rows = []
    for p in j["elements"]:
        rows.append({
            "player": p["web_name"],
            "full_name": f'{p["first_name"]} {p["second_name"]}',
            "team": team_map.get(p["team"]),
            "pos_code": p["element_type"],  # 1 GK, 2 DEF, 3 MID, 4 FWD
            "position": {1:"GK",2:"DEF",3:"MID",4:"FWD"}[p["element_type"]],
            "now_cost": p.get("now_cost",0)/10.0,
            "form": float(p.get("form", "0") or 0),
            "ep_next": float(p.get("ep_next", "0") or 0),  # FPL expected points next GW
            "status": p["status"],     # 'a'=available, 'd'=doubt, 'i'=injured, 's'=suspended
            "news": p.get("news") or "",
            "chance_next": p.get("chance_of_playing_next_round"),
            "id": p["id"]
        })
    return pd.DataFrame(rows)

def fixture_difficulty_df(horizon_gw=2):
    fx = get_fixtures()
    # Sum difficulty for next `horizon_gw` fixtures per team (simplistic)
    future = fx[fx["event"].notna()].copy()
    future = future.groupby(["team_h","event"]).agg({"team_h_difficulty":"mean"}).reset_index()
    return future
