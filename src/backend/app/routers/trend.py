from fastapi import APIRouter, Request
from pydantic import BaseModel, field_validator

router = APIRouter()


class TrendRequest(BaseModel):
    target_year: int = 2030

    @field_validator("target_year")
    @classmethod
    def valid_year(cls, v: int) -> int:
        if not (2024 <= v <= 2040):
            raise ValueError("target_year moet tussen 2024 en 2040 liggen")
        return v


@router.post("/simulate")
async def simulate_trend(body: TrendRequest, request: Request):
    """Project all variables forward using 2018-2023 linear trend, re-classify with SOM."""
    som = request.app.state.som
    features_norm, h3_ids = som.project_trend(body.target_year)

    results = []
    for i, vec in enumerate(features_norm):
        x, y = som.som.winner(vec)
        results.append({
            "h3": h3_ids[i],
            "cluster_id": int(x * som.som._weights.shape[1] + y),
            "cluster_x": int(x),
            "cluster_y": int(y),
        })

    return {"target_year": body.target_year, "results": results}
