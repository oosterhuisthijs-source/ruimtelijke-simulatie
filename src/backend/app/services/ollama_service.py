import ollama
from app.config import settings


SYSTEM_PROMPT = """Je bent een ruimtelijke data-analist voor Nederland.
Je analyseert H3 hexagon data over demografie, wonen, natuur en leefkwaliteit.
Geef korte, concrete inzichten in het Nederlands.
Vermijd jargon. Focus op wat beleidsmakers kunnen doen met deze informatie."""


async def describe_cluster(cluster_id: int, cluster_stats: dict) -> str:
    """Ask Ollama to describe what a SOM cluster represents."""
    stats_text = "\n".join(
        f"- {k}: {round(v, 1)}" for k, v in cluster_stats.items()
    )

    response = ollama.chat(
        model=settings.ollama_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Beschrijf dit type gebied op basis van de gemiddelde waarden (0-255 schaal, "
                    f"hoger = meer/groter):\n\n{stats_text}\n\n"
                    f"Geef een naam voor dit gebiedstype (max 5 woorden) en 2 zinnen uitleg."
                ),
            },
        ],
    )
    return response["message"]["content"]


async def explain_trajectory(h3_id: str, trajectory: list[dict]) -> str:
    """Ask Ollama to explain how a hexagon developed over time."""
    steps = "\n".join(
        f"- {t['year']}: cluster {t['cluster_id']} (positie {t['cluster_x']},{t['cluster_y']})"
        for t in trajectory
    )

    response = ollama.chat(
        model=settings.ollama_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Dit gebied (H3: {h3_id[:8]}...) bewoog door de volgende SOM-clusters van 2018-2023:\n\n"
                    f"{steps}\n\n"
                    f"Wat vertelt dit traject over de ontwikkeling van dit gebied? "
                    f"Is het stabiel, verbeterd, of verslechterd? Geef 2-3 zinnen."
                ),
            },
        ],
    )
    return response["message"]["content"]


async def explain_trend(target_year: int, shifted_count: int, total: int) -> str:
    """Ask Ollama to explain what the trend projection means for spatial policy."""
    shifted_pct = round(shifted_count / total * 100)

    response = ollama.chat(
        model=settings.ollama_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Trendscenario: alle ruimtelijke variabelen zijn doorgetrokken op basis van "
                    f"de historische trend 2018-2023, geprojecteerd naar {target_year}.\n\n"
                    f"Resultaat: {shifted_count} van de {total} gebieden ({shifted_pct}%) "
                    f"verschuiven naar een ander gebiedstype als de huidige trends doorzetten.\n\n"
                    f"Wat zegt dit over de ruimtelijke ontwikkeling van Nederland richting {target_year}? "
                    f"Welke typen gebieden zijn het meest in beweging? Geef 2-3 concrete beleidsrelevante zinnen."
                ),
            },
        ],
    )
    return response["message"]["content"]


async def explain_scenario(column: str, change_factor: float, shifted_count: int, total: int) -> str:
    """Ask Ollama to explain what a scenario simulation means for policy."""
    direction = "stijgt" if change_factor > 1 else "daalt"
    pct = abs(round((change_factor - 1) * 100))
    shifted_pct = round(shifted_count / total * 100)

    response = ollama.chat(
        model=settings.ollama_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Scenario: '{column}' {direction} met {pct}% in alle gebieden.\n"
                    f"Resultaat: {shifted_count} van de {total} gebieden ({shifted_pct}%) "
                    f"verschuiven naar een ander gebiedstype.\n\n"
                    f"Wat betekent dit voor beleid? Geef 2-3 concrete zinnen."
                ),
            },
        ],
    )
    return response["message"]["content"]
