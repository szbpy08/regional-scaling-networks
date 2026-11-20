"""NUTS3 gráf építése scikit-mobility gravity-modell kimenetéből (networkx)."""
import networkx as nx
import pandas as pd


def build_nuts3_graph(
    nodes_df: pd.DataFrame,
    flow_df: pd.DataFrame,
    id_col: str = "nuts3_id",
    origin_col: str = "origin",
    destination_col: str = "destination",
    flow_col: str = "flow",
    node_attr_cols: list[str] | None = None,
) -> nx.Graph:
    """
    NUTS3 node-okkal és gravity-súlyozott élekkel rendelkező gráfot épít
    a scikit-mobility (skmob) Gravity-modelljének kimenetéből.

    nodes_df: régiónkénti attribútumokat tartalmazó DataFrame, id_col oszloppal.

    flow_df: hosszú (long) formátumú tábla origin-destination párokkal és
    flow-értékkel — pl. egy skmob.models.gravity.Gravity(...).generate(...)
    hívás FlowDataFrame kimenete, DataFrame-ként átalakítva
    (pd.DataFrame(flow_fdf)). Oszlopnevek a paraméterekkel testre szabhatók,
    mert az skmob verziótól függően eltérhetnek ("origin"/"destination"/"flow").

    node_attr_cols: mely nodes_df oszlopok kerüljenek a gráf node-jaira
    attribútumként (pl. ["population", "gdp_total"]). Ha None, nincs
    node-attribútum.

    Visszaadja: súlyozott, irányítatlan networkx.Graph objektumot.
    Él-attribútum: "weight" (a flow-érték). Ha origin-destination és
    destination-origin is szerepel a flow_df-ben (mindkét irányú flow),
    az élsúly a kettő összege lesz (irányítatlan gráfhoz aggregálva).
    """
    for col in (origin_col, destination_col, flow_col):
        if col not in flow_df.columns:
            raise ValueError(f"Hiányzó oszlop a flow_df-ben: '{col}'")
    if id_col not in nodes_df.columns:
        raise ValueError(f"Hiányzó '{id_col}' oszlop a nodes_df-ben.")

    G = nx.Graph()

    for _, row in nodes_df.iterrows():
        attrs = {}
        if node_attr_cols:
            for col in node_attr_cols:
                if col not in nodes_df.columns:
                    raise ValueError(f"Hiányzó node_attr_col: '{col}'")
                attrs[col] = row[col]
        G.add_node(row[id_col], **attrs)

    for _, row in flow_df.iterrows():
        u, v, w = row[origin_col], row[destination_col], row[flow_col]
        if u == v or w <= 0:
            continue  # önhurok-élek és nulla/negatív flow kimarad
        if G.has_edge(u, v):
            G[u][v]["weight"] += float(w)  # mindkét irányú flow összeadódik
        else:
            G.add_edge(u, v, weight=float(w))

    return G