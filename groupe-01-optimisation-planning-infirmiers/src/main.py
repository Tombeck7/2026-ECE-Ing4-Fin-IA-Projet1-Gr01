from model import solve_planning

def main():
    print("=== Nurse Rostering CSP ===")

    # paramètres simples (MVP)
    num_nurses = 5
    num_days = 7
    shifts = ["M", "A", "N"]

    demand = {
        "M": 2,
        "A": 2,
        "N": 1
    }

    schedule = solve_planning(num_nurses, num_days, shifts, demand)

    if schedule is None:
        print("❌ Aucun planning faisable trouvé")
    else:
        print("✅ Planning trouvé :\n")
        for (n, d, s) in schedule:
            print(f"Infirmier {n} → Jour {d} → Shift {s}")

if __name__ == "__main__":
    main()
