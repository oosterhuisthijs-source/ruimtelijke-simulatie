from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter()


class ScenarioRequest(BaseModel):
    column: str
    change_factor: float  # e.g. 1.2 = +20%, 0.8 = -20%
    year: int = 2023


@router.post("/simulate")
async def simulate_scenario(body: ScenarioRequest, request: Request):
    """
    Simulate what happens to SOM clusters if one variable changes.
    Returns cluster assignments with modified data.
    """
    som = request.app.state.som
    df = request.app.state.df

    from app.services.som_service import SOM_COLUMNS
    import numpy as np

    df_year = df[df["year_int"] == body.year].copy()
    available = [c for c in SOM_COLUMNS if c in df_year.columns]

    if body.column not in available:
        return {"error": f"Column {body.column} not available for simulation"}

    # Apply change to selected column
    df_year[body.column] = (df_year[body.column] * body.change_factor).clip(0, 255)

    features = df_year[available].fillna(0).values.astype(float)
    col_max = som.feature_matrix.max(axis=0)
    col_max[col_max == 0] = 1
    features_norm = features / col_max

    results = []
    for i, vec in enumerate(features_norm):
        x, y = som.som.winner(vec)
        results.append({
            "h3": df_year["h3_id"].iloc[i],
            "cluster_id": int(x * som.som._weights.shape[1] + y),
            "cluster_x": int(x),
            "cluster_y": int(y),
        })

    return {
        "column": body.column,
        "change_factor": body.change_factor,
        "results": results,
    }
