from __future__ import annotations

import os
from typing import Dict, List

from model import RosteringConfig, solve_nurse_rostering
from viz import plot_schedule


# =========================================================
# ✅ ICI TU CHANGES TOUT CE QUE TU VEUX
# =========================================================

def build_demand(num_days: int) -> List[Dict[str, int]]:
    """
    DEMANDE par jour.
    Exemple constant: M=2, A=2, N=1 chaque jour.
    Tu peux faire varier par jour si tu veux.
    """
    return [{"M": 2, "A": 2, "N": 1} for _ in range(num_days)]


def build_preferences() -> Dict:
    """
    PREFERENCES infirmiers (soft constraints).
    Clé = (nurse, day)
    Valeur = {"type": "prefer"/"avoid", "shift":"M"/"A"/"N"/"OFF"}

    Exemples:
    - infirmier 0 veut OFF le jour 0
    - infirmier 1 évite N le jour 1
    - infirmier 2 préfère M le jour 3
    """
    prefs = {
        (0, 0): {"type": "prefer", "shift": "OFF"},
        (1, 1): {"type": "avoid", "shift": "N"},
        (2, 3): {"type": "prefer", "shift": "M"},
        (3, 4): {"type": "avoid", "shift": "N"},
        (4, 6): {"type": "prefer", "shift": "OFF"},
    }
    return prefs


def build_config() -> RosteringConfig:
    """
    CONTRAINTES / pondérations.
    C'est ici que tu modifies:
    - min_days_off
    - max_consecutive_work_days
    - max_nights_per_nurse
    - rest_after_night
    - poids objectifs
    """
    return RosteringConfig(
        min_days_off=1,
        max_consecutive_work_days=5,
        max_nights_per_nurse=3,
        rest_after_night=True,
        w_preference=10,
        w_balance_work=3,
        w_balance_nights=2,
    )


# =========================================================
# MAIN
# =========================================================

def print_schedule(schedule: List[List[str]]) -> None:
    num_nurses = len(schedule)
    num_days = len(schedule[0]) if num_nurses else 0
    for n in range(num_nurses):
        row = " | ".join(schedule[n])
        print(f"Infirmier {n} | {row}")


def check_coverage(schedule: List[List[str]], demand: List[Dict[str, int]]) -> None:
    shifts = ["M", "A", "N"]
    num_nurses = len(schedule)
    num_days = len(schedule[0]) if num_nurses else 0
    print("\n=== Couverture vs Demande ===")
    ok_all = True
    for d in range(num_days):
        counts = {s: 0 for s in shifts}
        for n in range(num_nurses):
            sh = schedule[n][d]
            if sh in shifts:
                counts[sh] += 1

        line = f"Jour {d} | "
        for s in shifts:
            need = demand[d][s]
            have = counts[s]
            status = "OK" if have == need else "KO"
            if have != need:
                ok_all = False
            line += f"{s}: {have}/{need} {status} | "
        print(line[:-3])

    if ok_all:
        print("✅ Couverture parfaite (tous les jours, tous les shifts).")
    else:
        print("❌ Problème de couverture.")


def main() -> None:
    print("=== Nurse Rostering CSP (CP-SAT) ===")

    # ✅ Paramètres faciles à changer
    num_nurses = 7
    num_days = 9

    demand = build_demand(num_days)
    preferences = build_preferences()
    config = build_config()

    # Solve
    res = solve_nurse_rostering(
        num_nurses=num_nurses,
        num_days=num_days,
        demand=demand,
        preferences=preferences,
        config=config,
        time_limit_s=10.0,
        log_search=False,
        num_workers=8,
    )

    print("\n--- Solver Stats ---")
    for k, v in res.stats.items():
        print(f"{k}: {v}")

    if not res.feasible or res.schedule is None:
        print("\n❌ Aucun planning faisable trouvé.")
        return

    if res.violations:
        print("\n⚠️ Violations détectées (ton modèle est incohérent avec tes contraintes):")
        for v in res.violations:
            print(" -", v)
        print("\n➡️ Corrige d'abord les contraintes/demandes.")
        return

    schedule = res.schedule
    print("\n✅ Planning trouvé :\n")
    print_schedule(schedule)
    check_coverage(schedule, demand)

    print("\n--- Metrics ---")
    for k, v in res.metrics.items():
        print(f"{k}: {v}")

    # Visualisation (lisible)
    out_dir = os.path.join("groupe-01-optimisation-planning-infirmiers", "docs")
    os.makedirs(out_dir, exist_ok=True)
    png_path = os.path.join(out_dir, "planning.png")

    plot_schedule(
        schedule=schedule,
        title="Planning infirmiers (lisible)",
        save_path=png_path,
        show=True,
    )
    print(f"\n🖼️ Image exportée: {png_path}")


if __name__ == "__main__":
    main()
