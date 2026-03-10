# Ruimtelijke Simulatie

Lokale simulatie-engine en interactieve viewer voor de H3 datacube van Nederland.

Ontdek ruimtelijke patronen, ontwikkeltrajecten en scenario's — volledig offline op je eigen machine.

## Wat het doet

- **Patroonherkenning** — Self-Organizing Maps clusteren 225k hexagons op basis van alle variabelen
- **Trajecten** — zie hoe een wijk of gebied zich ontwikkelt door de tijd (2018–2023)
- **Scenario's** — verander één variabele en zie het ruimtelijke effect
- **Lokale AI** — Ollama reasoning over patronen en afwijkingen, geen externe API

## Stack

- **Backend**: FastAPI + Python + minisom + DuckDB
- **LLM**: Ollama (volledig lokaal)
- **Visualisatie**: deck.gl H3HexagonLayer + MapLibre
- **Frontend**: Vue 3 + TypeScript

## Snel starten

```bash
# Backend
cd src/backend && uv sync
uv run uvicorn app.main:app --reload --port 8002

# Frontend
cd src/frontend && npm ci && npm run dev
```

## Data

Gebruikt dezelfde H3 datacube als de ruimtelijke assistent:
225.684 hexagons, H3 resolutie 7 (~250m), 2018–2023, bronnen CBS + LGN.
