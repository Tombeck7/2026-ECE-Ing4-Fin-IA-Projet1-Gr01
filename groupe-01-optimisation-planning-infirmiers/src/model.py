from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from ortools.sat.python import cp_model


Shift = str  # "M", "A", "N"
PrefType = str  # "prefer", "avoid"
PreferenceKey = Tuple[int, int]  # (nurse, day)


@dataclass(frozen=True)
class RosteringConfig:
    shifts: Tuple[Shift, ...] = ("M", "A", "N")
    min_days_off: int = 1                 # min OFF per nurse over horizon
    max_consecutive_work_days: int = 5    # max consecutive working days
    max_nights_per_nurse: int = 3         # cap on nights per nurse
    rest_after_night: bool = True         # if True: N implies OFF next day

    # Objective weights (tune as needed)
    w_preference: int = 10
    w_balance: int = 3
    w_night_balance: int = 2


@dataclass
class SolveResult:
    feasible: bool
    schedule: Optional[List[List[str]]]  # [nurse][day] in {"M","A","N","OFF"}
    objective_value: Optional[float]
    stats: Dict[str, str]
    violations: List[str]


def solve_nurse_rostering(
    num_nurses: int,
    num_days: int,
    demand: List[Dict[Shift, int]],
    preferences: Optional[Dict[PreferenceKey, Dict]] = None,
    config: Optional[RosteringConfig] = None,
    time_limit_s: float = 10.0,
    log_search: bool = False,
) -> SolveResult:
    """
    demand: list of length num_days, each element is dict {"M":int,"A":int,"N":int}
    preferences: dict keyed by (nurse, day), value examples:
        {"type":"prefer", "shift":"M"}  -> penalty if not assigned M that day
        {"type":"prefer", "shift":"OFF"}-> penalty if works that day
        {"type":"avoid",  "shift":"N"}  -> penalty if assigned N that day
        {"type":"avoid",  "shift":"A"}  -> penalty if assigned A that day
    """
    if config is None:
        config = RosteringConfig()
    if preferences is None:
        preferences = {}

    shifts = list(config.shifts)

    # Basic input checks
    if len(demand) != num_days:
        raise ValueError("demand must have length num_days")
    for d in range(num_days):
        for s in shifts:
            if s not in demand[d]:
                raise ValueError(f"demand[{d}] missing shift {s}")

    model = cp_model.CpModel()

    # Decision vars: x[n,d,s] = 1 if nurse n works shift s on day d
    x: Dict[Tuple[int, int, Shift], cp_model.IntVar] = {}
    for n in range(num_nurses):
        for d in range(num_days):
            for s in shifts:
                x[(n, d, s)] = model.NewBoolVar(f"x_n{n}_d{d}_s{s}")

    # work[n,d] = 1 if works any shift (else OFF)
    work: Dict[Tuple[int, int], cp_model.IntVar] = {}
    for n in range(num_nurses):
        for d in range(num_days):
            work[(n, d)] = model.NewBoolVar(f"work_n{n}_d{d}")
            model.Add(work[(n, d)] == sum(x[(n, d, s)] for s in shifts))

    # ---- Hard constraints ----

    # 1) At most 1 shift per day per nurse
    for n in range(num_nurses):
        for d in range(num_days):
            model.Add(sum(x[(n, d, s)] for s in shifts) <= 1)

    # 2) Exact coverage of demand per day per shift
    for d in range(num_days):
        for s in shifts:
            model.Add(sum(x[(n, d, s)] for n in range(num_nurses)) == int(demand[d][s]))

    # 3) Min days off per nurse over horizon
    if config.min_days_off > 0:
        for n in range(num_nurses):
            model.Add(sum(work[(n, d)] for d in range(num_days)) <= num_days - config.min_days_off)

    # 4) Max consecutive working days (sliding window)
    L = config.max_consecutive_work_days
    if L is not None and L > 0 and num_days >= (L + 1):
        for n in range(num_nurses):
            for start in range(0, num_days - (L + 1) + 1):
                model.Add(sum(work[(n, d)] for d in range(start, start + L + 1)) <= L)

    # 5) Rest after night: if N on day d then OFF on day d+1
    if config.rest_after_night and num_days >= 2:
        for n in range(num_nurses):
            for d in range(num_days - 1):
                model.Add(x[(n, d, "N")] + work[(n, d + 1)] <= 1)

    # 6) Max nights per nurse
    for n in range(num_nurses):
        model.Add(sum(x[(n, d, "N")] for d in range(num_days)) <= config.max_nights_per_nurse)

    # ---- Soft constraints (preferences) ----
    preference_penalties: List[cp_model.IntVar] = []

    for (n, d), pref in preferences.items():
        if not (0 <= n < num_nurses and 0 <= d < num_days):
            continue

        ptype = pref.get("type")
        shift = pref.get("shift")

        # Normalize / guard
        if shift not in shifts and shift != "OFF":
            continue

        pen = model.NewIntVar(0, 1, f"pref_pen_n{n}_d{d}")

        if ptype == "prefer":
            if shift == "OFF":
                # penalty if works
                model.Add(pen == work[(n, d)])
            else:
                # penalty if not assigned preferred shift
                # pen = 1 - x[n,d,shift]
                model.Add(pen + x[(n, d, shift)] == 1)
        elif ptype == "avoid":
            if shift == "OFF":
                # avoid OFF means prefer working: penalty if OFF -> (1-work)
                model.Add(pen + work[(n, d)] == 1)
            else:
                # penalty if assigned that shift
                model.Add(pen == x[(n, d, shift)])
        else:
            continue

        preference_penalties.append(pen)

    # ---- Workload balance objective (max - min) ----
    total_work: List[cp_model.IntVar] = []
    total_nights: List[cp_model.IntVar] = []

    for n in range(num_nurses):
        tw = model.NewIntVar(0, num_days, f"total_work_n{n}")
        tn = model.NewIntVar(0, num_days, f"total_nights_n{n}")
        model.Add(tw == sum(work[(n, d)] for d in range(num_days)))
        model.Add(tn == sum(x[(n, d, "N")] for d in range(num_days)))
        total_work.append(tw)
        total_nights.append(tn)

    max_work = model.NewIntVar(0, num_days, "max_work")
    min_work = model.NewIntVar(0, num_days, "min_work")
    model.AddMaxEquality(max_work, total_work)
    model.AddMinEquality(min_work, total_work)
    work_spread = model.NewIntVar(0, num_days, "work_spread")
    model.Add(work_spread == max_work - min_work)

    # Balance nights too (optional but useful)
    max_n = model.NewIntVar(0, num_days, "max_nights")
    min_n = model.NewIntVar(0, num_days, "min_nights")
    model.AddMaxEquality(max_n, total_nights)
    model.AddMinEquality(min_n, total_nights)
    night_spread = model.NewIntVar(0, num_days, "night_spread")
    model.Add(night_spread == max_n - min_n)

    # ---- Objective ----
    obj_terms = []
    if preference_penalties:
        obj_terms.append(config.w_preference * sum(preference_penalties))
    obj_terms.append(config.w_balance * work_spread)
    obj_terms.append(config.w_night_balance * night_spread)

    model.Minimize(sum(obj_terms))

    # ---- Solve ----
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(time_limit_s)
    solver.parameters.log_search_progress = bool(log_search)
    solver.parameters.num_search_workers = 8

    status = solver.Solve(model)
    feasible = status in (cp_model.OPTIMAL, cp_model.FEASIBLE)

    schedule = None
    violations: List[str] = []

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

        violations = validate_schedule(
            schedule=schedule,
            demand=demand,
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
    )


