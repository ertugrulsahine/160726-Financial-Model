from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import date
from copy import deepcopy

@dataclass
class Settings:
    project_name: str="Example Infrastructure Project"; location: str="Türkiye"; scenario_name: str="Base Case"
    model_start: date=date(2026,1,1); model_end: date=date(2050,12,31); reporting_currency: str="USD"; display_frequency: str="annual"
    days_per_year: int=365; tolerance: float=1e-6; max_iterations: int=100; damping_factor: float=0.65; minimum_cash_balance: float=1_000_000; dividend_frequency_months: int=6
@dataclass
class PhaseInput:
    name: str; it_capacity_mw: float; construction_start: date; construction_months: int; commissioning_months: int; cod: date; stabilization_months: int; capex_total: float
    enabled: bool=True; operating_life_years: int=30; contracted_at_cod_pct: float=0.20; stabilized_occupancy_pct: float=0.85; ai_ready_capacity_pct: float=0.40; rack_density_kw: float=10
@dataclass
class CapexInput:
    contingency_pct: float=0.08; recoverable_vat_pct: float=0.0; non_recoverable_vat_pct: float=0.0; spend_curve: list[float]=field(default_factory=lambda:[0.20,0.35,0.30,0.15])
@dataclass
class RevenueInput:
    colocation_price_per_kw_month: float=140.0; price_escalation: float=0.025; power_pass_through: bool=True; power_markup_pct: float=0.04; other_recurring_revenue_per_kw_month: float=6.0; bad_debt_pct: float=0.003; collection_days: int=45
@dataclass
class OperationsInput:
    pue: float=1.35; electricity_price_per_mwh: float=90.0; renewable_share: float=0.50; opex_per_occupied_mw_year: float=1_300_000; fixed_opex_per_mw_year: float=200_000; cost_escalation: float=0.025
@dataclass
class TaxInput:
    corporate_tax_rate: float=0.25; loss_carryforward_years: int=5; withholding_tax_rate: float=0.0
@dataclass
class AccountingInput:
    depreciation_life_years: int=20; declining_balance: bool=False; retained_earnings_opening: float=0; share_capital: float=1_000
@dataclass
class ValuationInput:
    project_discount_rate: float=0.10; equity_discount_rate: float=0.14; terminal_value_enabled: bool=True; terminal_ebitda_multiple: float=9.0; exit_cost_pct: float=0.01
@dataclass
class FinancingTranche:
    name: str; commitment: float; amortization_start: date; final_maturity: date
    instrument_type: str="senior_term"; enabled: bool=True; currency: str="USD"; gearing_pct: float=0.65; drawdown_priority: int=1; interest_rate: float=0.08; upfront_fee_pct: float=0.015; commitment_fee_pct: float=0.006; repayment_frequency_months: int=6; repayment_method: str="sculpted_dscr"; target_dscr: float=1.30; balloon_pct: float=0.0; cash_sweep_pct: float=0.0; dsra_months: int=6; liquidity_facility: bool=False
@dataclass
class ProjectModelInput:
    phases: list[PhaseInput]; financing: list[FinancingTranche]
    settings: Settings=field(default_factory=Settings); capex: CapexInput=field(default_factory=CapexInput); revenue: RevenueInput=field(default_factory=RevenueInput); operations: OperationsInput=field(default_factory=OperationsInput); tax: TaxInput=field(default_factory=TaxInput); accounting: AccountingInput=field(default_factory=AccountingInput); valuation: ValuationInput=field(default_factory=ValuationInput)
    def model_copy(self, deep=False): return deepcopy(self) if deep else ProjectModelInput(**self.__dict__)
    def model_dump(self, mode='json'): return asdict(self)

def base_case() -> ProjectModelInput:
    phases=[PhaseInput("Phase 1",12,date(2026,1,1),24,2,date(2028,3,1),36,180_000_000),PhaseInput("Phase 2",12,date(2029,1,1),24,2,date(2031,3,1),36,150_000_000,enabled=False)]
    financing=[FinancingTranche("Senior Term Loan",117_000_000,date(2029,6,30),date(2040,12,31))]
    return ProjectModelInput(phases=phases, financing=financing)
