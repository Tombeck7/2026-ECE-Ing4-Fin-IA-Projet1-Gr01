from ortools.sat.python import cp_model


def solve_planning(num_nurses, num_days, shifts, demand):
    """
    Résout le problème de planning infirmier via CP-SAT (CSP).
    """

    model = cp_model.CpModel()

    # Variables x[n][d][s] = 1 si infirmier n travaille le jour d sur le shift s
    x = {}
    for n in range(num_nurses):
        for d in range(num_days):
            for s in shifts:
                x[(n, d, s)] = model.NewBoolVar(f"x_{n}_{d}_{s}")

    # 1️⃣ Contrainte : au plus 1 shift par jour et par infirmier
    for n in range(num_nurses):
        for d in range(num_days):
            model.Add(
                sum(x[(n, d, s)] for s in shifts) <= 1
            )

    # 2️⃣ Contrainte : couverture de la demande
    for d in range(num_days):
        for s in shifts:
            model.Add(
                sum(x[(n, d, s)] for n in range(num_nurses)) >= demand[d][s]
            )

    # 3️⃣ Contrainte : repos après une nuit
    for n in range(num_nurses):
        for d in range(num_days - 1):
            model.Add(
                x[(n, d, "N")] + x[(n, d + 1, "M")] <= 1
            )

    # 4️⃣ Contrainte : maximum de nuits par infirmier
    MAX_NIGHTS = 3
    for n in range(num_nurses):
        model.Add(
            sum(x[(n, d, "N")] for d in range(num_days)) <= MAX_NIGHTS
        )

    # 5️⃣ Équilibrage de la charge de travail
    workload = []
    for n in range(num_nurses):
        w = model.NewIntVar(0, num_days, f"workload_{n}")
        model.Add(
            w == sum(x[(n, d, s)] for d in range(num_days) for s in shifts)
        )
        workload.append(w)

    max_workload = model.NewIntVar(0, num_days, "max_workload")
    min_workload = model.NewIntVar(0, num_days, "min_workload")
    model.AddMaxEquality(max_workload, workload)
    model.AddMinEquality(min_workload, workload)

    # 🎯 Fonction objectif : équilibrer la charge
    model.Minimize(max_workload - min_workload)

    # Résolution
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10
    status = solver.Solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None

    # Extraction du planning
    schedule = []
    for n in range(num_nurses):
        for d in range(num_days):
            for s in shifts:
                if solver.Value(x[(n, d, s)]) == 1:
                    schedule.append((n, d, s))

    return schedule
