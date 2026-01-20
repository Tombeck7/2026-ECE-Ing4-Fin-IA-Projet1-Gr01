from ortools.sat.python import cp_model


def solve_planning(num_nurses, num_days, shifts, demand):
    model = cp_model.CpModel()

    # =============================
    # PARAMÈTRES RH
    # =============================
    max_working_days = num_days - 1  # au moins 1 jour OFF

    # =============================
    # VARIABLES
    # =============================
    x = {}
    for n in range(num_nurses):
        for d in range(num_days):
            for s in shifts:
                x[(n, d, s)] = model.NewBoolVar(f"x_{n}_{d}_{s}")

    # =============================
    # CONTRAINTES
    # =============================

    # 1️⃣ Un seul shift par jour
    for n in range(num_nurses):
        for d in range(num_days):
            model.Add(sum(x[(n, d, s)] for s in shifts) <= 1)

    # 2️⃣ Couverture des besoins
    for d in range(num_days):
        for s in shifts:
            model.Add(sum(x[(n, d, s)] for n in range(num_nurses)) == demand[s])

    # 3️⃣ Repos : pas Nuit → Matin
    for n in range(num_nurses):
        for d in range(num_days - 1):
            model.Add(x[(n, d, "N")] + x[(n, d + 1, "M")] <= 1)

    # 4️⃣ Au moins 1 jour OFF
    for n in range(num_nurses):
        model.Add(
            sum(x[(n, d, s)] for d in range(num_days) for s in shifts)
            <= max_working_days
        )

    # =============================
    # OBJECTIF : ÉQUILIBRER LA CHARGE
    # =============================

    # Charge de chaque infirmier
    workload = {}
    for n in range(num_nurses):
        workload[n] = model.NewIntVar(0, num_days, f"workload_{n}")
        model.Add(
            workload[n]
            == sum(x[(n, d, s)] for d in range(num_days) for s in shifts)
        )

    # Charge maximale
    max_load = model.NewIntVar(0, num_days, "max_load")
    model.AddMaxEquality(max_load, [workload[n] for n in range(num_nurses)])

    # 🎯 Objectif : minimiser la charge maximale
    model.Minimize(max_load)

    # =============================
    # RÉSOLUTION
    # =============================
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10
    status = solver.Solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None

    # =============================
    # EXTRACTION DU PLANNING
    # =============================
    schedule = []
    for n in range(num_nurses):
        for d in range(num_days):
            for s in shifts:
                if solver.Value(x[(n, d, s)]) == 1:
                    schedule.append((n, d, s))

    return schedule
