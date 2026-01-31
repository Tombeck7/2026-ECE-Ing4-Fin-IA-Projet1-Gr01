from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from ortools.sat.python import cp_model

Shift = str  # "M", "A", "N"
PreferenceKey = Tuple[int, int]  # (nurse, day)


@dataclass(frozen=True)
class RosteringConfig:
    # Shifts
    shifts: Tuple[Shift, ...] = ("M", "A", "N")

    # Hard constraints
    min_days_off: int = 1                  # minimum OFF per nurse over horizon
    max_consecutive_work_days: int = 5     # maximum consecutive working days
    max_nights_per_nurse: int = 3          # cap number of nights per nurse
    rest_after_night: bool = True          # if True: N implies OFF next day

    # Objective weights (soft constraints)
    w_preference: int = 10                 # weight of preferences penalty
    w_balance_work: int = 3                # weight of work balance (max-min)
    w_balance_nights: int = 2              # weight of nights balance (max-min)


@dataclass
class SolveResult:
    feasible: bool
    schedule: Optional[List[List[str]]]    # [nurse][day] in {"M","A","N","OFF"}
    objective_value: Optional[float]
    stats: Dict[str, str]
    violations: List[str]
    metrics: Dict[str, float]


def solve_nurse_rostering(
    num_nurses: int,
    num_days: int,
    demand: List[Dict[Shift, int]],
    preferences: Optional[Dict[PreferenceKey, Dict]] = None,
    config: Optional[RosteringConfig] = None,
    time_limit_s: float = 10.0,
    log_search: bool = False,
    num_workers: int = 8,
) -> SolveResult:
    """
    demand: list length num_days; each element dict {"M":int,"A":int,"N":int}
    preferences: dict keyed by (nurse, day), example values:
        {"type":"prefer", "shift":"M"}     -> penalty if not assigned M that day
        {"type":"prefer", "shift":"OFF"}  -> penalty if works that day
        {"type":"avoid",  "shift":"N"}    -> penalty if assigned N that day
        {"type":"avoid",  "shift":"OFF"}  -> penalty if OFF (i.e. wants to work)
    """
    if config is None:
        config = RosteringConfig()
    if preferences is None:
        preferences = {}

    shifts = list(config.shifts)

    # ---- Input checks ----
    if len(demand) != num_days:
        raise ValueError("demand must have length == num_days")
    for d in range(num_days):
        for s in shifts:
            if s not in demand[d]:
                raise ValueError(f"demand[{d}] missing shift '{s}'")

    model = cp_model.CpModel()

    # Decision vars: x[n,d,s] ∈ {0,1}
    x: Dict[Tuple[int, int, Shift], cp_model.IntVar] = {}
    for n in range(num_nurses):
        for d in range(num_days):
            for s in shifts:
                x[(n, d, s)] = model.NewBoolVar(f"x_n{n}_d{d}_s{s}")

    # work[n,d] ∈ {0,1}: 1 if works any shift else OFF
    work: Dict[Tuple[int, int], cp_model.IntVar] = {}
    for n in range(num_nurses):
        for d in range(num_days):
            work[(n, d)] = model.NewBoolVar(f"work_n{n}_d{d}")
            model.Add(work[(n, d)] == sum(x[(n, d, s)] for s in shifts))

    # -----------------------
    # HARD CONSTRAINTS
    # -----------------------

    # (H1) At most 1 shift per day per nurse
    for n in range(num_nurses):
        for d in range(num_days):
            model.Add(sum(x[(n, d, s)] for s in shifts) <= 1)

    # (H2) Exact coverage of demand per day per shift
    for d in range(num_days):
        for s in shifts:
            model.Add(sum(x[(n, d, s)] for n in range(num_nurses)) == int(demand[d][s]))

    # (H3) Min OFF per nurse over horizon
    if config.min_days_off > 0:
        for n in range(num_nurses):
            model.Add(sum(work[(n, d)] for d in range(num_days)) <= num_days - config.min_days_off)

    # (H4) Max consecutive working days (sliding window)
    L = config.max_consecutive_work_days
    if L is not None and L > 0 and num_days >= (L + 1):
        for n in range(num_nurses):
            for start in range(0, num_days - (L + 1) + 1):
                model.Add(sum(work[(n, d)] for d in range(start, start + L + 1)) <= L)

    # (H5) Rest after night: if N on day d then OFF on day d+1
    if config.rest_after_night and "N" in shifts and num_days >= 2:
        for n in range(num_nurses):
            for d in range(num_days - 1):
                model.Add(x[(n, d, "N")] + work[(n, d + 1)] <= 1)

    # (H6) Max nights per nurse
    if "N" in shifts:
        for n in range(num_nurses):
            model.Add(sum(x[(n, d, "N")] for d in range(num_days)) <= config.max_nights_per_nurse)

    # -----------------------
    # SOFT CONSTRAINTS (Preferences)
    # -----------------------
    preference_penalties: List[cp_model.IntVar] = []

    for (n, d), pref in preferences.items():
        if not (0 <= n < num_nurses and 0 <= d < num_days):
            continue
        ptype = pref.get("type")
        shift = pref.get("shift")

        if shift not in shifts and shift != "OFF":
            continue

        pen = model.NewIntVar(0, 1, f"pref_pen_n{n}_d{d}")

        if ptype == "prefer":
            if shift == "OFF":
                # penalty if works
                model.Add(pen == work[(n, d)])
            else:
                # penalty if not assigned preferred shift
                model.Add(pen + x[(n, d, shift)] == 1)

        elif ptype == "avoid":
            if shift == "OFF":
                # avoid OFF => penalty if OFF -> (1 - work)
                model.Add(pen + work[(n, d)] == 1)
            else:
                # penalty if assigned that shift
                model.Add(pen == x[(n, d, shift)])
        else:
            continue

        preference_penalties.append(pen)

    # -----------------------
    # BALANCE OBJECTIVES
    # -----------------------
    total_work: List[cp_model.IntVar] = []
    total_nights: List[cp_model.IntVar] = []

    for n in range(num_nurses):
        tw = model.NewIntVar(0, num_days, f"total_work_n{n}")
        model.Add(tw == sum(work[(n, d)] for d in range(num_days)))
        total_work.append(tw)

        if "N" in shifts:
            tn = model.NewIntVar(0, num_days, f"total_nights_n{n}")
            model.Add(tn == sum(x[(n, d, "N")] for d in range(num_days)))
        else:
            tn = model.NewIntVar(0, 0, f"total_nights_n{n}")
        total_nights.append(tn)

    max_work = model.NewIntVar(0, num_days, "max_work")
    min_work = model.NewIntVar(0, num_days, "min_work")
    model.AddMaxEquality(max_work, total_work)
    model.AddMinEquality(min_work, total_work)
    work_spread = model.NewIntVar(0, num_days, "work_spread")
    model.Add(work_spread == max_work - min_work)

    max_n = model.NewIntVar(0, num_days, "max_nights")
    min_n = model.NewIntVar(0, num_days, "min_nights")
    model.AddMaxEquality(max_n, total_nights)
    model.AddMinEquality(min_n, total_nights)
    night_spread = model.NewIntVar(0, num_days, "night_spread")
    model.Add(night_spread == max_n - min_n)

    # -----------------------
    # Objective
    # -----------------------
    obj = []
    if preference_penalties:
        obj.append(config.w_preference * sum(preference_penalties))
    obj.append(config.w_balance_work * work_spread)
    obj.append(config.w_balance_nights * night_spread)
    model.Minimize(sum(obj))

    # -----------------------
    # Solve
    # -----------------------
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(time_limit_s)
    solver.parameters.log_search_progress = bool(log_search)
    solver.parameters.num_search_workers = int(num_workers)

    status = solver.Solve(model)
    feasible = status in (cp_model.OPTIMAL, cp_model.FEASIBLE)

    schedule: Optional[List[List[str]]] = None
    violations: List[str] = []
    metrics: Dict[str, float] = {}

    if feasible:
        schedule = [["OFF" for _ in range(num_days)] for _ in range(num_nurses)]
        for n in range(num_nurses):
            for d in range(num_days):
                assigned = "OFF"
                for s in shifts:
                    if solver.Value(x[(n, d, s)]) == 1:
                        assigned = s
                        break
                schedule[n][d] = assigned

        violations = validate_schedule(schedule, demand, config)

        metrics = compute_metrics(
            schedule=schedule,
            demand=demand,
            preferences=preferences,
            config=config,
        )

    stats = {
        "status": solver.StatusName(status),
        "objective": str(solver.ObjectiveValue()) if feasible else "NA",
        "wall_time_s": f"{solver.WallTime():.3f}",
        "branches": str(solver.NumBranches()),
        "conflicts": str(solver.NumConflicts()),
    }

    return SolveResult(
        feasible=feasible,
        schedule=schedule,
        objective_value=float(solver.ObjectiveValue()) if feasible else None,
        stats=stats,
        violations=violations,
        metrics=metrics,
    )


