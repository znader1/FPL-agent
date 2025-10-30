import os, streamlit as st
from crew import build_crew

st.title("FPL Agent (CrewAI)")
position = st.selectbox("Position", ["GK","DEF","MID","FWD"], index=2)
gw = st.number_input("Gameweek", min_value=1, max_value=60, value=int(os.getenv("DEFAULT_GW", 12)))
budget = st.number_input("Budget (M)", min_value=4.0, max_value=30.0, value=float(os.getenv("DEFAULT_BUDGET", 15.5)))
top_n = st.slider("Candidates to consider", 3, 15, 8)

if st.button("Recommend"):
    res = build_crew(position, gw, budget, top_n).kickoff()
    st.write(res)
