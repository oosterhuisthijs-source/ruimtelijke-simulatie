from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.services.dataset import load_dataset
from app.services.som_service import SOMService


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load dataset and train SOM on startup
    app.state.df = await load_dataset(settings.delta_table_path)
    app.state.som = SOMService(app.state.df)
    await app.state.som.train()
    yield


app = FastAPI(title="Ruimtelijke Simulatie", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routers import som, scenario, trajectory, health, insight, trend  # noqa: E402

app.include_router(health.router)
app.include_router(som.router, prefix="/api/som")
app.include_router(trajectory.router, prefix="/api/trajectory")
app.include_router(scenario.router, prefix="/api/scenario")
app.include_router(insight.router, prefix="/api/insight")
app.include_router(trend.router, prefix="/api/trend")
