#!/usr/bin/env bash
# scripts/download_gisco.sh
#
# GISCO NUTS3 és NUTS2 határ-geojsonok letöltése.
# Forrás: https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/
# URL-forma: NUTS_RG_{SCALE}_{YEAR}_4326_LEVL_{LEVEL}.geojson
#
# Kimenet:
#   data/raw/nuts3/NUTS_RG_{SCALE}_{YEAR}_4326.geojson  (LEVL_3, átnevezve a projekt-konvencióra)
#   data/raw/nuts2/NUTS_RG_{SCALE}_{YEAR}_4326_LEVL_2.geojson

set -euo pipefail

# --- Konfiguráció -----------------------------------------------------
SCALE="${GISCO_SCALE:-03M}"   # 60M/20M/10M/03M — 03M ad kellően finom felbontást a NUTS3-OSM térbeli illesztéshez
YEAR="${GISCO_YEAR:-2024}"    # 2024/2021/2016/2013/2010
BASE_URL="https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson"

RAW_DIR="data/raw"
NUTS3_DIR="${RAW_DIR}/nuts3"
NUTS2_DIR="${RAW_DIR}/nuts2"

mkdir -p "${NUTS3_DIR}" "${NUTS2_DIR}"

# --- Segédfüggvény ------------------------------------------------------
fetch() {
    local url="$1"
    local out_path="$2"
    if [[ -s "${out_path}" ]]; then
        echo "  [skip] ${out_path} már létezik"
        return 0
    fi
    echo "  [get]  ${url}"
    if ! curl -sfL "${url}" -o "${out_path}.tmp"; then
        echo "  [hiba] letöltés sikertelen: ${url}" >&2
        rm -f "${out_path}.tmp"
        return 1
    fi
    mv "${out_path}.tmp" "${out_path}"
}

# --- NUTS3 (LEVL_3), fő elemzéshez --------------------------------------
echo "NUTS3 határok (${SCALE}, ${YEAR})..."
nuts3_url="${BASE_URL}/NUTS_RG_${SCALE}_${YEAR}_4326_LEVL_3.geojson"
nuts3_out="${NUTS3_DIR}/NUTS_RG_${SCALE}_${YEAR}_4326.geojson"
fetch "${nuts3_url}" "${nuts3_out}"

# --- NUTS2 (LEVL_2), AI-adaptáció kiegészítő elemzéshez -----------------
echo "NUTS2 határok (${SCALE}, ${YEAR})..."
nuts2_url="${BASE_URL}/NUTS_RG_${SCALE}_${YEAR}_4326_LEVL_2.geojson"
nuts2_out="${NUTS2_DIR}/NUTS_RG_${SCALE}_${YEAR}_4326_LEVL_2.geojson"
fetch "${nuts2_url}" "${nuts2_out}"

echo "Dátumbélyeg írása..."
for dir in "${NUTS3_DIR}" "${NUTS2_DIR}"; do
  {
    echo "scale=${SCALE}"
    echo "year=${YEAR}"
    date -u +"%Y-%m-%dT%H:%M:%SZ"
  } > "${dir}/DOWNLOAD_DATE.txt"
done

echo "Kész: ${nuts3_out}"
echo "Kész: ${nuts2_out}"