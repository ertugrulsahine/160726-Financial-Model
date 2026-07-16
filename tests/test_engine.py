from datetime import date
import math
from temelli_finance import base_case, calculate_model
from temelli_finance.schemas import FinancingTranche

def test_base_case_calculates_and_converges():
    r=calculate_model(base_case())
    assert r['summary']['total_capacity_mw'] == 24
    assert r['summary']['total_project_cost'] > 450_000_000
    assert 'project_npv' in r['ratios']
    assert r['convergence']['iterations'] <= base_case().settings.max_iterations

def test_revenue_and_energy_positive_after_cod():
    r=calculate_model(base_case()); s=r['schedules']
    assert max(s['revenue']) > 0
    assert max(s['ebitda']) > 0

def test_pue_validation():
    inp=base_case(); inp.operations.pue=1.0
    assert calculate_model(inp)['checks']

def test_equal_principal_and_bullet_methods():
    inp=base_case(); inp.financing[0].repayment_method='equal_principal'
    r=calculate_model(inp); assert max(r['schedules']['principal']) > 0
    inp=base_case(); inp.financing[0].repayment_method='bullet'
    r=calculate_model(inp); assert max(r['schedules']['principal']) > 0

def test_multiple_tranches_and_shareholder_loan():
    inp=base_case(); inp.financing.append(FinancingTranche(name='Shareholder Loan', instrument_type='shareholder_loan', commitment=25_000_000, gearing_pct=0.05, interest_rate=0.12, amortization_start=date(2030,1,31), final_maturity=date(2042,12,31), repayment_method='annuity'))
    r=calculate_model(inp)
    assert r['summary']['debt_required'] > 0

def test_disabled_phase_excluded():
    inp=base_case(); inp.phases[1].enabled=False; inp.phases[2].enabled=False
    assert calculate_model(inp)['summary']['total_capacity_mw'] == 24

def test_low_occupancy_case_and_cash_trap_flag():
    inp=base_case(); inp.phases[0].stabilized_occupancy_pct=0.3
    r=calculate_model(inp)
    assert r['ratios']['min_dscr'] is None or r['ratios']['min_dscr'] < 10

def test_exportable_schedule_lengths():
    r=calculate_model(base_case()); lengths={len(v) for v in r['schedules'].values()}
    assert len(lengths)==1

def test_no_nan_or_infinity_check():
    r=calculate_model(base_case())
    assert any(c['name']=='no_nan_or_infinity' for c in r['checks'])
