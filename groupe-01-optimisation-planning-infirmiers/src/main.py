from model import solve_planning, SolveConfig
import matplotlib.pyplot as plt
import numpy as np


def build_preferences(num_nurses: int, num_days: int):
    """
    Exemple réaliste :
    - infirmier 0 et 1 n'aiment pas les nuits (pénalité)
    - infirmier 2 préfère matin (bonus)
    - infirmier 3 préfère après-midi (bonus)
    - infirmier 4 évite le lundi (jour 0) (pénalité sur tous shifts)
    """
    prefs = {}

    # Pénaliser toutes les nuits pour certains infirmiers
    for d in range(num_days):
        prefs[(0, d, "N")] = 4
        prefs[(1, d, "N")] = 3

    # Bonus si assigné sur shift préféré
    for d in range(num_days):
        prefs[(2, d, "M")] = -1
        prefs[(3, d, "A")] = -1

    # Éviter jour 0 pour infirmier 4
    for s in ["M", "A", "N"]:
        prefs[(4, 0, s)] = 2

    return prefs


def plot_planning_table(planning, num_nurses, num_days):
    # Table texte
    table = [["" for _ in range(num_days)] for _ in range(num_nurses)]
    for n, d, s in planning:
        table[n][d] = s

    # Couleurs lisibles
    color_map = {
        "M": "#A7C7E7",  # bleu clair
        "A": "#B4E7B0",  # vert clair
        "N": "#F4B6B6",  # rouge clair
        "": "#F0F0F0",   # repos/off
    }

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.axis("off")

    for i in range(num_nurses):
        for j in range(num_days):
            shift = table[i][j]
            ax.add_patch(
                plt.Rectangle(
                    (j, num_nurses - i - 1),
                    1, 1,
                    color=color_map[shift],
                    ec="black",
                    linewidth=1.2
                )
            )
            ax.text(
                j + 0.5,
                num_nurses - i - 0.5,
                shift if shift else "OFF",
                ha="center",
                va="center",
                fontsize=12,
                fontweight="bold"
            )

    ax.set_xlim(0, num_days)
    ax.set_ylim(0, num_nurses)
    ax.set_xticks(np.arange(num_days) + 0.5)
    ax.set_yticks(np.arange(num_nurses) + 0.5)
    ax.set_xticklabels([f"Jour {d}" for d in range(num_days)], fontsize=11)
    ax.set_yticklabels([f"Infirmier {i}" for i in reversed(range(num_nurses))], fontsize=11)

    ax.set_title("Planning infirmiers (tableau lisible)", fontsize=14, fontweight="bold")

    legend = [
        plt.Rectangle((0, 0), 1, 1, color=color_map["M"], label="Matin"),
        plt.Rectangle((0, 0), 1, 1, color=color_map["A"], label="Après-midi"),
        plt.Rectangle((0, 0), 1, 1, color=color_map["N"], label="Nuit"),
        plt.Rectangle((0, 0), 1, 1, color=color_map[""], label="Repos"),
    ]
    ax.legend(handles=legend, loc="upper right")
    plt.tight_layout()
    plt.show()


def main():
    num_nurses = 6
    num_days = 7
    shifts = ["M", "A", "N"]

    # Demande: 2 matin, 2 aprem, 1 nuit par jour
    demand = {}
    for d in range(num_days):
        demand[(d, "M")] = 2
        demand[(d, "A")] = 2
        demand[(d, "N")] = 1

    preferences = build_preferences(num_nurses, num_days)

    config = SolveConfig(max_time_seconds=10.0, balance_weight=10)

    planning = solve_planning(
        num_nurses=num_nurses,
        num_days=num_days,
        shifts=shifts,
        demand=demand,
        preferences=preferences,
        config=config
    )

    if planning is None:
        print("❌ Aucun planning faisable trouvé")
        return

    print("✅ Planning trouvé :\n")
    for n, d, s in sorted(planning, key=lambda t: (t[0], t[1])):
        print(f"Infirmier {n} → Jour {d} → Shift {s}")

    plot_planning_table(planning, num_nurses, num_days)


if __name__ == "__main__":
    main()
