# Temelli workbook-to-web mapping

No Excel workbook file was present in the repository during implementation. The web model therefore maps institutional project-finance workbook areas to engine modules and preserves reconciliation placeholders for a future workbook import.

| Excel area | Web module | Calculation approach | Status |
|---|---|---|---|
| Inputs / assumptions sheets | `schemas.py` and Inputs page | Typed editable Pydantic schema rendered on centralized Inputs page | Implemented from supplied base-case assumptions |
| Timeline | `engine.months` | Real monthly dates with annual/quarterly aggregation support | Implemented |
| Construction / CAPEX | `_active_phase_frame` | Phase-specific construction curves and capex spend | Implemented |
| Revenue | `calculate_model` revenue block | Occupied MW × kW/MW × monthly price, other recurring revenue, power pass-through and bad debt | Implemented |
| Energy / PUE | `calculate_model` energy block | Occupied IT load × hours × PUE × electricity price | Implemented |
| Debt | `_debt_schedule` | Tranche-level drawdown, interest, principal, DSRA, repayment method | Implemented |
| Circularity macro | `calculate_model` iteration loop | Damped fixed-point solver with diagnostics | Replaced; no VBA |
| Financial statements | `calculate_model` statement block | Linked P&L, balance sheet and cash flow calculations | Implemented |
| Checks | `calculate_model` checks block | Structured pass/error model checks | Implemented |
