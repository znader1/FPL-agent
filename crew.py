# crew.py
from crewai import Crew, Process
from agents import NewsAgent, ExpertsAgent, TeamAgent, OpponentsAgent, StrategistAgent
from tasks import task_news, task_experts, task_team, task_opponents, task_strategy

def make_crew(event: int, entry_id: int, h2h_league_id: int):
    return Crew(
        agents=[NewsAgent, ExpertsAgent, TeamAgent, OpponentsAgent, StrategistAgent],
        tasks=[
            task_news(event).as_agent(NewsAgent),
            task_experts(event).as_agent(ExpertsAgent),
            task_team(event, entry_id).as_agent(TeamAgent),
            task_opponents(event, h2h_league_id).as_agent(OpponentsAgent),
            task_strategy(event).as_agent(StrategistAgent),
        ],
        process=Process.sequential,
        verbose=True
    )
