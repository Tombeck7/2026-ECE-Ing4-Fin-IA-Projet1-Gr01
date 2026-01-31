from __future__ import annotations

from typing import List, Optional

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
import matplotlib.patches as mpatches


def plot_schedule(
    schedule: List[List[str]],
    title: str = "Planning infirmiers",
    nurse_labels: Optional[List[str]] = None,
    day_labels: Optional[List[str]] = None,
    save_path: Optional[str] = None,
    show: bool = True,
) -> None:
    """
    schedule: [nurse][day] in {"M","A","N","OFF"}
    """
    n_nurses = len(schedule)
    n_days = len(schedule[0]) if n_nurses else 0

    if nurse_labels is None:
        nurse_labels = [f"Infirmier {i}" for i in range(n_nurses)]
    if day_labels is None:
        day_labels = [f"Jour {d}" for d in range(n_days)]

    # Map to integers for colormap
    mapping = {"OFF": 0, "M": 1, "A": 2, "N": 3}
    data = np.zeros((n_nurses, n_days), dtype=int)
    for i in range(n_nurses):
        for j in range(n_days):
            data[i, j] = mapping.get(schedule[i][j], 0)

    # OFF, M, A, N
    cmap = ListedColormap(["#FFFFFF", "#A7D3F0", "#BDECC4", "#F7B7B7"])

    fig_w = max(10, n_days * 1.4)
    fig_h = max(5, n_nurses * 1.0)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))

    ax.imshow(data, cmap=cmap, aspect="auto", interpolation="nearest")

    # Grid lines (cell borders)
    ax.set_xticks(np.arange(-0.5, n_days, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, n_nurses, 1), minor=True)
    ax.grid(which="minor", linestyle="-", linewidth=1)
    ax.tick_params(which="minor", bottom=False, left=False)

    # Labels
    ax.set_xticks(np.arange(n_days))
    ax.set_yticks(np.arange(n_nurses))
    ax.set_xticklabels(day_labels)
    ax.set_yticklabels(nurse_labels)

    # Put big text in each cell
    for i in range(n_nurses):
        for j in range(n_days):
            txt = schedule[i][j]
            ax.text(j, i, txt, ha="center", va="center", fontsize=16, fontweight="bold")

    ax.set_title(title, fontsize=18, fontweight="bold", pad=15)

    # Legend
    legend_patches = [
        mpatches.Patch(facecolor="#A7D3F0", edgecolor="black", label="Matin (M)"),
        mpatches.Patch(facecolor="#BDECC4", edgecolor="black", label="Après-midi (A)"),
        mpatches.Patch(facecolor="#F7B7B7", edgecolor="black", label="Nuit (N)"),
        mpatches.Patch(facecolor="#FFFFFF", edgecolor="black", label="Repos (OFF)"),
    ]
    ax.legend(handles=legend_patches, loc="upper right")

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=200)

    if show:
        plt.show()
    else:
        plt.close(fig)
