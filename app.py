# app.py
import streamlit as st
from dotenv import load_dotenv

from fpl_news_and_reco import get_news_summary, get_recommendations



load_dotenv()

st.set_page_config(page_title="FPL News & Recommender", page_icon="⚽")

st.title("⚽ FPL News & Recommender")

st.markdown(
    """
This app helps you reduce time on the FPL app by:
- Summarising important **news / injuries / flags** from official FPL data  
- Recommending **5 players** for a given position and price cap, based on a simple score  
"""
)

# --- Sidebar controls ---
st.sidebar.header("Parameters")

position = st.sidebar.selectbox(
    "Position",
    options=["GK", "DEF", "MID", "FWD"],
    index=2,  # default MID
)

max_price = st.sidebar.slider(
    "Max price per player (M)",
    min_value=4.0,
    max_value=13.0,
    value=9.0,
    step=0.5,
)

top_n = st.sidebar.slider(
    "Shortlist size (before LLM picks 5)",
    min_value=5,
    max_value=40,
    value=15,
    step=1,
)

run_button = st.sidebar.button("🚀 Run recommendations")

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
