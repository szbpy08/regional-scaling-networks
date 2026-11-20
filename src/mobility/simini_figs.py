from __future__ import annotations

import numpy as np
from matplotlib.patches import Rectangle


def log_edges(lo, hi, per_decade):
    """Logaritmikusan egyenközű bin-határok lo és hi között (legalább hi-ig)."""
    n = int(np.ceil(np.log10(hi / lo) * per_decade))
    return lo * 10 ** (np.arange(n + 1) / per_decade)


def density_hist(values, weights, edges):
    """Súlyozott hisztogram, sűrűségként normálva: sum(dens * binszélesség) = 1.

    A normálás a mi definíciónk (a cikk szövege nem rögzíti); mivel az adatot és a modelleket
    ugyanígy normáljuk, az összehasonlítás alakja nem függ tőle.
    """
    h, _ = np.histogram(values, bins=edges, weights=weights)
    dens = h / h.sum() / np.diff(edges)
    centers = np.sqrt(edges[:-1] * edges[1:])
    return centers, dens


def dist_hist_from_matrix(E, dist_row_fn, edges):
    """P_dist(r) egy teljes (n x n) súlymátrixból, soronként számolt távolságokkal (memóriakímélő)."""
    h = np.zeros(len(edges) - 1)
    for i in range(E.shape[0]):
        w = E[i]
        if not w.any():
            continue
        h += np.histogram(dist_row_fn(i), bins=edges, weights=w)[0]
    centers = np.sqrt(edges[:-1] * edges[1:])
    return centers, h / h.sum() / np.diff(edges)


def box_stats(x_data, y_pred, edges, q=(9, 91), min_count=5):
    """Binenkénti (a megfigyelt érték szerint) statisztika az előrejelzett értékekre.

    'zöld', ha az y=x egyenes a binen belül átfedi a [q1, q2] percentilis-sávot
    (a cikk szavai: a 9. és 91. percentilis között van) -- az átfedés a mi pontosítási döntésünk.
    """
    idx = np.digitize(x_data, edges) - 1
    out = []
    for b in range(len(edges) - 1):
        m = idx == b
        if m.sum() < min_count:
            continue
        ys = y_pred[m]
        lo, hi = np.percentile(ys, q)
        out.append(dict(bin_lo=edges[b], bin_hi=edges[b + 1], center=np.sqrt(edges[b] * edges[b + 1]),
                        n=int(m.sum()), p_lo=lo, p_hi=hi, mean=ys.mean(), median=np.median(ys),
                        green=bool(lo <= edges[b + 1] and hi >= edges[b])))
    return out


def scatter_boxes(ax, x_data, y_pred, edges, title="", xlabel="Travelers (Data)", ylabel="Travelers (Model)"):
    """Fig. 2b-d stílusú ábra: szürke pontfelhő, 9-91 percentilis dobozok (zöld/piros), fekete körök = binátlag."""
    ax.scatter(x_data, y_pred, s=1, c="0.7", alpha=0.35, rasterized=True, linewidths=0)
    stats = box_stats(x_data, y_pred, edges)
    for s in stats:
        ax.add_patch(Rectangle((s["bin_lo"], s["p_lo"]), s["bin_hi"] - s["bin_lo"], s["p_hi"] - s["p_lo"],
                               facecolor="tab:green" if s["green"] else "tab:red", alpha=0.7, lw=0))
    ax.plot([s["center"] for s in stats], [s["mean"] for s in stats], "o", mfc="none", mec="k", ms=5)
    lo = min(np.min(x_data), np.min(y_pred)); hi = max(np.max(x_data), np.max(y_pred))
    ax.plot([lo, hi], [lo, hi], "k-", lw=1)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel(xlabel); ax.set_ylabel(ylabel); ax.set_title(title, fontsize=10)
    return stats