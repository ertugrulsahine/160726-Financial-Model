# Generic Infrastructure Project Finance Model

A production-oriented demonstration web application and independent Python calculation engine for project-finance modelling. All names, dates, capacities and financial assumptions in this public repository are synthetic examples and are not intended to represent any real project, client, employer or transaction.

## Architecture

- `apps/api`: FastAPI service exposing scenarios, calculations, sensitivities and exports.
- `apps/web`: React/TypeScript front end for inputs, summary views, schedules and checks.
- `packages/project-finance`: Python project-finance engine containing formulas, debt schedules, statements, ratios and model checks.
- `docs`: generic methodology and model-mapping notes.

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e packages/project-finance -r apps/api/requirements.txt
pytest
uvicorn apps.api.main:app --reload --port 8000
```

Docker:

```bash
docker compose up --build
```

## Calculation method

The engine runs monthly calculations over a common timeline and aggregates results for presentation. It models construction, CAPEX, occupancy, revenue, energy, OPEX, tax, debt sizing, debt service, liquidity, distributions and project/equity returns. Circular financing relationships are solved iteratively with configurable convergence settings.

## Synthetic example case

The included base case is deliberately fictional. It uses rounded illustrative assumptions for a generic infrastructure/data-center style project. No figures should be interpreted as confidential, current or historical information about any real asset or company.

## Exports

The API provides JSON and CSV outputs suitable for testing and demonstration.
