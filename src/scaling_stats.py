"""Urban scaling: log-log OLS illesztés és bootstrap robusztussági ellenőrzés."""
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt


def fit_scaling_law(
    df: pd.DataFrame,
    y_col: str,
    n_col: str = "population",
) -> dict:
    """
    Log-log OLS illesztés: log(Y) = alpha + beta * log(N) + epsilon.

    Csak a pozitív Y és N értékeket tartalmazó sorokat használja
    (log-transzformáció miatt a nulla/negatív értékek kimaradnak).

    Visszaadja:
      beta, beta_se, beta_ci_low, beta_ci_high (95%），
      alpha (intercept), r_squared, n_regions,
      breusch_pagan_pvalue (heteroszkedaszticitás-teszt),
      model (a teljes statsmodels eredményobjektum, további vizsgálathoz)
    """
    valid = df[[n_col, y_col]].dropna()
    valid = valid[(valid[n_col] > 0) & (valid[y_col] > 0)]

    if len(valid) < 3:
        raise ValueError(
            f"Túl kevés érvényes (pozitív, nem hiányzó) megfigyelés "
            f"'{y_col}' és '{n_col}' esetén: {len(valid)}"
        )

    log_n = np.log(valid[n_col])
    log_y = np.log(valid[y_col])

    X = sm.add_constant(log_n)
    model = sm.OLS(log_y, X).fit()

    beta = model.params[n_col]
    beta_se = model.bse[n_col]
    ci = model.conf_int(alpha=0.05)
    beta_ci_low, beta_ci_high = ci.loc[n_col]

    bp_test = sm.stats.diagnostic.het_breuschpagan(model.resid, model.model.exog)
    breusch_pagan_pvalue = bp_test[1]

    return {
        "y_variable": y_col,
        "n_variable": n_col,
        "alpha": model.params["const"],
        "beta": beta,
        "beta_se": beta_se,
        "beta_ci_low": beta_ci_low,
        "beta_ci_high": beta_ci_high,
        "r_squared": model.rsquared,
        "n_regions": len(valid),
        "breusch_pagan_pvalue": breusch_pagan_pvalue,
        "model": model,
    }


def bootstrap_beta_ci(
    df: pd.DataFrame,
    y_col: str,
    n_col: str = "population",
    n_iter: int = 1000,
    ci_level: float = 0.95,
    random_state: int | None = 42,
) -> tuple[float, float]:
    """
    Bootstrap konfidencia-intervallum a beta kitevőre: régiónkénti
    visszatevéses újramintavételezés (n_iter alkalommal), minden
    iterációban újrafuttatott log-log OLS.

    Visszaadja: (ci_low, ci_high) a beta eloszlásának ci_level-es
    percentilis-alapú intervallumaként.
    """
    valid = df[[n_col, y_col]].dropna()
    valid = valid[(valid[n_col] > 0) & (valid[y_col] > 0)]

    if len(valid) < 3:
        raise ValueError(
            f"Túl kevés érvényes megfigyelés a bootstraphez: {len(valid)}"
        )

    rng = np.random.default_rng(random_state)
    betas = np.empty(n_iter)

    log_n_full = np.log(valid[n_col]).to_numpy()
    log_y_full = np.log(valid[y_col]).to_numpy()
    n_obs = len(valid)

    for i in range(n_iter):
        idx = rng.integers(0, n_obs, size=n_obs)
        log_n_sample = log_n_full[idx]
        log_y_sample = log_y_full[idx]

        X = sm.add_constant(log_n_sample)
        model = sm.OLS(log_y_sample, X).fit()
        betas[i] = model.params[1]

    alpha = 1 - ci_level
    ci_low = np.percentile(betas, 100 * alpha / 2)
    ci_high = np.percentile(betas, 100 * (1 - alpha / 2))

    return float(ci_low), float(ci_high)


