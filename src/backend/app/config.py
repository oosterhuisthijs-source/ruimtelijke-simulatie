from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    delta_table_path: str = "data/volledige_tijdreeks_delta"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"
    allowed_origins: list[str] = ["http://localhost:5173"]
    som_grid_x: int = 10
    som_grid_y: int = 10
    som_iterations: int = 1000
    debug: bool = True

    class Config:
        env_file = ".env"


settings = Settings()
