"""OSM .pbf feldolgozás pyrosm-mal, rétegenként (network, buildings, pois)."""
from pathlib import Path

import geopandas as gpd

from src.config import INTERIM_OSM_DIR

try:
    from pyrosm import OSM
except ImportError as exc:
    raise ImportError(
        "A pyrosm csomag hiányzik. Telepítsd: pip install pyrosm "
        "(vagy ellenőrizd az environment.yml pip szekcióját)."
    ) from exc

# A projektben használt network-alrétegek: melyik pyrosm network_type-nak
# felel meg, és milyen néven mentjük el (fájlnév-utótag).
NETWORK_VARIANTS = {
    "driving": "driving",
    "walking": "walking",
}


def load_osm_layers(
    pbf_path: str,
    layers: list[str],
    network_variants: list[str] | None = None,
) -> dict[str, gpd.GeoDataFrame]:
    """
    Betölti a kért rétegeket egy .pbf fájlból, KÜLÖN pyrosm-hívásokkal
    (memóriakímélés miatt, spec 7. szakasz — Lengyelországnál kritikus lehet).

    layers: az alábbiak részhalmaza: "network", "buildings", "pois"

    network_variants: ha "network" szerepel a layers-ben, itt adható meg,
    mely hálózattípusok kellenek (NETWORK_VARIANTS kulcsai közül, pl.
    ["driving", "walking"]). Alapértelmezés: mindkettő. Minden variánshoz
    külön kulcs kerül a visszaadott dict-be: "network_driving", "network_walking".
    """
    valid_layers = {"network", "buildings", "pois"}
    unknown = set(layers) - valid_layers
    if unknown:
        raise ValueError(f"Ismeretlen réteg(ek): {unknown}. Érvényesek: {valid_layers}")

    if network_variants is None:
        network_variants = list(NETWORK_VARIANTS.keys())
    unknown_variants = set(network_variants) - set(NETWORK_VARIANTS.keys())
    if unknown_variants:
        raise ValueError(
            f"Ismeretlen network_variant(ok): {unknown_variants}. "
            f"Érvényesek: {list(NETWORK_VARIANTS.keys())}"
        )

    result: dict[str, gpd.GeoDataFrame] = {}

    for layer in layers:
        if layer == "network":
            for variant in network_variants:
                osm = OSM(pbf_path)  # rétegenként/variánsonként újra-példányosítva
                gdf = osm.get_network(network_type=NETWORK_VARIANTS[variant])
                if gdf is None or gdf.empty:
                    raise ValueError(
                        f"A 'network' ({variant}) réteg üres vagy nem tölthető be: {pbf_path}"
                    )
                result[f"network_{variant}"] = gdf
                del osm
            continue

        osm = OSM(pbf_path)
        if layer == "buildings":
            gdf = osm.get_buildings()
        elif layer == "pois":
            gdf = osm.get_pois()

        if gdf is None or gdf.empty:
            raise ValueError(f"A '{layer}' réteg üres vagy nem tölthető be: {pbf_path}")

        result[layer] = gdf
        del osm

    return result


def save_interim_layer(gdf: gpd.GeoDataFrame, country_code: str, layer_name: str) -> Path:
    """
    Elmenti a réteget parquet-ként a data/interim/osm/ alá.
    layer_name pl.: "network_driving", "network_walking", "buildings", "pois"
    -> fájlnév: {COUNTRY_CODE}_{layer_name}.parquet
    """
    valid_layers = {f"network_{v}" for v in NETWORK_VARIANTS} | {"buildings", "pois"}
    if layer_name not in valid_layers:
        raise ValueError(f"Ismeretlen réteg: '{layer_name}'. Érvényesek: {valid_layers}")

    INTERIM_OSM_DIR.mkdir(parents=True, exist_ok=True)
    out_path = INTERIM_OSM_DIR / f"{country_code}_{layer_name}.parquet"
    gdf.to_parquet(out_path)
    return out_path