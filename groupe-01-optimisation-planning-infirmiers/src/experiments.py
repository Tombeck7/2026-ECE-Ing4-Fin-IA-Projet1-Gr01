from __future__ import annotations

from copy import deepcopy
from typing import Dict, List

from model import RosteringConfig, solve_nurse_rostering


def demand_constant(num_days: int) -> List[Dict[str, int]]:
    return [{"M": 2, "A": 2, "N": 1} for _ in range(num_days)]


def prefs_demo() -> Dict:
    return {
        (0, 0): {"type": "prefer", "shift": "OFF"},
        (1, 1): {"type": "avoid", "shift": "N"},
        (2, 3): {"type": "prefer", "shift": "M"},
        (4, 6): {"type": "prefer", "shift": "OFF"},
    }


def run_case(name: str, num_nurses: int, num_days: int, demand, prefs, cfg: RosteringConfig):
    res = solve_nurse_rostering(
        num_nurses=num_nurses,
        num_days=num_days,
        demand=demand,
        preferences=prefs,
        config=cfg,
        time_limit_s=10.0,
        log_search=False,
    )
    if not res.feasible or res.schedule is None or res.violations:
        return {
            "case": name,
            "status": "INFEASIBLE",
            "objective": None,
            "work_spread": None,
            "night_spread": None,
            "pref_sat": None,
        }
    return {
        "case": name,
        "status": "OK",
        "objective": res.objective_value,
        "work_spread": res.metrics.get("work_spread"),
        "night_spread": res.metrics.get("night_spread"),
        "pref_sat": res.metrics.get("pref_satisfaction"),
    }


def main():
    num_nurses = 6
    num_days = 7
    demand = demand_constant(num_days)
    prefs = prefs_demo()

    base_cfg = RosteringConfig()

    cases = []

    # Case 1: no preferences
    cases.append(run_case("no_prefs", num_nurses, num_days, demand, {}, base_cfg))

    # Case 2: with preferences
    cases.append(run_case("with_prefs", num_nurses, num_days, demand, prefs, base_cfg))

    # Case 3: stronger balance, weaker prefs
    cfg3 = deepcopy(base_cfg)
    cfg3 = RosteringConfig(
        min_days_off=base_cfg.min_days_off,
        max_consecutive_work_days=base_cfg.max_consecutive_work_days,
        max_nights_per_nurse=base_cfg.max_nights_per_nurse,
        rest_after_night=base_cfg.rest_after_night,
        w_preference=5,
        w_balance_work=10,
        w_balance_nights=5,
    )
    cases.append(run_case("balance_strong", num_nurses, num_days, demand, prefs, cfg3))

    print("\n=== EXPERIMENTS RESULTS ===")
    for c in cases:
        print(c)


if __name__ == "__main__":
    main()
