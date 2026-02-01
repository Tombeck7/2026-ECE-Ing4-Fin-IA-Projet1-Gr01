from __future__ import annotations

from copy import deepcopy
from typing import Dict, List

from model import ConfigurationPlanning, resoudre_planning_infirmiers


def demande_constante(nombre_jours: int) -> List[Dict[str, int]]:
    return [{"M": 2, "A": 2, "N": 1} for _ in range(nombre_jours)]


def preferences_demo() -> Dict:
    return {
        (0, 0): {"type": "prefer", "shift": "OFF"},
        (1, 1): {"type": "avoid", "shift": "N"},
        (2, 3): {"type": "prefer", "shift": "M"},
        (4, 6): {"type": "prefer", "shift": "OFF"},
    }


def lancer_cas(
    nom: str,
    nb_infirmiers: int,
    nb_jours: int,
    demande,
    preferences,
    config: ConfigurationPlanning,
):
    resultat = resoudre_planning_infirmiers(
        nb_infirmiers,
        nb_jours,
        demande,
        preferences,
        config,
    )

    if not resultat.faisable or resultat.violations:
        return {"cas": nom, "statut": "INFAISABLE"}

    return {
        "cas": nom,
        "statut": "OK",
        "objectif": resultat.valeur_objectif,
        "equilibre_travail": resultat.metriques.get("work_spread"),
        "equilibre_nuits": resultat.metriques.get("night_spread"),
        "satisfaction_preferences": resultat.metriques.get("pref_satisfaction"),
    }


def main():
    nb_infirmiers = 6
    nb_jours = 7

    demande = demande_constante(nb_jours)
    preferences = preferences_demo()

    config_base = ConfigurationPlanning()

    resultats = []

    resultats.append(lancer_cas("sans_preferences", nb_infirmiers, nb_jours, demande, {}, config_base))
    resultats.append(lancer_cas("avec_preferences", nb_infirmiers, nb_jours, demande, preferences, config_base))

    config_equilibre_fort = deepcopy(config_base)
    config_equilibre_fort = ConfigurationPlanning(
        min_jours_repos=config_base.min_jours_repos,
        max_jours_travail_consecutifs=config_base.max_jours_travail_consecutifs,
        max_nuits_par_infirmier=config_base.max_nuits_par_infirmier,
        repos_apres_nuit=config_base.repos_apres_nuit,
        poids_preferences=5,
        poids_equilibrage_travail=10,
        poids_equilibrage_nuits=5,
    )

    resultats.append(
        lancer_cas("equilibrage_fort", nb_infirmiers, nb_jours, demande, preferences, config_equilibre_fort)
    )

    print("\n=== RÉSULTATS DES EXPÉRIMENTS ===")
    for r in resultats:
        print(r)


if __name__ == "__main__":
    main()
