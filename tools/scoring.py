# tools/scoring.py
def simple_expected_points(last4_pts: float, fdr: float, is_home: bool) -> float:
    home_bonus = 0.5 if is_home else 0.0
    return (last4_pts / max(1.0, fdr)) + home_bonus

def transfer_value(expected_gain: float, hit_cost: int) -> float:
    return expected_gain - hit_cost