def validate_schedule(
    schedule: List[List[str]],
    demand: List[Dict[Shift, int]],
    config: RosteringConfig,
) -> List[str]:
    """Return violations. Empty => OK."""
    shifts = list(config.shifts)
    num_nurses = len(schedule)
    num_days = len(schedule[0]) if num_nurses else 0

    viol: List[str] = []
    allowed = set(shifts + ["OFF"])

    # Symbol check
    for n in range(num_nurses):
        for d in range(num_days):
            if schedule[n][d] not in allowed:
                viol.append(f"[SYMBOL] nurse {n} day {d}: invalid '{schedule[n][d]}'")

    # Coverage check
    for d in range(num_days):
        counts = {s: 0 for s in shifts}
        for n in range(num_nurses):
            if schedule[n][d] in shifts:
                counts[schedule[n][d]] += 1
        for s in shifts:
            if counts[s] != int(demand[d][s]):
                viol.append(f"[COVER] day {d} shift {s}: have {counts[s]} need {demand[d][s]}")

    def works(n: int, d: int) -> int:
        return 1 if schedule[n][d] != "OFF" else 0

    # Min OFF
    if config.min_days_off > 0:
        for n in range(num_nurses):
            off = sum(1 for d in range(num_days) if schedule[n][d] == "OFF")
            if off < config.min_days_off:
                viol.append(f"[OFF] nurse {n}: off={off} < min_days_off={config.min_days_off}")

    # Max consecutive work
    L = config.max_consecutive_work_days
    if L is not None and L > 0:
        for n in range(num_nurses):
            consec = 0
            for d in range(num_days):
                if works(n, d):
                    consec += 1
                    if consec > L:
                        viol.append(f"[CONSEC] nurse {n}: >{L} consecutive work days ending at day {d}")
                        break
                else:
                    consec = 0

    # Rest after night
    if config.rest_after_night and num_days >= 2:
        for n in range(num_nurses):
            for d in range(num_days - 1):
                if schedule[n][d] == "N" and schedule[n][d + 1] != "OFF":
                    viol.append(f"[REST] nurse {n}: night day {d} but next day is {schedule[n][d+1]}")

    # Max nights
    for n in range(num_nurses):
        nights = sum(1 for d in range(num_days) if schedule[n][d] == "N")
        if nights > config.max_nights_per_nurse:
            viol.append(f"[NIGHTS] nurse {n}: nights={nights} > max={config.max_nights_per_nurse}")

    return viol


