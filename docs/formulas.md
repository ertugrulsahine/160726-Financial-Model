# Formula and audit notes

Every calculated result includes or can reference trace metadata. Key formulas:

- Revenue = occupied MW × 1,000 × monthly USD/kW/month tariff + other recurring revenue + optional power pass-through, less bad debt.
- Energy MWh = occupied MW × 1,000 × 24 × days in month × PUE ÷ 1,000.
- EBITDA = revenue - operating costs - power costs.
- Interest = (opening debt + 50% of current-period drawdown) × annual interest rate ÷ 12.
- Sculpted principal = max(CFADS / target DSCR - interest, 0), capped at outstanding balance.
- DSCR = CFADS / cash debt service.
- LLCR = discounted CFADS / peak debt balance.
- PLCR = discounted CFADS / total project cost.

Circularity is solved by fixed-point iteration with configurable damping, tolerance, and maximum iterations. The final response exposes convergence status, iteration diagnostics, largest residual, and residual schedule.
