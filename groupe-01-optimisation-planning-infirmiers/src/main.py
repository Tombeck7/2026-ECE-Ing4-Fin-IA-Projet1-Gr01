from model import solve_planning


def main():
    print("=== Nurse Rostering CSP ===")

    # -----------------------------
    # Paramètres du problème
    # -----------------------------
    num_nurses = 6
    num_days = 7
    shifts = ["M", "A", "N"]  # Matin, Après-midi, Nuit

    # Besoins par jour
    demand = {
        "M": 2,
        "A": 2,
        "N": 1
    }

    # -----------------------------
    # Résolution
    # -----------------------------
    schedule = solve_planning(
        num_nurses=num_nurses,
        num_days=num_days,
        shifts=shifts,
        demand=demand
    )

    # -----------------------------
    # Affichage
    # -----------------------------
    if schedule is None:
        print("❌ Aucun planning faisable trouvé")
        return

    print("✅ Planning trouvé :\n")
    for nurse, day, shift in schedule:
        print(f"Infirmier {nurse} → Jour {day} → Shift {shift}")


if __name__ == "__main__":
    main()
