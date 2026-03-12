"""
Tool definitions and executors for the spatial agent.
Each tool wraps existing services and is callable by the LLM orchestrator.
"""
import json
import duckdb
import pandas as pd
import numpy as np

from app.services.som_service import SOM_COLUMNS


# Tool schemas for Ollama function calling
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "query_data",
            "description": (
                "Voer een SQL-query uit op de H3 hexagon dataset van Nederland. "
                "De tabel heet 'df' en bevat kolommen: h3_id, year_int (2018-2023), "
                "gemeentenaam, wijknaam, buurtnaam, en ~100 ruimtelijke variabelen "
                "(demografie, wonen, landgebruik, milieu). "
                "Gebruik year_int voor jaarselectie, NOOIT 'year' of 'year_label'. "
                "Beperk resultaten met LIMIT."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "Geldige DuckDB SQL query met 'df' als tabelnaam.",
                    }
                },
                "required": ["sql"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_cluster_stats",
            "description": (
                "Haal gemiddelde waarden op voor alle hexagonen in een SOM-cluster (2023). "
                "Geeft inzicht in het karakter van een gebiedstype."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "cluster_id": {
                        "type": "integer",
                        "description": "Cluster ID (0-224 voor een 15x15 SOM).",
                    }
                },
                "required": ["cluster_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_hexagons",
            "description": (
                "Zoek hexagonen op basis van een kolom en drempelwaarde. "
                "Handig voor vragen als: 'welke gebieden hebben hoge hittestress?' "
                "of 'waar is de WOZ-waarde het hoogst?'"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "column": {
                        "type": "string",
                        "description": "Kolomnaam uit de dataset.",
                    },
                    "min_value": {
                        "type": "number",
                        "description": "Minimumwaarde (optioneel, gebruik 0 als niet van toepassing).",
                    },
                    "max_value": {
                        "type": "number",
                        "description": "Maximumwaarde (optioneel, gebruik 9999 als niet van toepassing).",
                    },
                    "year": {
                        "type": "integer",
                        "description": "Jaar (2018-2023), standaard 2023.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max aantal resultaten, standaard 20.",
                    },
                },
                "required": ["column", "min_value", "max_value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_trajectory",
            "description": (
                "Haal de SOM-clustertrajectory op van een specifiek hexagon over 2018-2023. "
                "Laat zien hoe een gebied zich ontwikkeld heeft."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "h3_id": {
                        "type": "string",
                        "description": "H3 hexagon ID (15 tekens).",
                    }
                },
                "required": ["h3_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_areas",
            "description": (
                "Vergelijk twee gemeenten of regio's op gemiddelde waarden van een variabele. "
                "Handig voor benchmarking en beleidsvergelijking."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "gemeente_a": {
                        "type": "string",
                        "description": "Naam van gemeente A.",
                    },
                    "gemeente_b": {
                        "type": "string",
                        "description": "Naam van gemeente B.",
                    },
                    "column": {
                        "type": "string",
                        "description": "Variabele om te vergelijken.",
                    },
                    "year": {
                        "type": "integer",
                        "description": "Jaar (2018-2023), standaard 2023.",
                    },
                },
                "required": ["gemeente_a", "gemeente_b", "column"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "highlight_hexagons",
            "description": (
                "Markeer specifieke hexagonen op de kaart met een label. "
                "Gebruik dit om gebieden visueel aan te wijzen na een analyse."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "h3_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Lijst van H3 hexagon IDs om te markeren (max 500).",
                    },
                    "label": {
                        "type": "string",
                        "description": "Omschrijving van de gemarkeerde gebieden.",
                    },
                },
                "required": ["h3_ids", "label"],
            },
        },
    },
]


