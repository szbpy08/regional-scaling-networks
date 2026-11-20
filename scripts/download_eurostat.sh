#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="data/raw/eurostat"
mkdir -p "$OUT_DIR"

CODES=(reg_area3 bd_hgnace_r road_go_na_rl3g demo_r_gind3 demo_r_d3dens demo_r_pjangrp3 nama_10r_3empers nama_10r_3gdp isoc_r_eb_ain2)

for code in "${CODES[@]}"; do
  curl -sL "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/${code}?format=tsv&compressed=true" -o "${OUT_DIR}/${code}.tsv.gz"
  gunzip -f "${OUT_DIR}/${code}.tsv.gz"
  echo "=== ${code} ==="
  head -1 "${OUT_DIR}/${code}.tsv"
done

date -u +"%Y-%m-%dT%H:%M:%SZ" > "${OUT_DIR}/DOWNLOAD_DATE.txt"