"""Projekt-szintű konfiguráció: útvonalak, országkódok, konstansok."""
from pathlib import Path

# --- Gyökér és fő mappák ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"
FIGURES_DIR = PROJECT_ROOT / "figures"
RESULTS_DIR = PROJECT_ROOT / "results"
MODEL_SUMMARIES_DIR = RESULTS_DIR / "model_summaries"

RAW_NUTS3_DIR = RAW_DIR / "nuts3"
RAW_NUTS2_DIR = RAW_DIR / "nuts2"
RAW_OSM_DIR = RAW_DIR / "osm"
RAW_EUROSTAT_DIR = RAW_DIR / "eurostat"

INTERIM_OSM_DIR = INTERIM_DIR / "osm"
INTERIM_AGGREGATED_DIR = INTERIM_DIR / "aggregated"

# --- Országok (Geofabrik kisbetűs kódok) ---
COUNTRY_CODES = ["hu", "pl", "cz", "sk"]
COUNTRY_CODES_UPPER = ["HU", "PL", "CZ", "SK"]  # Eurostat 'geo' kódok prefixe

# Geofabrik letöltési URL-sablon (Közép-Európa régió alatt találhatók)
GEOFABRIK_PBF_URL_TEMPLATE = (
    "https://download.geofabrik.de/europe/{country_code}-latest.osm.pbf"
)

# --- NUTS3 / GISCO ---
NUTS_SCALE = "03M"  # felbontás, pl. 01M / 03M / 10M / 20M / 60M
NUTS_YEAR = 2024

GISCO_NUTS3_URL_TEMPLATE = (
    "https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/"
    "NUTS_RG_{scale}_{year}_4326_LEVL_3.geojson"
)
GISCO_NUTS2_URL_TEMPLATE = (
    "https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/"
    "NUTS_RG_{scale}_{year}_4326_LEVL_2.geojson"
)


def is_nuts3_code(geo: str) -> bool:
    """pl. 'HU110' -> True. NUTS3 kód: 2 betű országkód + 3 karakter."""
    return len(geo) == 5 and geo[:2] in COUNTRY_CODES_UPPER


def is_nuts2_code(geo: str) -> bool:
    """pl. 'HU11' -> True. NUTS2 kód: 2 betű országkód + 2 karakter."""
    return len(geo) == 4 and geo[:2] in COUNTRY_CODES_UPPER


# --- Eurostat ---
EUROSTAT_SDMX_BASE_URL = (
    "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data"
)

# Fő elemzéshez letöltendő nyers dataset-kódok (a scripts/download_eurostat.sh
# is ezt a listát tölti le)
EUROSTAT_DATASET_CODES = [
    "reg_area3",
    "road_go_na_rl3g",
    "demo_r_gind3",
    "demo_r_d3dens",
    "demo_r_pjangrp3",
    "nama_10r_3empers",
    "nama_10r_3gdp",
    "bd_hgnace_r",
    "isoc_r_eb_ain2",  # kiegészítő, NUTS2 elemzéshez
]

# Fő elemzés évtartománya (NUTS3, panel-jellegű)
EUROSTAT_YEARS_MAIN = list(range(2014, 2024))  # 2014-2023

# A régió területe nem változik évente -> egyetlen fix referenciaév
EUROSTAT_YEAR_AREA = 2023

# Kiegészítő AI-elemzés éve (NUTS2)
EUROSTAT_YEAR_AI = 2025

# Minden logikai változóhoz: melyik dataset-kódból, milyen dim_filter-rel,
# mely év(ek)re és melyik területi szinten nyerjük ki. Ld. részletes indoklás:
# data/raw/eurostat/DATASET_SPEC.md
EUROSTAT_SOURCES = {
    "area": {
        "dataset_code": "reg_area3",
        "dim_filter": {"landuse": "TOTAL", "unit": "KM2"},
        "years": EUROSTAT_YEAR_AREA,
        "geo_level": "nuts3",
    },
    "road_freight_total": {
        "dataset_code": "road_go_na_rl3g",
        "dim_filter": {"nst07": "TOTAL", "unit": "THS_T"},
        "years": EUROSTAT_YEARS_MAIN,
        "geo_level": "nuts3",
    },
    "population_growth_rate": {
        "dataset_code": "demo_r_gind3",
        "dim_filter": {"indic_de": "GROWRT"},
        "years": EUROSTAT_YEARS_MAIN,
        "geo_level": "nuts3",
    },
    "net_migration": {
        "dataset_code": "demo_r_gind3",
        "dim_filter": {"indic_de": "CNMIGRAT"},
        "years": EUROSTAT_YEARS_MAIN,
        "geo_level": "nuts3",
    },
    "population_density": {
        "dataset_code": "demo_r_d3dens",
        "dim_filter": {"unit": "PER_KM2"},
        "years": EUROSTAT_YEARS_MAIN,
        "geo_level": "nuts3",
    },
    "population": {  # N — a scaling-elemzés fő tömeg-változója
        "dataset_code": "demo_r_pjangrp3",
        "dim_filter": {"sex": "T", "unit": "NR", "age": "TOTAL"},
        "years": EUROSTAT_YEARS_MAIN,
        "geo_level": "nuts3",
    },
    "employment": {
        "dataset_code": "nama_10r_3empers",
        "dim_filter": {"unit": "THS", "wstatus": "EMP", "nace_r2": "TOTAL"},
        "years": EUROSTAT_YEARS_MAIN,
        "geo_level": "nuts3",
    },
    "gdp_total": {
        "dataset_code": "nama_10r_3gdp",
        "dim_filter": {"unit": "MIO_EUR"},
        "years": EUROSTAT_YEARS_MAIN,
        "geo_level": "nuts3",
    },
    "active_enterprises": {
        "dataset_code": "bd_hgnace_r",
        "dim_filter": {"indic_sbs": "ENT_NR", "nace_r2": "B-S_X_O_S94"},
        "years": EUROSTAT_YEARS_MAIN,
        "geo_level": "nuts3",
    },
    "ai_adoption_rate": {  # kiegészítő elemzés, NUTS2, más év
        "dataset_code": "isoc_r_eb_ain2",
        "dim_filter": {"indic_is": "E_AI_TANY", "size_emp": "GE10", "unit": "PC_ENT", "nace_r2": "C10-S951_X_K"},
        "years": EUROSTAT_YEAR_AI,
        "geo_level": "nuts2",
    },
}

# --- Gravity modell ---
MASS_VARIANTS = ["population", "gdp", "osm_proxy"]
GAMMA_VALUES = [1.0, 1.5, 2.0]  # érzékenységvizsgálathoz

# --- Kulcstábla ---
NUTS3_MASTER_TABLE_PATH = PROCESSED_DIR / "nuts3_master_table.parquet"
GRAPH_PATH = PROCESSED_DIR / "graph_nuts3_v4.graphml"
SCALING_COEFFICIENTS_PATH = RESULTS_DIR / "scaling_coefficients.csv"


def gamma_to_filename_str(gamma: float) -> str:
    """1.5 -> 'g1_5' (fájlnévben tizedespont helyett aláhúzás, spec 3. szakasz)."""
    return "g" + str(gamma).replace(".", "_")