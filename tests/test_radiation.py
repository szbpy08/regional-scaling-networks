import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from mobility.radiation import p_row, s_row, simulate_origin


def test_toy_example_hand_computed():
    x = np.array([0.0, 1.0, 3.0]); y = np.zeros(3); pop = np.array([10.0, 20.0, 30.0])
    d = np.hypot(x - x[0], y - y[0])
    s = s_row(d, pop, 0)
    p = p_row(pop[0], pop, s, 0)
    assert np.allclose(s[1:], [0.0, 20.0])
    assert np.allclose(p[1:], [200 / 300, 300 / 1800])
    assert np.isclose(p.sum(), 1 - pop[0] / pop.sum())
    assert np.isclose(p_row(pop[0], pop, s, 0, N=pop.sum(), finite_correction=True).sum(), 1.0)


def test_sum_identity_and_lambda_invariance():
    rng = np.random.default_rng(0)
    n = 300
    x = rng.uniform(0, 1e5, n); y = rng.uniform(0, 1e5, n)
    pop = rng.integers(10, 5000, n).astype(float)
    N = pop.sum()
    for i in range(n):
        d = np.hypot(x - x[i], y - y[i])
        p = p_row(pop[i], pop, s_row(d, pop, i), i)
        assert abs(p.sum() - (1 - pop[i] / N)) < 1e-9
        p2 = p_row(7.3 * pop[i], 7.3 * pop, s_row(d, 7.3 * pop, i), i)
        assert np.abs(p - p2).max() < 1e-12


def test_zero_population_destination():
    rng = np.random.default_rng(1)
    n = 50
    x = rng.uniform(0, 1e4, n); y = rng.uniform(0, 1e4, n)
    pop = rng.integers(10, 500, n).astype(float); pop[5] = 0.0
    d = np.hypot(x - x[0], y - y[0])
    p = p_row(pop[0], pop, s_row(d, pop, 0), 0)
    assert p[5] == 0.0
    assert np.isclose(p.sum(), 1 - pop[0] / pop.sum())


def test_matches_direct_simulation_of_paper_process():
    """Az analitikus p_ij egyezzen a cikk folyamatának közvetlen szimulációjával (és a maradók aránya m_i/N legyen)."""
    rng = np.random.default_rng(42)
    n = 8
    x = rng.uniform(0, 100, n); y = rng.uniform(0, 100, n)
    pop = rng.integers(3, 25, n).astype(float); pop[3] = 0.0
    N = pop.sum()
    trials = 1_000_000
    for i in (0, 1, 5):
        d = np.hypot(x - x[i], y - y[i])
        p = p_row(pop[i], pop, s_row(d, pop, i), i)
        freq, stay = simulate_origin(i, d, pop, trials, rng)
        se = np.sqrt(np.maximum(p * (1 - p), 1e-12) / trials)
        z = np.abs(freq - p) / se
        z[i] = 0.0
        assert z.max() < 4.5, (i, z)
        assert abs(stay - pop[i] / N) < 5 * np.sqrt(pop[i] / N * (1 - pop[i] / N) / trials)