def compare_ci_methods(
    df: pd.DataFrame,
    y_col: str,
    year_col: str = "year",
    n_col: str = "population",
    years: list[int] | None = None,
    n_iter: int = 1000,
    ci_level: float = 0.95,
    random_state: int | None = 42,
) -> pd.DataFrame:
    """
    Évenkénti beta becslés OLS és bootstrap CI-vel, összehasonlításra.

    Minden évre lefuttatja a fit_scaling_law()-t (OLS beta + CI) és a
    bootstrap_beta_ci()-t (bootstrap CI, ugyanarra a beta pontbecslésre).

    Visszaadja: DataFrame egy sorral/évvel, oszlopok:
      year, beta, beta_se, r_squared, n_regions, breusch_pagan_pvalue,
      ols_ci_low, ols_ci_high, boot_ci_low, boot_ci_high
    """
    if years is None:
        years = sorted(df[year_col].dropna().unique())

    rows = []
    for year in years:
        df_year = df[df[year_col] == year]

        ols_fit = fit_scaling_law(df_year, y_col=y_col, n_col=n_col)
        boot_ci_low, boot_ci_high = bootstrap_beta_ci(
            df_year, y_col=y_col, n_col=n_col,
            n_iter=n_iter, ci_level=ci_level, random_state=random_state,
        )

        rows.append({
            "year": year,
            "beta": ols_fit["beta"],
            "beta_se": ols_fit["beta_se"],
            "r_squared": ols_fit["r_squared"],
            "n_regions": ols_fit["n_regions"],
            "breusch_pagan_pvalue": ols_fit["breusch_pagan_pvalue"],
            "ols_ci_low": ols_fit["beta_ci_low"],
            "ols_ci_high": ols_fit["beta_ci_high"],
            "boot_ci_low": boot_ci_low,
            "boot_ci_high": boot_ci_high,
        })

    return pd.DataFrame(rows)


def plot_ci_comparison(
    comparison_df: pd.DataFrame,
    y_label: str = "β",
    title: str | None = None,
) -> tuple[plt.Figure, plt.Axes]:
    """
    Errorbar plot: OLS CI és bootstrap CI egymás mellett, évenként,
    ugyanarra a beta pontbecslésre.
    """
    fig, ax = plt.subplots(figsize=(9, 5))
    offset = 0.12

    ax.errorbar(
        comparison_df["year"] - offset, comparison_df["beta"],
        yerr=[
            comparison_df["beta"] - comparison_df["ols_ci_low"],
            comparison_df["ols_ci_high"] - comparison_df["beta"],
        ],
        fmt="o", capsize=4, label="OLS CI", color="tab:blue",
    )

    ax.errorbar(
        comparison_df["year"] + offset, comparison_df["beta"],
        yerr=[
            comparison_df["beta"] - comparison_df["boot_ci_low"],
            comparison_df["boot_ci_high"] - comparison_df["beta"],
        ],
        fmt="s", capsize=4, label="Bootstrap CI", color="tab:orange",
    )

    ax.axhline(1, color="grey", linestyle="--", linewidth=1)
    ax.set_xlabel("Év")
    ax.set_ylabel(y_label)
    if title:
        ax.set_title(title)
    ax.legend()
    ax.set_xticks(comparison_df["year"])
    fig.tight_layout()
    return fig, ax


def plot_scaling_scatter(
    df: pd.DataFrame,
    y_col: str,
    n_col: str = "population",
    year: int | None = None,
    year_col: str = "year",
    ax=None,
):
    """
    Bettencourt-stílusú log-log szórásdiagram: LN[N] vs LN[Y], piros
    illesztett egyenessel, béta és R² felirattal a panelen.

    Ha year meg van adva, csak arra az évre szűr (year_col alapján).
    """
    data = df if year is None else df[df[year_col] == year]
    fit = fit_scaling_law(data, y_col=y_col, n_col=n_col)

    valid = data[[n_col, y_col]].dropna()
    valid = valid[(valid[n_col] > 0) & (valid[y_col] > 0)]
    log_n = np.log(valid[n_col])
    log_y = np.log(valid[y_col])

    if ax is None:
        fig, ax = plt.subplots(figsize=(6, 5))
    else:
        fig = ax.figure

    ax.scatter(log_n, log_y, color="tab:blue", edgecolor="white", s=40, zorder=3)

    x_line = np.linspace(log_n.min(), log_n.max(), 100)
    y_line = fit["alpha"] + fit["beta"] * x_line
    ax.plot(x_line, y_line, color="tab:red", linewidth=2, zorder=2)

    ax.text(
        0.05, 0.92,
        f"β={fit['beta']:.3f}   R²={fit['r_squared']:.2f}",
        transform=ax.transAxes, fontsize=12, va="top",
    )

    ax.set_xlabel(f"LN[{n_col}]")
    ax.set_ylabel(f"LN[{y_col}]")
    return fig, ax