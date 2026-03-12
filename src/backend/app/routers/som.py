from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/clusters")
async def get_clusters(request: Request, year: int = 2023):
    """Return SOM cluster assignment for all hexagons, optionally for a specific year."""
    if year == 2023:
        return request.app.state.som.get_cluster_map()
    return request.app.state.som.get_cluster_map_for_year(year)


@router.get("/grid")
async def get_grid(request: Request):
    """Return SOM grid size and cluster metadata."""
    from app.config import settings
    return {
        "grid_x": settings.som_grid_x,
        "grid_y": settings.som_grid_y,
        "total_clusters": settings.som_grid_x * settings.som_grid_y,
        "trained": request.app.state.som.trained,
    }
