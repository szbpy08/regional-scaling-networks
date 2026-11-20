"""Gravitációs referenciamodell (Simini et al., SI S5, S7).

T_ij = C * m_i^alfa * n_j^beta / r_ij^gamma, logaritmusban:
ln T = lnC + alfa*ln m + beta*ln n - gamma*ln r.
Az illesztés a megfigyelt (T > 0) párokon OLS, ami pontosan az E (log-négyzetes
eltérés) minimalizálása. A rövid és hosszú utak külön paraméterkészletet kapnak
egy rho határtávolság körül (r < rho: rövid).
A coef vektor: [lnC, alfa, beta, gamma].
"""
import numpy as np


def _X(m, n_, r):
    return np.column_stack([np.ones(len(m)), np.log(m), np.log(n_), -np.log(r)])


def _ols(X, y):
    coef = np.linalg.lstsq(X, y, rcond=None)[0]
    res = y - X @ coef
    return coef, float(res @ res)


def fit_gravity(m_i, n_j, r_km, T, rho_grid=None, min_pairs=2000):
    """Egy- és kétszakaszos gravitációs illesztés a megfigyelt párokon.

    Kizárja azokat a párokat, ahol m_i, n_j, r vagy T nem pozitív (ln 0).
    rho_grid=None esetén a megfigyelt távolságok kvantilisein pásztáz.
    Visszatér: dict(one=..., two=..., scan=[(rho, E), ...], n_excluded=...).
    """
    m_i, n_j, r_km, T = (np.asarray(a, dtype=float) for a in (m_i, n_j, r_km, T))
    ok = (m_i > 0) & (n_j > 0) & (r_km > 0) & (T > 0)
    X = _X(m_i[ok], n_j[ok], r_km[ok])
    y = np.log(T[ok])
    r = r_km[ok]
    N = int(ok.sum())

    coef1, sse1 = _ols(X, y)
    one = dict(rho=np.inf, coef_short=coef1, coef_long=coef1, E=sse1 / N,
               N=N, n_short=N, n_long=0)

    if rho_grid is None:
        rho_grid = np.quantile(r, np.linspace(0.10, 0.98, 45))
    best, scan = None, []
    for rho in rho_grid:
        s = r < rho
        if s.sum() < min_pairs or (~s).sum() < min_pairs:
            continue
        cs, sse_s = _ols(X[s], y[s])
        cl, sse_l = _ols(X[~s], y[~s])
        E = (sse_s + sse_l) / N
        scan.append((float(rho), float(E)))
        if best is None or E < best["E"]:
            best = dict(rho=float(rho), coef_short=cs, coef_long=cl, E=float(E),
                        N=N, n_short=int(s.sum()), n_long=int((~s).sum()))
    return dict(one=one, two=best, scan=np.array(scan), n_excluded=int(len(T) - N))


def gravity_expected_matrix(pop, dist, fit, dtype=np.float32):
    """Az illesztett gravitációs modell várható flow-mátrixa (n x n).

    pop:  népesség obecenként (a mátrix indexelésével azonos sorrend).
    dist: dist(i) -> az i. obec távolsága (km) mindenkihez, vagy n x n tömb.
    fit:  fit_gravity()["one"] vagy ["two"].
    Az átló és a nulla népességű obecek sora/oszlopa 0. A mátrix összege NEM
    normalizált (a gravitációs modell nem őrzi meg az összes ingázót).
    """
    pop = np.asarray(pop, dtype=float)
    n = len(pop)
    good = pop > 0
    lp = np.log(np.where(good, pop, 1.0))
    cs, cl, rho = fit["coef_short"], fit["coef_long"], fit["rho"]
    G = np.zeros((n, n), dtype=dtype)
    for i in range(n):
        if not good[i]:
            continue
        r = np.asarray(dist(i) if callable(dist) else dist[i], dtype=float)
        ok = good & (r > 0)
        lr = np.log(np.where(ok, r, 1.0))
        lnT = np.where(r < rho,
                       cs[0] + cs[1] * lp[i] + cs[2] * lp - cs[3] * lr,
                       cl[0] + cl[1] * lp[i] + cl[2] * lp - cl[3] * lr)
        G[i] = np.where(ok, np.exp(lnT), 0.0)
    return G