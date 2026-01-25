from __future__ import annotations

from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from model import RosteringConfig, solve_nurse_rostering


def build_demo_instance() -> Tuple[int, int, List[Dict[str, int]], Dict[Tuple[int, int], Dict]]:
    """
    Demo instance: 6 nurses, 7 days, demand per day (M/A/N).
    You can replace this by loading from CSV later.
    """
    num_nurses = 6
    num_days = 7

    # Demand per day
    # Example: every day need 2 morning, 2 afternoon, 1 night (total 5 nurses working/day)
    demand = []
    for d in range(num_days):
        demand.append({"M": 2, "A": 2, "N": 1})

    # Preferences (soft constraints)
    # Example format:
    # (nurse, day): {"type": "prefer"/"avoid", "shift":"M"/"A"/"N"/"OFF"}
    preferences: Dict[Tuple[int, int], Dict] = {
        (0, 0): {"type": "prefer", "shift": "M"},
        (0, 1): {"type": "avoid", "shift": "N"},
        (1, 2): {"type": "prefer", "shift": "OFF"},
        (2, 4): {"type": "prefer", "shift": "A"},
        (3, 5): {"type": "avoid", "shift": "M"},
        (4, 6): {"type": "prefer", "shift": "OFF"},
    }

    return num_nurses, num_days, demand, preferences


def print_schedule(schedule: List[List[str]], nurse_names: List[str]) -> None:
    num_nurses = len(schedule)
    num_days = len(schedule[0]) if num_nurses else 0

    header = " " * 14 + " ".join([f"J{d:02d}" for d in range(num_days)])
    print(header)
    print("-" * len(header))

    for n in range(num_nurses):
        row = " ".join([f"{schedule[n][d]:>3}" for d in range(num_days)])
        print(f"{nurse_names[n]:<14}{row}")


def plot_schedule(schedule: List[List[str]], nurse_names: List[str]) -> None:
    """
    Readable table: nurses x days with text labels and clear colors.
    """
    num_nurses = len(schedule)
    num_days = len(schedule[0]) if num_nurses else 0

    # Map to colors (use strong, readable palette)
    color_map = {
        "M": "#8ecae6",   # blue
        "A": "#b7e4c7",   # green
        "N": "#ffadad",   # red/pink
        "OFF": "#f1f1f1", # light gray
    }

    fig_w = max(10, num_days * 1.2)
    fig_h = max(5, num_nurses * 0.8)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))

    # Draw grid cells
    for n in range(num_nurses):
        for d in range(num_days):
            val = schedule[n][d]
            ax.add_patch(
                plt.Rectangle(
                    (d, n), 1, 1,
                    facecolor=color_map.get(val, "#ffffff"),
                    edgecolor="black",
                    linewidth=1.2
                )
            )
            ax.text(
                d + 0.5, n + 0.5, val,
                ha="center", va="center",
                fontsize=14, fontweight="bold"
            )

    # Axis limits and ticks
    ax.set_xlim(0, num_days)
    ax.set_ylim(0, num_nurses)
    ax.invert_yaxis()

    ax.set_xticks([d + 0.5 for d in range(num_days)])
    ax.set_xticklabels([f"Jour {d}" for d in range(num_days)], fontsize=11)

    ax.set_yticks([n + 0.5 for n in range(num_nurses)])
    ax.set_yticklabels(nurse_names, fontsize=11)

    ax.set_title("Planning infirmiers (lisible)", fontsize=16, fontweight="bold", pad=12)

    # Legend
    legend_items = [
        Patch(facecolor=color_map["M"], edgecolor="black", label="Matin (M)"),
        Patch(facecolor=color_map["A"], edgecolor="black", label="Après-midi (A)"),
        Patch(facecolor=color_map["N"], edgecolor="black", label="Nuit (N)"),
        Patch(facecolor=color_map["OFF"], edgecolor="black", label="Repos (OFF)"),
    ]
    ax.legend(handles=legend_items, loc="upper right")

    # Remove spines (grid is enough)
    for spine in ax.spines.values():
        spine.set_visible(False)

    plt.tight_layout()
    plt.show()


def main() -> None:
    print("=== Nurse Rostering (CSP / OR-Tools CP-SAT) ===")

    num_nurses, num_days, demand, preferences = build_demo_instance()
    nurse_names = [f"Infirmier {i}" for i in range(num_nurses)]

    config = RosteringConfig(
        shifts=("M", "A", "N"),
        min_days_off=1,
        max_consecutive_work_days=5,
        max_nights_per_nurse=3,
        rest_after_night=True,
        w_preference=10,
        w_balance=3,
        w_night_balance=2,
    )

    result = solve_nurse_rostering(
        num_nurses=num_nurses,
        num_days=num_days,
        demand=demand,
        preferences=preferences,
        config=config,
        time_limit_s=10.0,
        log_search=False,
    )

    print("\n--- Solver stats ---")
    for k, v in result.stats.items():
        print(f"{k}: {v}")

    if not result.feasible or result.schedule is None:
        print("\n❌ Aucun planning faisable trouvé (avec ces contraintes).")
        return

    # Verify constraints
    if result.violations:
        print("\n⚠️ VIOLATIONS détectées (donc le modèle n’est pas OK) :")
        for v in result.violations:
            print(" -", v)
        print("\n=> Stop. Il faut corriger le modèle avant de présenter.")
        return

    print("\n✅ Planning trouvé (contraintes OK) :\n")
    print_schedule(result.schedule, nurse_names)

    # Visual readable planning
    plot_schedule(result.schedule, nurse_names)


if __name__ == "__main__":
    main()
