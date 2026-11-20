from __future__ import annotations

import numpy as np


def s_row(dist_i, pop, i):
    """s_ij rögzített forrásra (i) és minden célra (j), az eredeti sorrendben.

    s_ij = az i körüli, r_ij sugarú körben (a határán lévőket is beleértve) élő népesség
    a forrás (i) és a cél (j) népessége nélkül (Simini és mtsai, 2. egyenlet környezete).
    Egyenlő távolságú egységeket mind a körön belülinek számolunk (konvenció).
    """
    order = np.argsort(dist_i, kind="stable")
    d_sorted = dist_i[order]
    cum = np.cumsum(pop[order])
    pos = np.searchsorted(d_sorted, dist_i, side="right") - 1   # az utolsó egység, amelynek d <= r_ij
    s = cum[pos] - pop[i] - pop
    s[i] = np.nan                                               # i -> i nem értelmezett
    return s


def p_row(m_i, pop, s, i, N=None, finite_correction=False):
    """p_ij = m_i n_j / ((m_i + s_ij)(m_i + n_j + s_ij)) minden j-re; p_ii = 0.

    finite_correction=True: p_ij / (1 - m_i/N), hogy véges rendszerben sum_j p_ij = 1 legyen.
    """
    with np.errstate(divide="ignore", invalid="ignore"):
        p = m_i * pop / ((m_i + s) * (m_i + pop + s))
    p = np.nan_to_num(p, nan=0.0, posinf=0.0, neginf=0.0)
    p[i] = 0.0
    if finite_correction:
        p = p / (1.0 - m_i / N)
    return p


def simulate_origin(i, dist_i, pop, trials, rng):
    """Referencia-megvalósítás: a cikk 1-2. lépése (SI 2. szakasz, emisszió/abszorpció) közvetlenül.

    z_j = az n_j darab U(0,1) húzás maximuma (= U**(1/n_j)); az egyén a forráshoz legközelebbi olyan
    egységbe megy, ahol z_j > z_i. Függetlenül ellenőrzi az analitikus p_ij-t.
    Visszaadja: a célok szerinti gyakoriságokat és azon egyének arányát, akik nem ingáznak (a forrásnál a legjobb az ajánlat).
    """
    n = len(pop)
    u = rng.random((trials, n))
    has_pop = pop > 0
    z = np.where(has_pop, u ** (1.0 / np.where(has_pop, pop, 1.0)), -1.0)   # 0 népességű egység soha nem nyer
    order = np.argsort(dist_i, kind="stable")
    order = order[order != i]
    wins = z[:, order] > z[:, [i]]
    has = wins.any(axis=1)
    first = np.argmax(wins, axis=1)
    chosen = np.where(has, order[first], -1)
    freq = np.bincount(chosen[has], minlength=n) / trials
    return freq, 1.0 - has.mean()


def iter_p_rows(x, y, pop, finite_correction=True):
    """Egyenként adja vissza az (i, p_i·) párokat minden pozitív népességű forrásra.

    Memóriakímélő: egyszerre csak egy sor van a memóriában (n x n helyett).
    """
    N = pop.sum()
    for i in range(len(pop)):
        if pop[i] <= 0:
            continue
        d = np.hypot(x - x[i], y - y[i])
        yield i, p_row(pop[i], pop, s_row(d, pop, i), i, N=N, finite_correction=finite_correction)


def expected_flow_matrix(x, y, pop, N_c, finite_correction=True, dtype=np.float32):
    """Az Eq. 2 várható áramlásai: <T_ij> = T_i * p_ij, T_i = m_i * N_c / N. Alak: (n, n), átló = 0."""
    N = pop.sum()
    T = np.zeros((len(pop), len(pop)), dtype=dtype)
    for i, p in iter_p_rows(x, y, pop, finite_correction):
        T[i] = (pop[i] * N_c / N) * p
    return T


def sample_realization(x, y, pop, N_c, rng, finite_correction=True):
    """Egy sztochasztikus realizáció: forrásonként Multinomial(round(T_i), p_i·) (SI S3-S4).

    Csak a korrigált p-vel (sum_j p_ij = 1) értelmezett a multinomiális eloszlás.
    Visszaadja a ritka (sor, oszlop, darabszám) hármast.
    """
    assert finite_correction, "multinomiális mintavételhez sum_j p_ij = 1 kell"
    N = pop.sum()
    rows, cols, vals = [], [], []
    for i, p in iter_p_rows(x, y, pop, finite_correction=True):
        t_i = int(round(pop[i] * N_c / N))
        if t_i == 0:
            continue
        p = p / p.sum()                     # numerikus zaj eltüntetése
        draw = rng.multinomial(t_i, p)
        j = np.nonzero(draw)[0]
        rows.append(np.full(len(j), i)); cols.append(j); vals.append(draw[j])
    return np.concatenate(rows), np.concatenate(cols), np.concatenate(vals)
def sample_from_matrix(E, T_i, rng):
    """Sztochasztikus realizáció egy tetszőleges sor-súlyozású mátrixból: forrásonként Multinomial(T_i, E[i]/sum(E[i])).

    T_i egész darabszám (pl. a megfigyelt kijutás). Visszaadja a ritka (sor, oszlop, darabszám) hármast.
    """
    rows, cols, vals = [], [], []
    for i in range(E.shape[0]):
        t_i = int(T_i[i])
        if t_i == 0:
            continue
        p = E[i].astype(np.float64)
        p /= p.sum()
        draw = rng.multinomial(t_i, p)
        j = np.nonzero(draw)[0]
        rows.append(np.full(len(j), i)); cols.append(j); vals.append(draw[j])
    return np.concatenate(rows), np.concatenate(cols), np.concatenate(vals)