"""Térbeli illesztés és aggregáció NUTS3 régiókhoz."""
import geopandas as gpd
import pandas as pd


def aggregate_to_nuts3(
    layer_gdf: gpd.GeoDataFrame,
    nuts3_gdf: gpd.GeoDataFrame,
    agg_spec: dict,
) -> pd.DataFrame:
    """
    Egy OSM-réteget (network_driving, network_walking, buildings, pois)
    NUTS3 poligonokhoz illeszt térbeli overlay-jel, majd nuts3_id szerint
    aggregál az agg_spec alapján.

    nuts3_gdf: legalább 'nuts3_id' és 'geometry' oszlopot tartalmazó GeoDataFrame
    (a GISCO NUTS3 geojsonból, LEVL_3-ra szűrve).

    agg_spec: az aggregáció leírása, pl.:
      {"length_km": {"method": "sum_length_km"}}                      # útvonalakhoz
      {"building_count": {"method": "count"},
       "building_footprint_sqm": {"method": "sum_area_sqm"}}          # épületekhez
      {"poi_count": {"method": "count"}}                              # POI-khoz
      {"poi_count_by_category": {"method": "count", "groupby": "amenity"}}  # kategóriánként

    Visszaadja: nuts3_id-nkénti aggregált mértékeket tartalmazó DataFrame-et
    (nincs benne geometry — az később a master table-nél kerül vissza a
    nuts3_gdf-ből).
    """
    if "nuts3_id" not in nuts3_gdf.columns:
        raise ValueError("A nuts3_gdf-nek tartalmaznia kell egy 'nuts3_id' oszlopot.")

    if layer_gdf.crs != nuts3_gdf.crs:
        layer_gdf = layer_gdf.to_crs(nuts3_gdf.crs)

    # A metrikus (terület/hossz) számításokhoz projektált (nem fokalapú) CRS kell.
    # Ha a bemenet EPSG:4326 (fokalapú), UTM-be vetítjük a pontos km/m2-ekhez.
    if nuts3_gdf.crs is not None and nuts3_gdf.crs.is_geographic:
        metric_crs = nuts3_gdf.estimate_utm_crs()
        layer_metric = layer_gdf.to_crs(metric_crs)
        nuts3_metric = nuts3_gdf.to_crs(metric_crs)
    else:
        layer_metric = layer_gdf
        nuts3_metric = nuts3_gdf

    joined = gpd.overlay(
        layer_metric[["geometry"] + [c for c in layer_metric.columns if c != "geometry"]],
        nuts3_metric[["nuts3_id", "geometry"]],
        how="intersection",
    )

    results = []
    for out_col, spec in agg_spec.items():
        method = spec["method"]
        groupby_col = spec.get("groupby")

        if method == "sum_length_km":
            joined["_length_km"] = joined.geometry.length / 1000.0
            grouped = joined.groupby("nuts3_id")["_length_km"].sum()
            results.append(grouped.rename(out_col))

        elif method == "sum_area_sqm":
            joined["_area_sqm"] = joined.geometry.area
            grouped = joined.groupby("nuts3_id")["_area_sqm"].sum()
            results.append(grouped.rename(out_col))

        elif method == "count":
            if groupby_col:
                if groupby_col not in joined.columns:
                    raise ValueError(f"Hiányzó groupby oszlop: '{groupby_col}'")
                grouped = joined.groupby(["nuts3_id", groupby_col]).size()
                wide = grouped.unstack(fill_value=0)
                wide.columns = [f"{out_col}_{c}" for c in wide.columns]
                results.append(wide)
            else:
                grouped = joined.groupby("nuts3_id").size()
                results.append(grouped.rename(out_col))

        else:
            raise ValueError(f"Ismeretlen aggregációs method: '{method}'")

    combined = pd.concat(results, axis=1).reset_index()

    # Régiók, ahol a rétegnek nincs metszete (pl. nincs POI), 0-t kapjanak NaN helyett
    numeric_cols = combined.columns.difference(["nuts3_id"])
    combined[numeric_cols] = combined[numeric_cols].fillna(0)

    return combined