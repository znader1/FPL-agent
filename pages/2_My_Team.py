# pages/2_My_Team.py
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from tools.fpl_api import build_team_df

load_dotenv()

st.set_page_config(page_title="My FPL Team", page_icon="👤", layout="wide")

st.title("👤 My FPL Team")

st.markdown(
    """
    View your Fantasy Premier League team for any gameweek.
    Enter your FPL entry ID to load your team.
    """
)

# Sidebar for entry ID and gameweek
st.sidebar.header("Team Settings")

entry_id = st.sidebar.number_input(
    "FPL Entry ID",
    min_value=1,
    value=st.session_state.get("entry_id", None) or 1,
    step=1,
    help="Your FPL entry ID can be found in your FPL team URL: fantasy.premierleague.com/entry/ENTRY_ID/event/..."
)

if entry_id:
    st.session_state["entry_id"] = entry_id

event = st.sidebar.number_input(
    "Gameweek",
    min_value=1,
    max_value=38,
    value=None,
    step=1,
    help="Leave empty to use current gameweek"
)

load_button = st.sidebar.button("🔍 Load Team")

# Main content
if load_button or (entry_id and "team_df" in st.session_state):
    try:
        with st.spinner("Loading your team..."):
            team_df, entry_data, picks_data = build_team_df(
                entry_id=int(entry_id),
                event=int(event) if event else None
            )
            st.session_state["team_df"] = team_df
            st.session_state["entry_data"] = entry_data
            st.session_state["picks_data"] = picks_data
            st.session_state["current_event"] = event or entry_data.get("current_event", 1)
    except Exception as e:
        st.error(f"Error loading team: {e}")
        st.info("Make sure your Entry ID is correct and the gameweek exists.")
        st.stop()

if "team_df" in st.session_state and not st.session_state["team_df"].empty:
    team_df = st.session_state["team_df"]
    entry_data = st.session_state["entry_data"]
    current_event = st.session_state.get("current_event", 1)
    
    # Display entry info
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Team Name", entry_data.get("name", "Unknown"))
    with col2:
        rank = entry_data.get('summary_overall_rank')
        rank_display = f"#{rank:,}" if rank else "N/A"
        st.metric("Overall Rank", rank_display)
    with col3:
        st.metric("Total Points", entry_data.get("summary_overall_points", 0))
    with col4:
        st.metric("Gameweek", current_event)
    
    st.divider()
    
    # Split into starting XI and bench
    starting_xi = team_df[team_df["position_in_squad"] <= 11].copy()
    bench = team_df[team_df["position_in_squad"] > 11].copy()
    
    # Display Starting XI
    st.subheader("⚽ Starting XI")
    
    # Group by position
    for pos in ["GK", "DEF", "MID", "FWD"]:
        pos_players = starting_xi[starting_xi["position"] == pos]
        if not pos_players.empty:
            st.markdown(f"**{pos}**")
            cols = st.columns(len(pos_players))
            for idx, (_, player) in enumerate(pos_players.iterrows()):
                with cols[idx]:
                    captain_badge = "👑" if player["is_captain"] else ("⭐" if player["is_vice_captain"] else "")
                    status_emoji = {
                        "a": "✅",
                        "d": "⚠️",
                        "i": "🏥",
                        "s": "🚫"
                    }.get(player["status"], "❓")
                    
                    st.markdown(
                        f"""
                        **{player['player']}** {captain_badge} {status_emoji}  
                        {player['team']} | {player['now_cost']:.1f}M  
                        Form: {player['form']:.1f} | xP: {player['ep_next']:.1f}
                        """
                    )
                    if player["news"]:
                        st.caption(f"⚠️ {player['news'][:50]}...")
    
    st.divider()
    
    # Display Bench
    st.subheader("🪑 Bench")
    if not bench.empty:
        bench_cols = st.columns(len(bench))
        for idx, (_, player) in enumerate(bench.iterrows()):
            with bench_cols[idx]:
                status_emoji = {
                    "a": "✅",
                    "d": "⚠️",
                    "i": "🏥",
                    "s": "🚫"
                }.get(player["status"], "❓")
                
                st.markdown(
                    f"""
                    **{player['player']}** {status_emoji}  
                    {player['team']} | {player['now_cost']:.1f}M  
                    Form: {player['form']:.1f}
                    """
                )
    else:
        st.write("No bench players")
    
    st.divider()
    
    # Detailed table view
    st.subheader("📊 Detailed View")
    
    # Add flags for issues
    display_df = team_df.copy()
    display_df["flags"] = display_df.apply(
        lambda row: "👑" if row["is_captain"] else ("⭐" if row["is_vice_captain"] else ""),
        axis=1
    )
    display_df["status_display"] = display_df["status"].map({
        "a": "Available",
        "d": "Doubtful",
        "i": "Injured",
        "s": "Suspended"
    })
    
    # Select columns to display
    cols_to_show = [
        "flags", "player", "team", "position", "now_cost",
        "form", "ep_next", "total_points", "status_display", "news"
    ]
    
    st.dataframe(
        display_df[cols_to_show].rename(columns={
            "flags": "",
            "status_display": "Status",
            "now_cost": "Price (M)",
            "ep_next": "xP Next",
            "total_points": "Total Pts"
        }),
        use_container_width=True,
        hide_index=True
    )
    
    # Team summary stats
    st.divider()
    st.subheader("📈 Team Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Value", f"£{team_df['now_cost'].sum():.1f}M")
    with col2:
        st.metric("Average Form", f"{team_df['form'].mean():.2f}")
    with col3:
        st.metric("Total xP Next", f"{team_df['ep_next'].sum():.1f}")
    with col4:
        injured_count = len(team_df[team_df["status"] != "a"])
        st.metric("Issues", injured_count, delta=None if injured_count == 0 else f"{injured_count} players")
    
    # Flag players with issues
    issues = team_df[(team_df["status"] != "a") | (team_df["news"].str.len() > 0)]
    if not issues.empty:
        st.warning("⚠️ Players with issues:")
        for _, player in issues.iterrows():
            st.write(f"- **{player['player']}** ({player['team']}): {player['status_display']} - {player['news'] or 'No news'}")

else:
    st.info("👆 Enter your FPL Entry ID in the sidebar and click 'Load Team' to view your squad.")
    st.markdown(
        """
        ### How to find your Entry ID:
        1. Go to your FPL team page on fantasy.premierleague.com
        2. Look at the URL - it will be something like: `fantasy.premierleague.com/entry/1234567/event/1`
        3. The number after `/entry/` is your Entry ID (e.g., 1234567)
        """
    )

