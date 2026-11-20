"""Eurostat SDMX 2.1 letöltés (bash curl-lal) és TSV-parszolás."""
import subprocess
from pathlib import Path

import pandas as pd

from src.config import EUROSTAT_SDMX_BASE_URL


def download_eurostat_tsv(dataset_code: str, out_dir: str) -> str:
    """
    Letölti az Eurostat táblát SDMX 2.1 API-n keresztül (TSV, gzip),
    majd kicsomagolja. A régi BulkDownloadListing URL-forma elavult.
    """
    out_dir_path = Path(out_dir)
    out_dir_path.mkdir(parents=True, exist_ok=True)

    gz_path = out_dir_path / f"{dataset_code}.tsv.gz"
    tsv_path = out_dir_path / f"{dataset_code}.tsv"

    url = f"{EUROSTAT_SDMX_BASE_URL}/{dataset_code}?format=tsv&compressed=true"

    subprocess.run(
        ["curl", "-L", url, "-o", str(gz_path)],
        check=True,
    )
    subprocess.run(["gunzip", "-f", str(gz_path)], check=True)

    if not tsv_path.exists():
        raise FileNotFoundError(f"Várt kimenet nem található: {tsv_path}")

    return str(tsv_path)


def parse_eurostat_tsv(
    tsv_path: str,
    geo_filter: list[str],
    years: int | list[int],
    dim_filter: dict[str, str] | None = None,
) -> pd.DataFrame:
    """
    Eurostat TSV parszolása, hosszú (long) formátumban.

    Egy vagy több évre is lehet szűrni: years=2021 -> egyetlen év,
    years=list(range(2014, 2024)) -> panel-jellegű, több sor/geo/év.

    geo_filter: NUTS3 vagy NUTS2 kódok listája (a 'geo' oszlop szűrésére —
    a paraméter neve szándékosan általános, mert mindkét szinthez használjuk).

    dim_filter: opcionális dimenzió-szűrő, pl. {"sex": "T", "age": "TOTAL"}.
    Ha None, nincs szűrés a dimenziókon (csak geo-ra és évre).

    Visszatérési formátum (hosszú/long, egy sor = egy geo-év-dimenziókombináció):
    geo, <egyéb dimenziók...>, year, value, flag
    """
    if isinstance(years, int):
        years = [years]

    df = pd.read_csv(tsv_path, sep="\t")

    dim_col = df.columns[0]  # pl. 'freq,unit,sex,age,geo\TIME_PERIOD'
    dim_names = dim_col.split("\\")[0].split(",")

    dims_df = df[dim_col].str.split(",", expand=True)
    dims_df.columns = dim_names
    df = pd.concat([dims_df, df.drop(columns=[dim_col])], axis=1)

    for col in dim_names:
        df[col] = df[col].str.strip()

    if "geo" not in df.columns:
        raise ValueError(f"Nincs 'geo' dimenzió a táblában: {tsv_path}")

    df = df[df["geo"].isin(geo_filter)].copy()

    if dim_filter:
        for dim, val in dim_filter.items():
            if dim not in df.columns:
                raise ValueError(f"Ismeretlen dimenzió a szűrőben: '{dim}'")
            df = df[df[dim] == val]

    other_dims = [c for c in dim_names if c != "geo"]
    long_rows = []

    for year in years:
        year_col_candidates = [
            c for c in df.columns if str(year) in c and c not in dim_names
        ]
        if not year_col_candidates:
            continue  # az adott év nincs a táblában (pl. tartományon kívül esik) -> kihagyjuk
        year_col = year_col_candidates[0]

        value_raw = df[year_col].astype(str).str.strip()
        flag = value_raw.str.extract(r"([a-zA-Z:]+)$")[0]
        value = pd.to_numeric(
            value_raw.str.extract(r"([\d.,]+)")[0].str.replace(",", ""),
            errors="coerce",
        )

        year_df = df[["geo"] + other_dims].copy()
        year_df["year"] = year
        year_df["value"] = value
        year_df["flag"] = flag
        long_rows.append(year_df)

    if not long_rows:
        raise ValueError(f"Egyik kért év sem található a táblában: {tsv_path}")

    return pd.concat(long_rows, ignore_index=True)