def execute_tool(name: str, args: dict, df: pd.DataFrame, som) -> str:
    """Execute a tool call and return the result as a string."""
    try:
        if name == "highlight_hexagons":
            h3_ids = args.get("h3_ids", [])[:500]
            label = args.get("label", "")
            return "__HIGHLIGHT__:" + json.dumps({"h3_ids": h3_ids, "label": label})
        elif name == "query_data":
            return _query_data(args["sql"], df)
        elif name == "get_cluster_stats":
            return _get_cluster_stats(int(args["cluster_id"]), df, som)
        elif name == "find_hexagons":
            return _find_hexagons(args, df)
        elif name == "get_trajectory":
            return _get_trajectory(args["h3_id"], som)
        elif name == "compare_areas":
            return _compare_areas(args, df)
        else:
            return f"Onbekende tool: {name}"
    except Exception as e:
        return f"Fout bij uitvoeren van {name}: {str(e)}"


def _query_data(sql: str, df: pd.DataFrame) -> str:
    con = duckdb.connect()
    con.register("df", df)
    result = con.execute(sql).df()
    con.close()
    if len(result) == 0:
        return "Geen resultaten gevonden."
    # Limit output size
    if len(result) > 50:
        result = result.head(50)
        suffix = f"\n(Resultaten afgekapt tot 50 rijen)"
    else:
        suffix = ""
    return result.to_string(index=False, max_rows=50) + suffix


def _get_cluster_stats(cluster_id: int, df: pd.DataFrame, som) -> str:
    clusters = som.get_cluster_map()
    hex_ids = [c["h3"] for c in clusters if c["cluster_id"] == cluster_id]
    if not hex_ids:
        return f"Cluster {cluster_id} niet gevonden."

    df_2023 = df[df["year_int"] == 2023]
    df_cluster = df_2023[df_2023["h3_id"].isin(hex_ids)]
    available = [c for c in SOM_COLUMNS if c in df_cluster.columns]
    stats = df_cluster[available].mean().dropna()
    # Only show columns with meaningful values
    stats = stats[stats > 0.5].sort_values(ascending=False).head(15)

    lines = [f"Cluster {cluster_id} — {len(hex_ids)} hexagonen"]
    for col, val in stats.items():
        lines.append(f"  {col}: {round(float(val), 1)}")
    return "\n".join(lines)


def _find_hexagons(args: dict, df: pd.DataFrame) -> str:
    col = args["column"]
    min_val = float(args.get("min_value", 0))
    max_val = float(args.get("max_value", 9999))
    year = int(args.get("year", 2023))
    limit = int(args.get("limit", 20))

    if col not in df.columns:
        return f"Kolom '{col}' niet gevonden. Beschikbare kolommen: {', '.join(SOM_COLUMNS[:10])}..."

    df_year = df[df["year_int"] == year]
    mask = (df_year[col] >= min_val) & (df_year[col] <= max_val)
    result = df_year[mask][["h3_id", "gemeentenaam", "wijknaam", col]].sort_values(col, ascending=False).head(limit)

    if len(result) == 0:
        return f"Geen hexagonen gevonden met {col} tussen {min_val} en {max_val}."
    return result.to_string(index=False)


def _get_trajectory(h3_id: str, som) -> str:
    trajectory = som.get_trajectory(h3_id)
    if not trajectory:
        return f"Geen data gevonden voor {h3_id}."
    lines = [f"Trajectory voor {h3_id[:8]}...:"]
    for t in trajectory:
        lines.append(f"  {t['year']}: cluster {t['cluster_id']} (positie {t['cluster_x']},{t['cluster_y']})")
    return "\n".join(lines)


def _compare_areas(args: dict, df: pd.DataFrame) -> str:
    col = args["column"]
    year = int(args.get("year", 2023))
    df_year = df[df["year_int"] == year]

    results = []
    for gemeente in [args["gemeente_a"], args["gemeente_b"]]:
        subset = df_year[df_year["gemeentenaam"].str.lower() == gemeente.lower()]
        if len(subset) == 0:
            results.append(f"{gemeente}: niet gevonden")
        elif col not in subset.columns:
            results.append(f"{gemeente}: kolom '{col}' niet beschikbaar")
        else:
            val = subset[col].mean()
            results.append(f"{gemeente}: gemiddeld {round(float(val), 2)} ({len(subset)} hexagonen)")

    return f"Vergelijking '{col}' in {year}:\n" + "\n".join(results)
