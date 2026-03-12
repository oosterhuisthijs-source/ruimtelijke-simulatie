
# CLAUDE.md

This file provides guidance to Claude Code when working in this repository.

## ExoBrain context

For vision, values and project context, read:
`/home/thijsradijs/Documents/exobrain-vault/exobrain-index.md`

Key notes:
`/home/thijsradijs/Documents/exobrain-vault/notes/professional/project-ruimtelijke-assistent.md`
`/home/thijsradijs/Documents/exobrain-vault/notes/professional/geo-datacube-visie.md`

## What this is

A local spatial simulation engine and interactive viewer for the H3 datacube of the Netherlands.

Goal: discover spatial patterns and development trajectories using Self-Organizing Maps (SOM),
and visualize predictions and scenarios in an interactive deck.gl map.

Runs fully locally on Fedora desktop using Ollama for LLM reasoning.

## Architecture

### Backend (FastAPI + Python)
- SOM training on the H3 datacube time series (2018–2023)
- Trajectory analysis per hexagon
- Scenario simulation (change one variable, see spatial effect)
- Ollama integration for natural language reasoning about patterns
- Data: Delta table from ruimtelijke-assistent (symlinked or copied)

### Frontend (Vue 3 + deck.gl)
- Interactive H3 hexagon map (deck.gl H3HexagonLayer)
- SOM cluster visualization
- Trajectory viewer (how a hexagon moved through time)
- Scenario controls (sliders, variable selection)
- Pattern explorer (find similar hexagons)

## Stack

| Layer | Tool |
|-------|------|
| Backend | FastAPI + Python |
| SOM | minisom or somoclu |
| Data | DuckDB + Delta table (from ruimtelijke-assistent) |
| LLM | Ollama (local, Fedora desktop) |
| Visualization | deck.gl H3HexagonLayer + MapLibre |
| Frontend | Vue 3 + TypeScript + Vite |

## Data

Symlink or copy from ruimtelijke-assistent:
`src/backend/data/` → points to Delta table + LLM metadata

225,684 H3 hexagons, resolution 7 (~250m), 2018–2023.

See dataset note in exobrain for column details and data quality warnings.

## Key principles

- Runs fully offline — no Azure, no external APIs
- Ollama for local LLM (llama3, mistral, or similar)
- Reproducible: same data → same SOM → same trajectories
- Transparent: show users what the model does and why
- Modular: SOM, trajectories, and scenarios are separate concerns

## Development commands

```bash
# Backend
cd src/backend
uv sync
uv run uvicorn app.main:app --reload --port 8002

# Frontend
cd src/frontend
npm ci
npm run dev
```

## Conventions

- Python: use `uv` for package management
- Frontend: Vue 3 composition API, TypeScript, composables for logic
- All user-facing text in Dutch
- H3 column in data is `h3_id`, queries return it as `h3`
- Use `year_int` not `year` or `year_label` (corrupt columns)
- Normalized columns (0-255): only compare within same year
