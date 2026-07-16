# Temelli Data Center Project Finance Model

A production-oriented web application and independent Python calculation engine for the Temelli Data Center project finance model. The repository intentionally contains no Excel macro, VBA, Goal Seek, copy-paste circularity, or workbook runtime dependency.

## Architecture

- `apps/api`: FastAPI service exposing scenarios, calculations, sensitivities, exports, and trace metadata.
- `apps/web`: Next.js/React/TypeScript front end with a single centralized Inputs page, Executive Summary, calculation schedules, checks, scenarios, and sensitivity views.
- `packages/temelli-finance`: Python project finance engine. It owns all formulas, circularity, debt sculpting, statements, ratios, checks, and export data structures.
- `docs`: workbook inspection notes, workbook-to-web mapping, formula methodology, and deployment guidance.

The latest Excel workbook was not present in this repository at implementation time. The model therefore seeds the latest known Temelli base case from the prompt and documents every assumed placeholder in `docs/workbook_mapping.md`. If a workbook is later added, the mapping file identifies the reconciliation path.

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e packages/temelli-finance -r apps/api/requirements.txt
pytest
uvicorn apps.api.main:app --reload --port 8000
cd apps/web && npm install && npm run dev
```

Docker:

```bash
docker compose up --build
```

## Calculation method

The engine runs monthly calculations over a common timeline and then aggregates to quarterly or annual display periods. Inputs are typed Python schema objects and all assumptions are supplied by `TemelliModelInput`; calculation modules do not use hidden constants. The core sequence is:

1. Validate dates, percentages, capex curves, financing tenors, and phase capacity.
2. Build monthly timeline and phase status flags.
3. Calculate construction, capex, occupancy, revenue, energy, opex, working capital, depreciation, and tax.
4. Solve circular financing relationships with damped fixed-point iteration.
5. Size and schedule debt tranches, including equal-principal, annuity, bullet, balloon, cash sweep, and DSCR-sculpted repayment.
6. Apply the configurable cash waterfall, liquidity facilities, DSRA, cash trap, and distributions.
7. Generate P&L, balance sheet, cash flow statement, returns, ratios, and model checks.

Circularity convergence is controlled by editable tolerance, maximum iterations, and damping factor. The solver reports status, iteration count, largest residual, residual schedule, and diagnostics. Debt sizing uses bounded bisection for sculpted tranches and never performs manual copy-paste style iteration.

## Seeded base case

- Project: Temelli Data Center, Ankara, Türkiye.
- Phase 1: 24 MW, COD December 2028, approximately USD 456.13m total Phase 1 project cost.
- Wider campus: 24 MW + 24 MW + 36 MW, total potential 84 MW.
- Initial target gearing: 70:30, senior debt approximately USD 319m, equity approximately USD 137m.
- PUE: 1.30, carrier-neutral colocation, customer-agnostic commercial model, renewable/PPA capability, Tier III+ availability positioning.

Run the seed through the API:

```bash
curl http://localhost:8000/api/scenarios/base/calculate
```

## Exports

The API provides JSON snapshots, CSV schedules, XLSX-style sheet payloads without macros, annual financial statements, scenario comparison payloads, model checks, and executive-summary PDF-ready JSON.

## Production deployment

Set `DATABASE_URL` to PostgreSQL for production. If omitted, the API uses a local SQLite database. Use `docker-compose.yml` as the deployment baseline and configure secrets via environment variables.
