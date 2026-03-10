from fastapi import APIRouter, Request
from pydantic import BaseModel
from app.services.ollama_service import describe_cluster, explain_trajectory, explain_scenario, explain_trend
from app.services.som_service import SOM_COLUMNS

router = APIRouter()


@router.get("/cluster/{cluster_id}")
async def cluster_insight(cluster_id: int, request: Request):
    """Get Ollama description of what a SOM cluster represents."""
    som = request.app.state.som
    df = request.app.state.df

    # Get hexagons in this cluster
    clusters = som.get_cluster_map()
    hex_ids = [c["h3"] for c in clusters if c["cluster_id"] == cluster_id]

    if not hex_ids:
        return {"cluster_id": cluster_id, "insight": "Geen hexagons gevonden in dit cluster."}

    # Compute mean values for available SOM columns
    df_2023 = df[df["year_int"] == 2023]
    df_cluster = df_2023[df_2023["h3_id"].isin(hex_ids)]
    available = [c for c in SOM_COLUMNS if c in df_cluster.columns]
    stats = df_cluster[available].mean().to_dict()

    insight = await describe_cluster(cluster_id, stats)
    return {
        "cluster_id": cluster_id,
        "hex_count": len(hex_ids),
        "insight": insight,
        "stats": {k: round(v, 1) for k, v in stats.items()},
    }


class TrajectoryInsightRequest(BaseModel):
    h3_id: str


@router.post("/trajectory")
async def trajectory_insight(body: TrajectoryInsightRequest, request: Request):
    """Get Ollama explanation of a hexagon's development trajectory."""
    trajectory = request.app.state.som.get_trajectory(body.h3_id)
    if not trajectory:
        return {"h3_id": body.h3_id, "insight": "Geen data gevonden voor dit gebied."}

    insight = await explain_trajectory(body.h3_id, trajectory)
    return {
        "h3_id": body.h3_id,
        "trajectory": trajectory,
        "insight": insight,
    }


class ScenarioInsightRequest(BaseModel):
    column: str
    change_factor: float
    original_clusters: list[dict]
    new_clusters: list[dict]


class TrendInsightRequest(BaseModel):
    target_year: int
    original_clusters: list[dict]
    new_clusters: list[dict]


@router.post("/trend")
async def trend_insight(body: TrendInsightRequest):
    """Get Ollama explanation of what the trend projection means for policy."""
    orig_map = {c["h3"]: c["cluster_id"] for c in body.original_clusters}
    shifted = sum(
        1 for c in body.new_clusters
        if orig_map.get(c["h3"]) != c["cluster_id"]
    )
    insight = await explain_trend(body.target_year, shifted, len(body.new_clusters))
    return {"insight": insight, "shifted_count": shifted}


@router.post("/scenario")
async def scenario_insight(body: ScenarioInsightRequest):
    """Get Ollama explanation of what a scenario simulation means for policy."""
    # Count how many hexagons shifted clusters
    orig_map = {c["h3"]: c["cluster_id"] for c in body.original_clusters}
    shifted = sum(
        1 for c in body.new_clusters
        if orig_map.get(c["h3"]) != c["cluster_id"]
    )

    insight = await explain_scenario(
        body.column, body.change_factor, shifted, len(body.new_clusters)
    )
    return {"insight": insight, "shifted_count": shifted}
