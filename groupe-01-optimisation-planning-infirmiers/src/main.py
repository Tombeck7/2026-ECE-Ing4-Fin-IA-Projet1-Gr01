from __future__ import annotations

import os
from typing import Dict, List

from model import ConfigurationPlanning, resoudre_planning_infirmiers
from viz import afficher_planning


# =========================================================
# ICI TU MODIFIES FACILEMENT LE PROBLÈME
# =========================================================

def construire_demande(nombre_jours: int) -> List[Dict[str, int]]:
    """
    Demande par jour.
    Ici : 2 Matin, 2 Après-midi, 1 Nuit chaque jour.
    """
    return [{"M": 2, "A": 2, "N": 1} for _ in range(nombre_jours)]


def construire_preferences() -> Dict:
    """
    Préférences infirmiers (contraintes souples).
    Clé = (infirmier, jour)
    """
    return {
        (0, 0): {"type": "prefer", "shift": "OFF"},
        (1, 1): {"type": "avoid", "shift": "N"},
        (2, 3): {"type": "prefer", "shift": "M"},
        (3, 4): {"type": "avoid", "shift": "N"},
        (4, 6): {"type": "prefer", "shift": "OFF"},
    }


def construire_configuration() -> ConfigurationPlanning:
    """
    Contraintes globales et pondérations.
    """
    return ConfigurationPlanning(
        min_jours_repos=1,
        max_jours_travail_consecutifs=5,
        max_nuits_par_infirmier=3,
        repos_apres_nuit=True,
        poids_preferences=10,
        poids_equilibrage_travail=3,
        poids_equilibrage_nuits=2,
    )


# =========================================================
# AFFICHAGES
# =========================================================

def afficher_planning_console(planning: List[List[str]]) -> None:
    for i, ligne in enumerate(planning):
        print(f"Infirmier {i} | " + " | ".join(ligne))


def verifier_couverture(planning: List[List[str]], demande: List[Dict[str, int]]) -> None:
    shifts = ["M", "A", "N"]
    print("\n=== Couverture vs Demande ===")
    for j in range(len(demande)):
        compte = {s: 0 for s in shifts}
        for i in range(len(planning)):
            if planning[i][j] in shifts:
                compte[planning[i][j]] += 1

        ligne = f"Jour {j} | "
        for s in shifts:
            ok = "OK" if compte[s] == demande[j][s] else "KO"
            ligne += f"{s}: {compte[s]}/{demande[j][s]} {ok} | "
        print(ligne[:-3])


# =========================================================
# MAIN
# =========================================================

def main() -> None:
    print("=== Nurse Rostering CSP (CP-SAT) ===")

    nombre_infirmiers = 6
    nombre_jours = 10

    demande = construire_demande(nombre_jours)
    preferences = construire_preferences()
    config = construire_configuration()

    resultat = resoudre_planning_infirmiers(
        nombre_infirmiers=nombre_infirmiers,
        nombre_jours=nombre_jours,
        demande=demande,
        preferences=preferences,
        config=config,
    )

    print("\n--- Statistiques solveur ---")
    for k, v in resultat.statistiques.items():
        print(f"{k}: {v}")

    if not resultat.faisable or resultat.planning is None:
        print("\n❌ Aucun planning faisable trouvé.")
        return

    print("\n✅ Planning trouvé :\n")
    afficher_planning_console(resultat.planning)
    verifier_couverture(resultat.planning, demande)

    print("\n--- Métriques ---")
    for k, v in resultat.metriques.items():
        print(f"{k}: {v}")

    # Visualisation graphique
    dossier_docs = os.path.join("groupe-01-optimisation-planning-infirmiers", "docs")
    os.makedirs(dossier_docs, exist_ok=True)
    chemin_image = os.path.join(dossier_docs, "planning.png")

    afficher_planning(
        planning=resultat.planning,
        titre="Planning infirmiers",
        chemin_sauvegarde=chemin_image,
        afficher=True,
    )

    print(f"\n🖼️ Image exportée : {chemin_image}")


if __name__ == "__main__":
    main()
