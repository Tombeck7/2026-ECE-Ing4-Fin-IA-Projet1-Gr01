from __future__ import annotations

from typing import List, Optional

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
import matplotlib.patches as mpatches


def afficher_planning(
    planning: List[List[str]],
    titre: str = "Planning infirmiers",
    noms_infirmiers: Optional[List[str]] = None,
    noms_jours: Optional[List[str]] = None,
    chemin_sauvegarde: Optional[str] = None,
    afficher: bool = True,
) -> None:
    """
    Affiche le planning sous forme de tableau coloré lisible.
    """

    nb_infirmiers = len(planning)
    nb_jours = len(planning[0]) if nb_infirmiers else 0

    if noms_infirmiers is None:
        noms_infirmiers = [f"Infirmier {i}" for i in range(nb_infirmiers)]
    if noms_jours is None:
        noms_jours = [f"Jour {j}" for j in range(nb_jours)]

    # Encodage numérique
    conversion = {"OFF": 0, "M": 1, "A": 2, "N": 3}
    matrice = np.zeros((nb_infirmiers, nb_jours), dtype=int)
    for i in range(nb_infirmiers):
        for j in range(nb_jours):
            matrice[i, j] = conversion[planning[i][j]]

    couleurs = ListedColormap(["#FFFFFF", "#A7D3F0", "#BDECC4", "#F7B7B7"])

    fig, ax = plt.subplots(figsize=(max(10, nb_jours * 1.4), max(5, nb_infirmiers)))
    ax.imshow(matrice, cmap=couleurs, aspect="auto")

    ax.set_xticks(range(nb_jours))
    ax.set_yticks(range(nb_infirmiers))
    ax.set_xticklabels(noms_jours)
    ax.set_yticklabels(noms_infirmiers)

    for i in range(nb_infirmiers):
        for j in range(nb_jours):
            ax.text(j, i, planning[i][j], ha="center", va="center", fontsize=16, fontweight="bold")

    ax.set_title(titre, fontsize=18, fontweight="bold")

    legende = [
        mpatches.Patch(color="#A7D3F0", label="Matin (M)"),
        mpatches.Patch(color="#BDECC4", label="Après-midi (A)"),
        mpatches.Patch(color="#F7B7B7", label="Nuit (N)"),
        mpatches.Patch(color="#FFFFFF", label="Repos (OFF)"),
    ]
    ax.legend(handles=legende, loc="upper right")

    plt.tight_layout()

    if chemin_sauvegarde:
        plt.savefig(chemin_sauvegarde, dpi=200)

    if afficher:
        plt.show()
    else:
        plt.close(fig)
