from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from ortools.sat.python import cp_model

# ============================
# TYPES
# ============================

Shift = str  # "M", "A", "N"
ClePreference = Tuple[int, int]  # (infirmier, jour)


# ============================
# CONFIGURATION GLOBALE
# ============================

@dataclass(frozen=True)
class ConfigurationPlanning:
    """
    Paramètres globaux du problème de planning.
    Modifier cette classe permet de changer les règles.
    """

    # Shifts possibles
    shifts: Tuple[Shift, ...] = ("M", "A", "N")

    # Contraintes dures
    min_jours_repos: int = 1
    max_jours_travail_consecutifs: int = 5
    max_nuits_par_infirmier: int = 3
    repos_apres_nuit: bool = True

    # Pondérations de la fonction objectif
    poids_preferences: int = 10
    poids_equilibrage_travail: int = 3
    poids_equilibrage_nuits: int = 2


# ============================
# STRUCTURE DU RÉSULTAT
# ============================

@dataclass
class ResultatResolution:
    faisable: bool
    planning: Optional[List[List[str]]]
    valeur_objectif: Optional[float]
    statistiques: Dict[str, str]
    violations: List[str]
    metriques: Dict[str, float]


# ============================
# SOLVEUR CSP
# ============================

def resoudre_planning_infirmiers(
    nombre_infirmiers: int,
    nombre_jours: int,
    demande: List[Dict[Shift, int]],
    preferences: Optional[Dict[ClePreference, Dict]] = None,
    config: Optional[ConfigurationPlanning] = None,
    limite_temps_s: float = 10.0,
    afficher_logs: bool = False,
    nombre_workers: int = 8,
) -> ResultatResolution:
    """
    Résout le problème de Nurse Rostering via CP-SAT.
    """

    if config is None:
        config = ConfigurationPlanning()
    if preferences is None:
        preferences = {}

    shifts = list(config.shifts)

    # ============================
    # CRÉATION DU MODÈLE
    # ============================

    modele = cp_model.CpModel()

    # x[infirmier, jour, shift] = 1 si l'infirmier travaille ce shift ce jour
    x = {}
    for i in range(nombre_infirmiers):
        for j in range(nombre_jours):
            for s in shifts:
                x[(i, j, s)] = modele.NewBoolVar(f"x_i{i}_j{j}_s{s}")

    # travaille[i, j] = 1 si l'infirmier travaille ce jour-là
    travaille = {}
    for i in range(nombre_infirmiers):
        for j in range(nombre_jours):
            travaille[(i, j)] = modele.NewBoolVar(f"travaille_i{i}_j{j}")
            modele.Add(travaille[(i, j)] == sum(x[(i, j, s)] for s in shifts))

    # ============================
    # CONTRAINTES DURES
    # ============================

    # 1) Un seul shift par jour max
    for i in range(nombre_infirmiers):
        for j in range(nombre_jours):
            modele.Add(sum(x[(i, j, s)] for s in shifts) <= 1)

    # 2) Couverture exacte de la demande
    for j in range(nombre_jours):
        for s in shifts:
            modele.Add(
                sum(x[(i, j, s)] for i in range(nombre_infirmiers))
                == demande[j][s]
            )

    # 3) Nombre minimum de jours de repos
    for i in range(nombre_infirmiers):
        modele.Add(
            sum(travaille[(i, j)] for j in range(nombre_jours))
            <= nombre_jours - config.min_jours_repos
        )

    # 4) Limite de jours travaillés consécutifs
    L = config.max_jours_travail_consecutifs
    if L > 0 and nombre_jours >= L + 1:
        for i in range(nombre_infirmiers):
            for debut in range(nombre_jours - L):
                modele.Add(
                    sum(travaille[(i, j)] for j in range(debut, debut + L + 1))
                    <= L
                )

    # 5) Repos obligatoire après une nuit
    if config.repos_apres_nuit:
        for i in range(nombre_infirmiers):
            for j in range(nombre_jours - 1):
                modele.Add(x[(i, j, "N")] + travaille[(i, j + 1)] <= 1)

    # 6) Limite du nombre de nuits
    for i in range(nombre_infirmiers):
        modele.Add(
            sum(x[(i, j, "N")] for j in range(nombre_jours))
            <= config.max_nuits_par_infirmier
        )

    # ============================
    # PRÉFÉRENCES (SOFT)
    # ============================

    penalites_preferences = []

    for (i, j), pref in preferences.items():
        if not (0 <= i < nombre_infirmiers and 0 <= j < nombre_jours):
            continue

        type_pref = pref.get("type")
        shift = pref.get("shift")

        penalite = modele.NewIntVar(0, 1, f"penalite_i{i}_j{j}")

        if type_pref == "prefer":
            if shift == "OFF":
                modele.Add(penalite == travaille[(i, j)])
            else:
                modele.Add(penalite + x[(i, j, shift)] == 1)

        elif type_pref == "avoid":
            if shift == "OFF":
                modele.Add(penalite + travaille[(i, j)] == 1)
            else:
                modele.Add(penalite == x[(i, j, shift)])

        penalites_preferences.append(penalite)

    # ============================
    # ÉQUILIBRAGE
    # ============================

    total_travail = []
    total_nuits = []

    for i in range(nombre_infirmiers):
        t = modele.NewIntVar(0, nombre_jours, f"total_travail_i{i}")
        n = modele.NewIntVar(0, nombre_jours, f"total_nuits_i{i}")

        modele.Add(t == sum(travaille[(i, j)] for j in range(nombre_jours)))
        modele.Add(n == sum(x[(i, j, "N")] for j in range(nombre_jours)))

        total_travail.append(t)
        total_nuits.append(n)

    max_travail = modele.NewIntVar(0, nombre_jours, "max_travail")
    min_travail = modele.NewIntVar(0, nombre_jours, "min_travail")
    modele.AddMaxEquality(max_travail, total_travail)
    modele.AddMinEquality(min_travail, total_travail)

    max_nuits = modele.NewIntVar(0, nombre_jours, "max_nuits")
    min_nuits = modele.NewIntVar(0, nombre_jours, "min_nuits")
    modele.AddMaxEquality(max_nuits, total_nuits)
    modele.AddMinEquality(min_nuits, total_nuits)

    # ============================
    # FONCTION OBJECTIF
    # ============================

    modele.Minimize(
        config.poids_preferences * sum(penalites_preferences)
        + config.poids_equilibrage_travail * (max_travail - min_travail)
        + config.poids_equilibrage_nuits * (max_nuits - min_nuits)
    )

    # ============================
    # RÉSOLUTION
    # ============================

    solveur = cp_model.CpSolver()
    solveur.parameters.max_time_in_seconds = limite_temps_s
    solveur.parameters.log_search_progress = afficher_logs
    solveur.parameters.num_search_workers = nombre_workers

    statut = solveur.Solve(modele)
    faisable = statut in (cp_model.OPTIMAL, cp_model.FEASIBLE)

    planning = None
    if faisable:
        planning = [["OFF"] * nombre_jours for _ in range(nombre_infirmiers)]
        for i in range(nombre_infirmiers):
            for j in range(nombre_jours):
                for s in shifts:
                    if solveur.Value(x[(i, j, s)]) == 1:
                        planning[i][j] = s

    return ResultatResolution(
        faisable=faisable,
        planning=planning,
        valeur_objectif=solveur.ObjectiveValue() if faisable else None,
        statistiques={
            "statut": solveur.StatusName(statut),
            "temps_s": f"{solveur.WallTime():.3f}",
            "branches": str(solveur.NumBranches()),
        },
        violations=[],
        metriques={},
    )
