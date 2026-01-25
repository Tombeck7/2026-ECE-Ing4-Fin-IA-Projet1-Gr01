from model import solve_planning
import csv


def display_planning_table(planning, num_nurses, num_days):
    """
    Affiche le planning sous forme de tableau lisible
    """
    table = [["Jour \\ Infirmier"] + [f"I{n}" for n in range(num_nurses)]]

    for d in range(num_days):
        row = [f"Jour {d}"]
        for n in range(num_nurses):
            shift = "-"
            for (n2, d2, s) in planning:
                if n2 == n and d2 == d:
                    shift = s
            row.append(shift)
        table.append(row)

    for row in table:
        print(" | ".join(row))


def export_planning_csv(planning, num_nurses, num_days, filename="planning.csv"):
    """
    Exporte le planning en CSV
    """
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Jour"] + [f"Infirmier {n}" for n in range(num_nurses)])

        for d in range(num_days):
            row = [f"Jour {d}"]
            for n in range(num_nurses):
                shift = ""
                for (n2, d2, s) in planning:
                    if n2 == n and d2 == d:
                        shift = s
                row.append(shift)
            writer.writerow(row)


def main():
    print("=== Nurse Rostering CSP ===")

    num_nurses = 6
    num_days = 7
    shifts = ["M", "A", "N"]

    demand = {
        d: {"M": 2, "A": 2, "N": 1}
        for d in range(num_days)
    }

    planning = solve_planning(num_nurses, num_days, shifts, demand)

    if planning is None:
        print("❌ Aucun planning faisable trouvé")
        return

    print("\n✅ Planning trouvé (liste brute) :\n")
    for n, d, s in planning:
        print(f"Infirmier {n} → Jour {d} → Shift {s}")

    print("\n📊 Planning sous forme de tableau :\n")
    display_planning_table(planning, num_nurses, num_days)

    export_planning_csv(planning, num_nurses, num_days)
    print("\n📁 Planning exporté dans planning.csv")


if __name__ == "__main__":
    main()
