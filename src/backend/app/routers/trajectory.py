from fastapi import APIRouter, Request, HTTPException

router = APIRouter()


@router.get("/{h3_id}")
async def get_trajectory(h3_id: str, request: Request):
    """Return the development trajectory of a single hexagon through time."""
    trajectory = request.app.state.som.get_trajectory(h3_id)
    if not trajectory:
        raise HTTPException(status_code=404, detail="Hexagon not found")
    return {"h3_id": h3_id, "trajectory": trajectory}
