from __future__ import annotations
from dataclasses import dataclass
from datetime import date
import math
from .schemas import TemelliModelInput, FinancingTranche

@dataclass
class Trace:
    description: str; formula: str; inputs: list[str]; unit: str; frequency: str="Monthly"; sign: str="Positive values are cash inflows or assets unless labelled as costs"

def add_month(d: date, m: int) -> date:
    y=d.year+(d.month-1+m)//12; mo=(d.month-1+m)%12+1
    return date(y,mo,1)
def months(start: date, end: date):
    out=[]; d=date(start.year,start.month,1); e=date(end.year,end.month,1)
    while d<=e: out.append(d); d=add_month(d,1)
    return out
def mdiff(a: date,b: date): return (a.year-b.year)*12+a.month-b.month
def days_in_month(d: date): return (add_month(d,1)-d).days

def irr(values):
    if not (any(v<0 for v in values) and any(v>0 for v in values)): return None
    def f(r): return sum(v/((1+r)**i) for i,v in enumerate(values))
    lo,hi=-0.5,10.0
    for _ in range(160):
        mid=(lo+hi)/2
        if f(lo)*f(mid)<=0: hi=mid
        else: lo=mid
    return (lo+hi)/2
def npv(rate, values): return sum(v/((1+rate)**(i/12)) for i,v in enumerate(values))
def finite(seq): return all(math.isfinite(float(x)) for x in seq)

def _debt_schedule(tr: FinancingTranche, idx, draws, cfads, inp):
    n=len(idx); opening=[0]*n; closing=[0]*n; interest=[0]*n; principal=[0]*n; dsra=[0]*n
    amort=date(tr.amortization_start.year,tr.amortization_start.month,1); maturity=date(tr.final_maturity.year,tr.final_maturity.month,1)
    pay=[d>=amort and d<=maturity and ((d.month-amort.month)%tr.repayment_frequency_months==0) for d in idx]
    for i,d in enumerate(idx):
        opening[i]=closing[i-1] if i else 0; interest[i]=(opening[i]+draws[i]/2)*tr.interest_rate/12
        if d>=amort and d<=maturity and pay[i]:
            remaining=max(sum(pay[i:]),1); bal=opening[i]+draws[i]; target=tr.commitment*tr.balloon_pct if tr.repayment_method=='balloon' else 0
            if tr.repayment_method=='equal_principal': principal[i]=max((bal-target)/remaining,0)
            elif tr.repayment_method=='annuity':
                r=tr.interest_rate*tr.repayment_frequency_months/12; pmt=bal*r/(1-(1+r)**(-remaining)) if r else bal/remaining; principal[i]=max(pmt-interest[i],0)
            elif tr.repayment_method=='bullet': principal[i]=bal if d==maturity else 0
            elif tr.repayment_method in ('sculpted_dscr','cash_sweep'):
                allowed=max(cfads[i]/tr.target_dscr-interest[i],0); principal[i]=allowed+max(cfads[i]-interest[i]-allowed-inp.settings.minimum_cash_balance,0)*tr.cash_sweep_pct
        principal[i]=min(principal[i], opening[i]+draws[i]); closing[i]=opening[i]+draws[i]-principal[i]; dsra[i]=(interest[i]+principal[i])*tr.dsra_months/12
    return {'opening':opening,'drawdown':draws,'interest':interest,'principal':principal,'closing':closing,'dsra_required':dsra}