def validate_schedule(
    schedule: List[List[str]],
    demand: List[Dict[Shift, int]],
    config: RosteringConfig,
) -> List[str]:
    """Returns list of violations. Empty list => OK."""
    shifts = list(config.shifts)
    num_nurses = len(schedule)
    num_days = len(schedule[0]) if num_nurses > 0 else 0

    viol: List[str] = []

    # 1) each nurse one assignment per day is ensured by representation, but check valid symbols
    allowed = set(shifts + ["OFF"])
    for n in range(num_nurses):
        for d in range(num_days):
            if schedule[n][d] not in allowed:
                viol.append(f"[SYMBOL] nurse {n} day {d}: invalid '{schedule[n][d]}'")

    # 2) coverage check
    for d in range(num_days):
        counts = {s: 0 for s in shifts}
        for n in range(num_nurses):
            if schedule[n][d] in shifts:
                counts[schedule[n][d]] += 1
        for s in shifts:
            if counts[s] != int(demand[d][s]):
                viol.append(f"[COVER] day {d} shift {s}: have {counts[s]} need {demand[d][s]}")

    # helper work
    def works(n: int, d: int) -> int:
        return 1 if schedule[n][d] != "OFF" else 0

    # 3) min days off
    if config.min_days_off > 0:
        for n in range(num_nurses):
            total_work = sum(works(n, d) for d in range(num_days))
            off = num_days - total_work
            if off < config.min_days_off:
                viol.append(f"[OFF] nurse {n}: off={off} < min_days_off={config.min_days_off}")

    # 4) max consecutive work days
    L = config.max_consecutive_work_days
    if L is not None and L > 0 and num_days >= (L + 1):
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

    # 5) rest after night
    if config.rest_after_night and num_days >= 2:
        for n in range(num_nurses):
            for d in range(num_days - 1):
                if schedule[n][d] == "N" and schedule[n][d + 1] != "OFF":
                    viol.append(f"[REST] nurse {n}: night day {d} but next day {d+1} is {schedule[n][d+1]}")

    # 6) max nights
    for n in range(num_nurses):
        nights = sum(1 for d in range(num_days) if schedule[n][d] == "N")
        if nights > config.max_nights_per_nurse:
            viol.append(f"[NIGHTS] nurse {n}: nights={nights} > max={config.max_nights_per_nurse}")

    return viol
