# app.py
import streamlit as st
from dotenv import load_dotenv

from fpl_news_and_reco import get_news_summary, get_recommendations
from tools.fpl_api import build_team_df

load_dotenv()

st.set_page_config(
    page_title="FPL News & Recommender",
    page_icon="⚽",
    layout="wide"
)

st.title("⚽ FPL News & Recommender")

# Create tabs
tab1, tab2 = st.tabs(["📰 News & Recommendations", "👤 My Team"])

# ========== TAB 1: News & Recommendations ==========
with tab1:
    st.markdown(
        """
        This app helps you reduce time on the FPL app by:
        - Summarising important **news / injuries / flags** from official FPL data  
        - Recommending **5 players** for a given position and price cap, based on a simple score  
        """
    )

    # --- Sidebar controls ---
    with st.sidebar.expander("📊 Recommendation Parameters", expanded=True):
        position = st.selectbox(
            "Position",
            options=["GK", "DEF", "MID", "FWD"],
            index=2,  # default MID
        )
        
        max_price = st.slider(
            "Max price per player (M)",
            min_value=4.0,
            max_value=13.0,
            value=9.0,
            step=0.5,
        )
        
        top_n = st.slider(
            "Shortlist size (before LLM picks 5)",
            min_value=5,
            max_value=40,
            value=15,
            step=1,
        )
        
        run_button = st.button("🚀 Run recommendations")
    
    # --- Main content ---
    # Load news summary (cached) - this only runs once per session/data update
    @st.cache_data(ttl=3600)  # Cache for 1 hour
    def load_cached_news():
        """Load and cache news summary."""
        return get_news_summary()
    
    # Display news summary (cached)
    st.subheader("📰 News / Injuries")
    try:
        with st.spinner("Loading news summary (this is cached)..."):
            news_summary = load_cached_news()
        st.markdown(news_summary)
    except Exception as e:
        st.error(f"Error loading news: {e}")
        news_summary = None
    
    # Run recommendations when button is clicked
    if run_button:
        st.info(f"Running recommendations for {position} up to {max_price}M…")
    
        with st.spinner("Fetching FPL data and generating recommendations..."):
            try:
                result = get_recommendations(
                    position=position,
                    max_price=max_price,
                    top_n=top_n,
                )
            except Exception as e:
                st.error(f"Error while running recommendations: {e}")
            else:
                st.success("Done! See below 👇")
    
                st.subheader("🎯 Recommended players")
                st.markdown(result["reco_summary"])
    
                st.subheader("📊 Shortlist used by the recommender")
                if result["shortlist_df"].empty:
                    st.write("No candidates found for these parameters.")
                else:
                    st.dataframe(result["shortlist_df"])
    else:
        st.caption("Configure your parameters in the sidebar, then click **🚀 Run recommendations**.")

# ========== TAB 2: My Team ==========
with tab2:
    st.markdown(
        """
        View your Fantasy Premier League team for any gameweek.
        Enter your FPL entry ID to load your team.
        """
    )
    
    # Sidebar for entry ID and gameweek
    with st.sidebar.expander("👤 Team Settings", expanded=True):
        entry_id = st.number_input(
            "FPL Entry ID",
            min_value=1,
            value=st.session_state.get("entry_id", None) or 1,
            step=1,
            help="Your FPL entry ID can be found in your FPL team URL: fantasy.premierleague.com/entry/ENTRY_ID/event/...",
            key="team_entry_id"
        )
        
        if entry_id:
            st.session_state["entry_id"] = entry_id
        
        event = st.number_input(
            "Gameweek",
            min_value=1,
            max_value=38,
            value=None,
            step=1,
            help="Leave empty to use current gameweek",
            key="team_event"
        )
        
        load_button = st.button("🔍 Load Team", key="load_team_btn")
    
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
            "form", "ep_next", "total_points", "status_display", "news","points_per_game", "event_points"
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
                st.write(f"- **{player['player']}** ({player['team']}): {player['status']} - {player['news'] or 'No news'}")
    
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