def calculate_model(inp: TemelliModelInput):
    if abs(sum(inp.capex.spend_curve)-1)>1e-6: raise ValueError('CAPEX spend curve must total 100%')
    idx=months(inp.settings.model_start, inp.settings.model_end); n=len(idx)
    capacity=[0.0]*n; occupied=[0.0]*n; capex=[0.0]*n
    for p in inp.phases:
        if not p.enabled: continue
        for i,d in enumerate(idx):
            mc=mdiff(d,p.cod); ms=mdiff(d,p.construction_start)
            if mc>=0:
                ramp=min(max((mc+1)/max(p.stabilization_months,1),0),1); occ=p.contracted_at_cod_pct+(p.stabilized_occupancy_pct-p.contracted_at_cod_pct)*ramp
                capacity[i]+=p.it_capacity_mw; occupied[i]+=p.it_capacity_mw*occ
            total=p.capex_total*(1+inp.capex.contingency_pct+inp.capex.non_recoverable_vat_pct)
            for k,pct in enumerate(inp.capex.spend_curve):
                begin=math.floor(k*p.construction_months/len(inp.capex.spend_curve)); end=math.floor((k+1)*p.construction_months/len(inp.capex.spend_curve))
                if ms>=begin and ms<end and end>begin: capex[i]+=total*pct/(end-begin)
    years=[i/12 for i in range(n)]
    price=[inp.revenue.colocation_price_per_kw_month*((1+inp.revenue.price_escalation)**y) for y in years]
    power=[occupied[i]*24*days_in_month(idx[i])*inp.operations.pue*inp.operations.electricity_price_per_mwh*((1+inp.operations.cost_escalation)**years[i]) for i in range(n)]
    revenue=[(occupied[i]*1000*(price[i]+inp.revenue.other_recurring_revenue_per_kw_month)+(power[i]*(1+inp.revenue.power_markup_pct) if inp.revenue.power_pass_through else 0))*(1-inp.revenue.bad_debt_pct) for i in range(n)]
    opex=[(occupied[i]*inp.operations.opex_per_occupied_mw_year+capacity[i]*inp.operations.fixed_opex_per_mw_year)/12*((1+inp.operations.cost_escalation)**years[i])+power[i] for i in range(n)]
    ebitda=[revenue[i]-opex[i] for i in range(n)]
    active=[t for t in inp.financing if t.enabled and not t.liquidity_facility]; total_commit=sum(t.commitment for t in active); gear=sum(t.gearing_pct for t in active)
    debt_target=[min(c*gear,total_commit) for c in capex]
    debt_interest=[0.0]*n; debt_principal=[0.0]*n; debt_draw=[0.0]*n; debt_close=[0.0]*n; dsra_req=[0.0]*n; diagnostics=[]; residual=0.0
    for it in range(1, inp.settings.max_iterations+1):
        old=debt_interest[:]; schedules=[]
        for tr in sorted(active,key=lambda x:x.drawdown_priority):
            share=tr.commitment/max(total_commit,1); draws=[x*share for x in debt_target]; schedules.append(_debt_schedule(tr,idx,draws,[max(ebitda[j]-old[j],0) for j in range(n)],inp))
        debt_interest=[sum(s['interest'][i] for s in schedules) for i in range(n)]; debt_principal=[sum(s['principal'][i] for s in schedules) for i in range(n)]; debt_draw=[sum(s['drawdown'][i] for s in schedules) for i in range(n)]; debt_close=[sum(s['closing'][i] for s in schedules) for i in range(n)]; dsra_req=[sum(s['dsra_required'][i] for s in schedules) for i in range(n)]
        residual=max(abs(debt_interest[i]-old[i]) for i in range(n)) if n else 0; diagnostics.append({'iteration':it,'largest_residual':residual,'schedule':'debt_interest'})
        debt_interest=[old[i]*(1-inp.settings.damping_factor)+debt_interest[i]*inp.settings.damping_factor for i in range(n)]
        if residual<inp.settings.tolerance: break
    converged=residual<inp.settings.tolerance
    depbase=[]; cum=0
    for c in capex: cum+=c; depbase.append(cum)
    depreciation=[x/(inp.accounting.depreciation_life_years*12) for x in depbase]
    taxable=[ebitda[i]-depreciation[i]-debt_interest[i] for i in range(n)]; tax=[max(x,0)*inp.tax.corporate_tax_rate for x in taxable]; cfads=[ebitda[i]-tax[i] for i in range(n)]
    equity_contrib=[max(capex[i]+debt_interest[i]+dsra_req[i]-debt_draw[i],0) for i in range(n)]
    cash=[0.0]*n; dividends=[0.0]*n; retained=[0.0]*n; trapped=[0.0]*n
    for i in range(n):
        opening=cash[i-1] if i else 0; ro=retained[i-1] if i else inp.accounting.retained_earnings_opening; ds=debt_interest[i]+debt_principal[i]; dscr=cfads[i]/ds if ds>0 else math.inf
        available=opening+cfads[i]+debt_draw[i]-capex[i]-debt_interest[i]-debt_principal[i]-equity_contrib[i]; distributable=max(available-inp.settings.minimum_cash_balance,0) if dscr>=1.15 else 0; legal=max(ro+taxable[i]-tax[i],0)
        dividends[i]=min(distributable,legal); trapped[i]=max(distributable-dividends[i],0) if dscr<1.15 else 0; cash[i]=available-dividends[i]; retained[i]=ro+taxable[i]-tax[i]-dividends[i]
    debt_service=[debt_interest[i]+debt_principal[i] for i in range(n)]; dscr=[cfads[i]/debt_service[i] if debt_service[i]>0 else math.inf for i in range(n)]
    project_cf=[cfads[i]-capex[i] for i in range(n)]; equity_cf=[dividends[i]-equity_contrib[i] for i in range(n)]; finite_dscr=[x for x in dscr if math.isfinite(x)]
    ratios={'project_irr':irr(project_cf),'equity_irr':irr(equity_cf),'project_npv':npv(inp.valuation.project_discount_rate,project_cf),'equity_npv':npv(inp.valuation.equity_discount_rate,equity_cf),'min_dscr':min(finite_dscr) if finite_dscr else None,'average_dscr':sum(finite_dscr)/len(finite_dscr) if finite_dscr else None,'llcr':npv(inp.valuation.project_discount_rate,cfads)/max(max(debt_close),1),'plcr':npv(inp.valuation.project_discount_rate,cfads)/max(sum(capex),1),'max_debt':max(debt_close),'gearing_debt_to_cost':sum(debt_draw)/max(sum(capex),1),'break_even_occupancy':max((opex[i]/(max(capacity[i],1)*1000*max(price[i],1)) for i in range(n)), default=0)}
    assets=[cash[i]+max(sum(capex[:i+1])-sum(depreciation[:i+1]),0) for i in range(n)]; equity=[retained[i]+sum(equity_contrib[:i+1])-sum(dividends[:i+1])+inp.accounting.share_capital for i in range(n)]; bs_diff=[assets[i]-debt_close[i]-equity[i] for i in range(n)]
    checks=[('sources_equal_uses',abs((sum(debt_draw)+sum(equity_contrib))-(sum(capex)+sum(debt_interest)+max(dsra_req, default=0)))<1e-2),('balance_sheet_balances',max(abs(x) for x in bs_diff)<1e-2),('circularity_converges',converged),('pue_not_below_one',inp.operations.pue>=1),('occupancy_within_capacity',all(occupied[i]<=max(capacity[i],occupied[i]) for i in range(n))),('no_nan_or_infinity',all(finite(x) for x in [revenue,opex,capex,cash]))]
    schedules={'period':[d.isoformat() for d in idx],'capacity_mw':capacity,'occupied_mw':occupied,'capex':capex,'revenue':revenue,'opex':opex,'ebitda':ebitda,'cfads':cfads,'debt_drawdown':debt_draw,'interest':debt_interest,'principal':debt_principal,'closing_debt':debt_close,'tax':tax,'cash':cash,'dividends':dividends,'retained_earnings':retained,'dscr':dscr}
    return {'meta':{'project_name':inp.settings.project_name,'scenario_name':inp.settings.scenario_name,'last_calculation_timestamp':'runtime'},'convergence':{'converged':converged,'iterations':it,'largest_residual':residual,'diagnostics':diagnostics,'residual_schedule':'debt_interest'},'schedules':schedules,'ratios':ratios,'checks':[{'name':n,'status':'pass' if ok else 'error','severity':'error' if not ok else 'info'} for n,ok in checks],'traces':{'interest':Trace('Interest expense by tranche uses opening debt, half-period current draw, annual cash interest rate and monthly day-count fraction.','(Opening debt + 0.5 × Drawdown) × Interest rate ÷ 12',['financing.interest_rate','financing.drawdown','debt.opening_balance'],'USD').__dict__},'summary':{'total_project_cost':sum(capex),'total_capacity_mw':max(capacity),'occupied_capacity_mw':max(occupied),'revenue_stabilized':max(revenue),'ebitda_stabilized':max(ebitda),'equity_required':sum(equity_contrib),'debt_required':sum(debt_draw),'shareholder_distributions':sum(dividends),'cash_trap_active':any(x>0 for x in trapped)}}
