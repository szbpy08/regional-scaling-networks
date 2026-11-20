# Network Science in Theory and Practice: An Interdisciplinary Approach to Economic and Social Problems

Code, result tables and figures of a research project on **urban/regional scaling laws** and
**commuting networks** in the 115 NUTS3 regions of Czechia (CZ), Poland (PL), Hungary (HU)
and Slovakia (SK).

The main question: how much of the superlinear scaling of regional GDP with resident
population comes from the concentration of workplaces created by commuting, and how much
from higher labour productivity. In formula form:

```
beta_Y = beta_E + beta_P        (Y = GDP, E = workplace employment, P = Y / E)
```

Gravity and radiation mobility models are used as null models for the commuting network.

> This repository documents the analysis behind a thesis. It is not a software package.
> Raw data is **not** included; it is downloaded by the scripts and notebooks (see [Data](#data)).

---

## Contents

- [Repository structure](#repository-structure)
- [Environments](#environments)
- [Data](#data)
- [Notebooks](#notebooks)
- [How to run](#how-to-run)
- [Notes and limitations](#notes-and-limitations)
- [Licence](#licence)
- [Acknowledgement](#acknowledgement)
- [Citation](#citation)

---

## Repository structure

```
.
├── LICENSE                     # GPL-3.0 (code)
├── README.md
├── environment.yml             # conda environments (3, see below)
├── environment_mobility.yml
├── environment_tdlm.yml
├── scripts/                    # download helpers, run from the repo root
├── src/                        # shared Python modules (paths, scaling statistics,
│                               #   spatial join, OSM processing, gravity/radiation models)
├── tests/                      # tests of the gravity and radiation implementations
├── notebooks/                  # analysis notebooks, run in numerical order
├── tables/                     # result tables (CSV) behind the tables of the thesis
│   └── LICENSE                 #   ODbL 1.0 (tables)
├── figures/                    # figures used in the thesis
└── assets/                     # funder logo
```

The code creates a `data/` folder (`raw/`, `interim/`, `processed/`) when it runs;
it is not part of the repository.

All paths in the code are relative to the repository root (`src/config.py`).
Notebook outputs are cleared; each notebook starts with a short summary of its inputs and outputs.

---

## Environments

Three separate conda environments are used, because the mobility packages have
conflicting version requirements. The exact package versions are in the `.yml` files.

| Environment file | Used for |
|---|---|
| `environment.yml` | main analysis (data preparation, scaling, spatial statistics) |
| `environment_mobility.yml` | scikit-mobility notebooks |
| `environment_tdlm.yml` | PyTDLM notebooks |

```bash
conda env create -f environment.yml
conda env create -f environment_mobility.yml
conda env create -f environment_tdlm.yml
```

Each notebook's kernel is stored in its metadata; select the matching environment in Jupyter.

---

## Data

Raw data is not redistributed. Every download step skips files that already exist,
so a rerun after a crash continues where it stopped.

| Source | Content | Reference year | Obtained by |
|---|---|---|---|
| Eurostat | population, area, GDP, employment, enterprises (`demo_r_pjangrp3`, `demo_r_gind3`, `demo_r_d3dens`, `reg_area3`, `nama_10r_3gdp`, `nama_10r_3empers`, `bd_hgnace_r`) | 2023 (main analysis) | `scripts/download_eurostat.sh` |
| Eurostat (supplementary) | `isoc_r_eb_ain2`, NUTS2 level; supplementary analysis, not used in the thesis | see `src/config.py` | `scripts/download_eurostat.sh` |
| Eurostat GISCO | NUTS2 / NUTS3 boundaries (2024, 1:3M) | 2024 | `scripts/download_gisco.sh` |
| OpenStreetMap (Geofabrik) | V4 country extracts (`.osm.pbf`): roads, buildings, POIs | September 2026 snapshot | `scripts/download_osm.sh` |
| ČSÚ, Census 2021 (CZ) | commuting to work, municipality (`obec`) and region (`kraj`) level | 2021 | notebooks 05, 09, 22 |
| GUS (PL) | commuting-to-work flow matrix (`gmina` level, wage employees, flows ≥ 3) | 2021 | notebooks 05b, 09, 22 |
| KSH, Census 2022 (HU) | employed population and commuters by settlement | 2022 | notebook 10 |
| ŠÚ SR, Census 2021 (SK) | statistical lexicon of municipalities (outgoing commuters) | 2021 | notebook 10 |

`scripts/inspect_dims.sh` lists the dimension codes of the downloaded Eurostat tables
(used to choose the filters in `src/config.py`).

**Attribution**

- Eurostat data © European Union. Data were downloaded, merged and transformed by the author;
  Eurostat bears no responsibility for the results or their interpretation.
- Administrative boundaries © EuroGeographics.
- OSM data © OpenStreetMap contributors, available under the
  [Open Database License (ODbL)](https://www.openstreetmap.org/copyright).
  The map backgrounds of the figures are also © OpenStreetMap contributors.

**Commuting definitions differ by country** (all employed vs. wage employees only,
observed flows vs. model-generated matrices for HU/SK). The thesis discusses this in detail.

---

## Notebooks

Run from the `notebooks/` folder.

### 1. Data preparation

| Notebook | Purpose |
|---|---|
| `01_data_acquisition` | Checks that the raw files exist and are readable |
| `02_osm_processing` | Cuts the OSM extracts into tiles and extracts road networks, buildings and POIs |
| `03_spatial_aggregation` | Aggregates OSM indicators to NUTS3 and joins them with Eurostat → `nuts3_master_table.parquet` |

### 2. Scaling

| Notebook | Purpose |
|---|---|
| `04_scaling_analysis` | Scaling exponents β (log-log OLS, bootstrap CI), with and without capitals |
| `14_scaling_by_country` | β separately for CZ, PL, HU, SK |
| `19_core_scaling_decomposition` | **Main result:** β_Y = β_E + β_P and the commuting component β_E − β_R |
| `21_spatial_residuals` | Moran's I of the scaling residuals |
| `25_year_check` | Sensitivity to the population year (2021 vs 2023) |

### 3. Gravity and radiation models

| Notebook | Purpose |
|---|---|
| `05_gravity_network`, `05b_gravity_network_pl` | Gravity (scikit-mobility) and radiation models on NUTS3 commuting, CZ / PL |
| `06_lenormand_skmob_cz`, `06b_lenormand_skmob_pl` | Comparison of trip distribution laws, scikit-mobility |
| `07_lenormand_pytdlm_cz`, `07b_lenormand_pytdlm_pl` | Same comparison with PyTDLM, all four constraint levels |
| `08_lenormand_graph_export`, `08b_lenormand_graph_export_levels` | Exports observed and simulated networks as GraphML |
| `09_lenormand_multilevel` | Model comparison across spatial levels (CZ obec → kraj, PL gmina → NUTS3) |
| `10_v4_inputs` | HU / SK commuting totals (N_c) for the model runs |
| `11_v4_model_run`, `11b_cz_pl_model_run` | Settlement-level model runs (HU/SK, then CZ/PL), aggregated to NUTS3 |

### 4. Gravity destination exponent and functional regions

| Notebook | Purpose |
|---|---|
| `15_b_estimation` | Destination exponent b from the gravity fits |
| `16_b_bootstrap` | Region bootstrap of b |
| `18_b_w_estimation` | b with GDP / enterprises as destination mass; test of b_N ≈ β_W · b_W |
| `20_ppml_distance` | b estimated with PPML, origin fixed effects and spline distance |
| `22_functional_regions` | Community detection on the commuting network; administrative vs functional regions |

### 5. Output

| Notebook | Purpose |
|---|---|
| `23_figures` | Figures of the thesis from the saved result tables |

---

## How to run

```bash
# 1. download raw data (from the repository root)
bash scripts/download_gisco.sh
bash scripts/download_eurostat.sh
bash scripts/download_osm.sh

# 2. start Jupyter and run the notebooks in numerical order,
#    each with the matching environment
cd notebooks
jupyter lab
```

Practical notes:

- Expensive steps write their output to disk and skip themselves if the file already
  exists, so a notebook can be rerun after a kernel crash.
- The OSM processing (02–03) and the settlement-level model runs (09, 11, 11b) are
  memory- and time-intensive.

---

## Notes and limitations

- Economic variables refer to **2023**, commuting data to **2021** (HU: 2022),
  OSM data to **September 2026**.
- For HU and SK no observed origin–destination matrix is available; their commuting
  networks are model-generated and are treated separately from the observed CZ / PL networks.
- NUTS3 regions are administrative units, not functional urban areas (modifiable areal
  unit problem); notebook 22 compares the two.

---

## Licence

- **Code** (`notebooks/`, `src/`, `scripts/`, `tests/`): GNU General Public License v3.0 or later
  (`GPL-3.0-or-later`), see `LICENSE`.
- **Result tables** (`tables/`): Open Database License v1.0 (ODbL), see `tables/LICENSE`,
  because some tables are derived from OpenStreetMap data.
- **Figures** (`figures/`): © <author>; map backgrounds © OpenStreetMap contributors.
- **Logo** (`assets/`): property of its owner, not covered by the licences of this repository.

Third-party packages keep their own licences (e.g. PyTDLM: GPL-3.0,
scikit-mobility: BSD-3-Clause, python-igraph: GPL-2.0-or-later).

---

## Acknowledgement

<img src="assets/ekop_logo.png" alt="EKÖP logo" height="60">

Supported by the University Research Scholarship Programme (EKÖP), grant no. EKÖP-26-2-SZTE-374,
of the Ministry of Culture and Innovation from the source of the National Research,
Development and Innovation Fund.

---

## Citation

If you use this material, please cite this repository:

Boglárka Szabó (2026): *Network Science in Theory and Practice: An Interdisciplinary Approach to
Economic and Social Problems.* GitHub repository, https://github.com/szbpy08/regional-scaling-networks