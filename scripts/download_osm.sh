#!/usr/bin/env bash
# scripts/download_osm.sh
#
# OSM .pbf kivonatok letöltése Geofabrik-ról a V4 országokra.
# Forrás: https://download.geofabrik.de/europe/
#
# Kimenet: data/raw/osm/{COUNTRY_CODE}-latest.osm.pbf
#          {COUNTRY_CODE} ∈ {hu, pl, cz, sk} — a projekt-konvenció szerinti kisbetűs kód
#          (nem feltétlenül egyezik a Geofabrik saját fájlnév-szegmensével, ld. lenn)

set -euo pipefail

BASE_URL="https://download.geofabrik.de/europe"
OUT_DIR="data/raw/osm"
mkdir -p "${OUT_DIR}"

# projekt-kód -> Geofabrik fájlnév-szegmens
declare -A GEOFABRIK_SEGMENT=(
    [hu]="hungary"
    [pl]="poland"
    [cz]="czech-republic"
    [sk]="slovakia"
)

fetch_country() {
    local code="$1"
    local segment="${GEOFABRIK_SEGMENT[$code]}"
    local url="${BASE_URL}/${segment}-latest.osm.pbf"
    local md5_url="${url}.md5"
    local out_path="${OUT_DIR}/${code}-latest.osm.pbf"
    local md5_path="${out_path}.md5"

    echo "== ${code} (${segment}) =="

    echo "  [get] ${url}"
    curl -sfL "${url}" -o "${out_path}.tmp"

    echo "  [get] ${md5_url}"
    if curl -sfL "${md5_url}" -o "${md5_path}.tmp"; then
        # a Geofabrik .md5 fájl a saját fájlnevére hivatkozik, nem a mi átnevezett fájlunkra,
        # ezért az ellenőrzéshez a hash-t kell kivonni és a helyi fájlnévhez illeszteni
        expected_hash="$(awk '{print $1}' "${md5_path}.tmp")"
        actual_hash="$(md5sum "${out_path}.tmp" | awk '{print $1}')"
        if [[ "${expected_hash}" != "${actual_hash}" ]]; then
            echo "  [hiba] MD5-ellenőrzés sikertelen ${code}-ra (várt: ${expected_hash}, kapott: ${actual_hash})" >&2
            rm -f "${out_path}.tmp" "${md5_path}.tmp"
            return 1
        fi
        mv "${md5_path}.tmp" "${md5_path}"
        echo "  [ok]  MD5 egyezik"
    else
        echo "  [warn] .md5 nem elérhető, ellenőrzés kihagyva" >&2
        rm -f "${md5_path}.tmp"
    fi

    mv "${out_path}.tmp" "${out_path}"
    echo "  [kész] ${out_path} ($(du -h "${out_path}" | cut -f1))"
}

FAILED=()
for code in hu pl cz sk; do
    if ! fetch_country "${code}"; then
        FAILED+=("${code}")
    fi
done

date -u +"%Y-%m-%dT%H:%M:%SZ" > "${OUT_DIR}/DOWNLOAD_DATE.txt"

if (( ${#FAILED[@]} > 0 )); then
    echo "Sikertelen letöltések: ${FAILED[*]}" >&2
    exit 1
fi

echo "Minden ország OSM-kivonata letöltve: ${OUT_DIR}"