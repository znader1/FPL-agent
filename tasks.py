from crewai import Task
from tools.load_predictions import top_players

def data_task(position, gw, budget, top_n=8):
    # We precompute data and pass it via context; the agent formats/summarizes.
    candidates = top_players(position, gw, budget, top_n).to_dict(orient="records")
    t = Task(
        description=(f"Here are candidate players for {position=}, {gw=}, budget<={budget}. "
                     f"Summarize in a concise JSON list: player, team, position, price, exp_points."),
        expected_output="A concise JSON list of candidates.",
    )
    t.context = {"candidates": candidates}
    return t

def analyst_task():
    return Task(
        description=("Given the candidates list, pick the best subset under budget "
                     "maximizing exp_points. Return JSON {selected:[...], total_price:float, reasoning:str}."),
        expected_output="JSON with selected players, total price, reasoning.",
    )

def explainer_task():
    return Task(
        description=("Write a 4–6 sentence explanation referencing exp_points and price. "
                     "Add one trade-off to consider."),
        expected_output="Short readable paragraph.",
    )
