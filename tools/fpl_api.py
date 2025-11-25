import requests, pandas as pd

BOOTSTRAP = "https://fantasy.premierleague.com/api/bootstrap-static/"
FIXTURES  = "https://fantasy.premierleague.com/api/fixtures/"
ENTRY = "https://fantasy.premierleague.com/api/entry/{entry_id}/"
ENTRY_PICKS = "https://fantasy.premierleague.com/api/entry/{entry_id}/event/{event}/picks/"

def _get(url):
    r = requests.get(url, timeout=30); r.raise_for_status(); return r.json()

def get_bootstrap():
    return _get(BOOTSTRAP)

def get_fixtures():
    return pd.DataFrame(_get(FIXTURES))

def get_entry(entry_id: int):
    """Get general entry information."""
    return _get(ENTRY.format(entry_id=entry_id))

def get_entry_picks(entry_id: int, event: int):
    """Get picks for a specific gameweek."""
    return _get(ENTRY_PICKS.format(entry_id=entry_id, event=event))

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
            "id": p["id"],
             "transfers_in_event": p.get("transfers_in_event", 0),
             "total_points": p.get("total_points", 0),
             "points_per_game": p.get("points_per_game", 0),
             "event_points": p.get("event_points", 0),
        })
    return pd.DataFrame(rows)

def fixture_difficulty_df(horizon_gw=2):
    fx = get_fixtures()
    # Sum difficulty for next `horizon_gw` fixtures per team (simplistic)
    future = fx[fx["event"].notna()].copy()
    future = future.groupby(["team_h","event"]).agg({"team_h_difficulty":"mean"}).reset_index()
    return future

def build_team_df(entry_id: int, event: int = None):
    """
    Build a DataFrame of the user's FPL team for a given gameweek.
    If event is None, uses the current gameweek from entry data.
    """
    entry_data = get_entry(entry_id)
    if event is None:
        event = entry_data.get("current_event", 1)
    
    picks_data = get_entry_picks(entry_id, event)
    bootstrap = get_bootstrap()
    
    # Create mappings
    teams = {t["id"]: t["name"] for t in bootstrap["teams"]}
    players_dict = {p["id"]: p for p in bootstrap["elements"]}
    position_map = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}
    
    # Build team dataframe
    rows = []
    picks = picks_data.get("picks", [])
    
    for pick in picks:
        player_id = pick["element"]
        player_data = players_dict.get(player_id, {})
        position_code = player_data.get("element_type", 0)
        
        rows.append({
            "id": player_id,
            "player": player_data.get("web_name", "Unknown"),
            "full_name": f'{player_data.get("first_name", "")} {player_data.get("second_name", "")}'.strip(),
            "team": teams.get(player_data.get("team", 0), "Unknown"),
            "position": position_map.get(position_code, "UNK"),
            "now_cost": player_data.get("now_cost", 0) / 10.0,
            "form": float(player_data.get("form", "0") or 0),
            "ep_next": float(player_data.get("ep_next", "0") or 0),
            "total_points": player_data.get("total_points", 0),
            "status": player_data.get("status", "a"),
            "news": player_data.get("news") or "",
            "multiplier": pick.get("multiplier", 1),
            "is_captain": pick.get("is_captain", False),
            "is_vice_captain": pick.get("is_vice_captain", False),
            "position_in_squad": pick.get("position", 0),  # 1-15, starting XI first
            "points_per_game": player_data.get("points_per_game", 0),
            "event_points": player_data.get("event_points", 0),
            
        })
    
    df = pd.DataFrame(rows)
    # Sort by position in squad (starting XI first, then bench)
    df = df.sort_values("position_in_squad")
    return df, entry_data, picks_data
