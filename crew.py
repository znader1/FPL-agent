import os
from dotenv import load_dotenv
from crewai import Crew, Process
from agents import DataAgent, AnalystAgent, ExplainerAgent
from tasks import data_task, analyst_task, explainer_task

def build_crew(position="MID", gw=12, budget=15.5, top_n=8):
    load_dotenv()
    t1 = data_task(position, gw, budget, top_n)
    t2 = analyst_task()
    t3 = explainer_task()
    return Crew(
        agents=[DataAgent, AnalystAgent, ExplainerAgent],
        tasks=[t1, t2, t3],
        process=Process.sequential,
        verbose=True,
    )

if __name__ == "__main__":
    crew = build_crew(
        position="MID",
        gw=int(os.getenv("DEFAULT_GW", 12)),
        budget=float(os.getenv("DEFAULT_BUDGET", 15.5)),
        top_n=8
    )
    print(crew.kickoff())
