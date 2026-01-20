from ortools.sat.python import cp_model


def solve_planning(num_nurses, num_days, shifts, demand):
    model = cp_model.CpModel()

    # Variables x[n, d, s] ∈ {0,1}
    x = {}
    for n in range(num_nurses):
        for d in range(num_days):
            for s in shifts:
                x[(n, d, s)] = model.NewBoolVar(f"x_{n}_{d}_{s}")

    # 1️⃣ Un infirmier max par jour
    for n in range(num_nurses):
        for d in range(num_days):
            model.Add(sum(x[(n, d, s)] for s in shifts) <= 1)

    # 2️⃣ Couverture des besoins
    for d in range(num_days):
        for s in shifts:
            model.Add(sum(x[(n, d, s)] for n in range(num_nurses)) == demand[s])

    # 3️⃣ Repos simple : pas Nuit → Matin
    for n in range(num_nurses):
        for d in range(num_days - 1):
            model.Add(x[(n, d, "N")] + x[(n, d + 1, "M")] <= 1)

    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None

    schedule = []
    for n in range(num_nurses):
        for d in range(num_days):
            for s in shifts:
                if solver.Value(x[(n, d, s)]) == 1:
                    schedule.append((n, d, s))

    return schedule
