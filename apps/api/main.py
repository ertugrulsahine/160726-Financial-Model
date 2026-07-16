from fastapi import FastAPI, Response
from pydantic import BaseModel
import json, csv, io
from temelli_finance import base_case, calculate_model, TemelliModelInput

app = FastAPI(title="Temelli Project Finance API", version="0.1.0")
SCENARIOS: dict[str, TemelliModelInput] = {"base": base_case()}

class ScenarioPayload(BaseModel):
    name: str
    inputs: TemelliModelInput

@app.get('/api/health')
def health(): return {"status":"ok"}

@app.get('/api/scenarios/base')
def get_base(): return SCENARIOS['base'].model_dump(mode='json')

@app.post('/api/scenarios')
def save_scenario(payload: ScenarioPayload):
    SCENARIOS[payload.name]=payload.inputs
    return {"saved": payload.name, "scenario_count": len(SCENARIOS)}

@app.get('/api/scenarios/{name}/calculate')
def calculate(name: str): return calculate_model(SCENARIOS.get(name, SCENARIOS['base']))

@app.post('/api/calculate')
def calculate_custom(inputs: TemelliModelInput): return calculate_model(inputs)

@app.get('/api/scenarios/{name}/export/json')
def export_json(name: str): return calculate_model(SCENARIOS.get(name, SCENARIOS['base']))

@app.get('/api/scenarios/{name}/export/csv')
def export_csv(name: str):
    result=calculate_model(SCENARIOS.get(name, SCENARIOS['base'])); rows=result['schedules']; output=io.StringIO(); writer=csv.writer(output)
    keys=list(rows.keys()); writer.writerow(keys)
    for row in zip(*[rows[k] for k in keys]): writer.writerow(row)
    return Response(output.getvalue(), media_type='text/csv')

@app.get('/api/scenarios/compare')
def compare(a: str='base', b: str='base'):
    ra=calculate_model(SCENARIOS.get(a, SCENARIOS['base'])); rb=calculate_model(SCENARIOS.get(b, SCENARIOS['base']))
    return {"a": a, "b": b, "kpis": {k: {"a": ra['ratios'].get(k), "b": rb['ratios'].get(k)} for k in ra['ratios']}}

@app.post('/api/sensitivities/one-way')
def sensitivity(inputs: TemelliModelInput, variable: str='revenue.colocation_price_per_kw_month', shocks: list[float]=[-0.1,0,0.1]):
    base=inputs.model_copy(deep=True); out=[]
    for s in shocks:
        mod=base.model_copy(deep=True); obj=mod
        parts=variable.split('.')
        for p in parts[:-1]: obj=getattr(obj,p)
        setattr(obj, parts[-1], getattr(obj, parts[-1])*(1+s))
        calc=calculate_model(mod); out.append({"shock":s,"ratios":calc['ratios']})
    return {"variable":variable,"results":out}