def compute_metrics(
    schedule: List[List[str]],
    demand: List[Dict[Shift, int]],
    preferences: Dict[PreferenceKey, Dict],
    config: RosteringConfig,
) -> Dict[str, float]:
    """Compute useful metrics for comparisons."""
    shifts = list(config.shifts)
    num_nurses = len(schedule)
    num_days = len(schedule[0]) if num_nurses else 0

    # Work counts
    work_counts = []
    night_counts = []
    for n in range(num_nurses):
        work_counts.append(sum(1 for d in range(num_days) if schedule[n][d] != "OFF"))
        night_counts.append(sum(1 for d in range(num_days) if schedule[n][d] == "N"))

    work_spread = float(max(work_counts) - min(work_counts)) if work_counts else 0.0
    night_spread = float(max(night_counts) - min(night_counts)) if night_counts else 0.0

    # Preference satisfaction
    pref_total = 0
    pref_viol = 0
    for (n, d), pref in preferences.items():
        if not (0 <= n < num_nurses and 0 <= d < num_days):
            continue
        ptype = pref.get("type")
        sh = pref.get("shift")
        if sh not in shifts and sh != "OFF":
            continue

        pref_total += 1
        assigned = schedule[n][d]
        works = assigned != "OFF"

        violated = False
        if ptype == "prefer":
            if sh == "OFF":
                violated = works
            else:
                violated = (assigned != sh)
        elif ptype == "avoid":
            if sh == "OFF":
                violated = (not works)
            else:
                violated = (assigned == sh)

        if violated:
            pref_viol += 1

    pref_satisfaction = 0.0 if pref_total == 0 else float(1.0 - pref_viol / pref_total)

    return {
        "work_spread": work_spread,
        "night_spread": night_spread,
        "avg_work": float(sum(work_counts) / num_nurses) if num_nurses else 0.0,
        "pref_total": float(pref_total),
        "pref_viol": float(pref_viol),
        "pref_satisfaction": pref_satisfaction,
    }
