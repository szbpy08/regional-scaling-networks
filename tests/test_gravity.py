import numpy as np
from mobility.gravity import fit_gravity, gravity_expected_matrix


def _synthetic(n=250, seed=0):
    rng = np.random.default_rng(seed)
    xy = rng.uniform(0, 100, size=(n, 2))
    pop = np.exp(rng.normal(8, 1.2, n))
    d = np.linalg.norm(xy[:, None] - xy[None], axis=2)
    ii, jj = np.where(~np.eye(n, dtype=bool))
    r = d[ii, jj]
    cs = np.array([1.0, 0.4, 0.9, 0.8])
    cl = np.array([2.0, 0.7, 0.6, 1.9])
    def lnT(c):
        return c[0] + c[1] * np.log(pop[ii]) + c[2] * np.log(pop[jj]) - c[3] * np.log(r)
    T = np.exp(np.where(r < 40.0, lnT(cs), lnT(cl)))
    return pop, d, ii, jj, r, T, cs, cl


def test_fit_recovers_two_regimes():
    pop, d, ii, jj, r, T, cs, cl = _synthetic()
    fit = fit_gravity(pop[ii], pop[jj], r, T, rho_grid=[40.0])
    np.testing.assert_allclose(fit["two"]["coef_short"], cs, atol=1e-6)
    np.testing.assert_allclose(fit["two"]["coef_long"], cl, atol=1e-6)
    assert fit["two"]["E"] < 1e-10
    assert fit["n_excluded"] == 0


def test_expected_matrix_matches_formula():
    pop, d, ii, jj, r, T, *_ = _synthetic()
    fit = fit_gravity(pop[ii], pop[jj], r, T, rho_grid=[40.0])
    G = gravity_expected_matrix(pop, lambda i: d[i], fit["two"], dtype=np.float64)
    np.testing.assert_allclose(G[ii, jj], T, rtol=1e-6)
    assert np.all(np.diag(G) == 0)


def test_zero_population_unit_is_zero():
    pop, d, ii, jj, r, T, *_ = _synthetic()
    fit = fit_gravity(pop[ii], pop[jj], r, T, rho_grid=[40.0])
    pop0 = pop.copy(); pop0[7] = 0
    G = gravity_expected_matrix(pop0, d, fit["two"], dtype=np.float64)
    assert np.all(G[7] == 0) and np.all(G[:, 7] == 0)