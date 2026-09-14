# Generic workbook-to-web mapping

This public repository is a synthetic demonstration. No client workbook or real project workbook is included. The web model maps common institutional project-finance workbook areas to generic engine modules.

| Workbook area | Web module | Calculation approach | Status |
|---|---|---|---|
| Inputs / assumptions | `schemas.py` and Inputs page | Typed editable schema rendered on centralized Inputs page | Synthetic example |
| Timeline | `engine.months` | Monthly dates with aggregation support | Implemented |
| Construction / CAPEX | engine phase logic | Phase-specific construction curves and capex spend | Implemented |
| Revenue | `calculate_model` revenue block | Capacity × pricing assumptions plus recurring revenue | Implemented |
| Energy / PUE | `calculate_model` energy block | Occupied load × hours × PUE × electricity price | Implemented |
| Debt | `_debt_schedule` | Drawdown, interest, principal, DSRA and repayment method | Implemented |
| Circularity | `calculate_model` iteration loop | Damped fixed-point solver with diagnostics | Implemented |
| Financial statements | `calculate_model` statement block | Linked project-finance calculations | Implemented |
| Checks | `calculate_model` checks block | Structured pass/error checks | Implemented |
