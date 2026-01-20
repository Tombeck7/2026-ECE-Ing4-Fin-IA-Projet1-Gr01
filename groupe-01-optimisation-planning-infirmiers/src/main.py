from model import solve_planning


def main():
    print("=== Nurse Rostering CSP ===")

    num_nurses = 6
    num_days = 7
    shifts = ["M", "A", "N"]  # Matin, Après-midi, Nuit

    # Demande minimale par jour et par shift
    demand = {
        0: {"M": 2, "A": 2, "N": 1},
        1: {"M": 2, "A": 2, "N": 1},
        2: {"M": 2, "A": 2, "N": 1},
        3: {"M": 2, "A": 2, "N": 1},
        4: {"M": 2, "A": 2, "N": 1},
        5: {"M": 2, "A": 2, "N": 1},
        6: {"M": 2, "A": 2, "N": 1},
    }

    planning = solve_planning(num_nurses, num_days, shifts, demand)

    if planning is None:
        print("❌ Aucun planning faisable trouvé")
        return

    print("✅ Planning trouvé :\n")
    for n, d, s in planning:
        print(f"Infirmier {n} → Jour {d} → Shift {s}")


if __name__ == "__main__":
    main()
