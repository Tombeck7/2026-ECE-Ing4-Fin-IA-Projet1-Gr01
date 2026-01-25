from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from ortools.sat.python import cp_model

Shift = str  # "M", "A", "N"
Assignment = Tuple[int, int, Shift]  # (nurse, day, shift)
PrefMap = Dict[Tuple[int, int, Shift], int]  # penalty (+) or bonus (-)


@dataclass
class SolveConfig:
    max_time_seconds: float = 10.0
    balance_weight: int = 10  # weight on workload imbalance vs preferences


def solve_planning(
    num_nurses: int,
    num_days: int,
    shifts: List[Shift],
    demand: Dict[Tuple[int, Shift], int],
    preferences: Optional[PrefMap] = None,
    config: SolveConfig = SolveConfig(),
) -> Optional[List[Assignment]]:
    """
    Solve nurse rostering with:
    - Hard constraints: at most one shift/day, demand coverage, rest after night (N -> no M next day)
    - Soft constraints: preferences via penalties/bonuses in objective
    - Objective: minimize workload imbalance + preference penalties
    """

    model = cp_model.CpModel()

    # x[n, d, s] = 1 if nurse n works shift s on day d
    x: Dict[Tuple[int, int, Shift], cp_model.IntVar] = {}
    for n in range(num_nurses):
        for d in range(num_days):
            for s in shifts:
                x[(n, d, s)] = model.NewBoolVar(f"x_{n}_{d}_{s}")

    # 1) At most one shift per day per nurse
    for n in range(num_nurses):
        for d in range(num_days):
            model.Add(sum(x[(n, d, s)] for s in shifts) <= 1)

    # 2) Demand coverage
    for d in range(num_days):
        for s in shifts:
            required = demand.get((d, s), 0)
            model.Add(sum(x[(n, d, s)] for n in range(num_nurses)) >= required)

    # 3) Rest after night: if N on day d then no M on day d+1
    if "N" in shifts and "M" in shifts:
        for n in range(num_nurses):
            for d in range(num_days - 1):
                model.Add(x[(n, d, "N")] + x[(n, d + 1, "M")] <= 1)

    # ---- Workload variables
    workloads: List[cp_model.IntVar] = []
    for n in range(num_nurses):
        w = model.NewIntVar(0, num_days, f"workload_{n}")
        model.Add(w == sum(x[(n, d, s)] for d in range(num_days) for s in shifts))
        workloads.append(w)

    max_w = model.NewIntVar(0, num_days, "max_workload")
    min_w = model.NewIntVar(0, num_days, "min_workload")
    model.AddMaxEquality(max_w, workloads)
    model.AddMinEquality(min_w, workloads)

    # ---- Preferences (soft constraints)
    # Convention:
    #  - penalty > 0 : "I don't want this assignment" (adds cost if assigned)
    #  - penalty < 0 : "I like this assignment" (reduces objective if assigned)
    pref_cost_terms = []
    if preferences:
        for (n, d, s), penalty in preferences.items():
            if (n, d, s) in x:
                pref_cost_terms.append(penalty * x[(n, d, s)])

    # Objective: workload imbalance weighted + preference costs
    model.Minimize(config.balance_weight * (max_w - min_w) + sum(pref_cost_terms))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = config.max_time_seconds

    status = solver.Solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None

    planning: List[Assignment] = []
    for n in range(num_nurses):
        for d in range(num_days):
            for s in shifts:
                if solver.Value(x[(n, d, s)]) == 1:
                    planning.append((n, d, s))

    return planning
