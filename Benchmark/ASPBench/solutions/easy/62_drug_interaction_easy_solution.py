import clingo
import json

asp_program = """
patient_condition("pain").
patient_condition("hypertension").
patient_condition("diabetes").
patient_contraindication("bleeding_disorder").
max_drugs(3).

drug("drug1"). drug("drug2"). drug("drug3"). drug("drug4"). drug("drug5").

treats("drug1", "pain").
treats("drug1", "inflammation").
treats("drug2", "blood_clot_prevention").
treats("drug3", "hypertension").
treats("drug4", "diabetes").
treats("drug5", "pain").
treats("drug5", "inflammation").

drug_contraindication("drug1", "bleeding_disorder").
drug_contraindication("drug2", "pregnancy").
drug_contraindication("drug3", "kidney_disease").
drug_contraindication("drug4", "kidney_disease").

max_dose("drug1", 4000).
max_dose("drug2", 10).
max_dose("drug3", 40).
max_dose("drug4", 2000).
max_dose("drug5", 2400).

interaction("drug1", "drug2", "increased_bleeding", "moderate").
interaction("drug2", "drug1", "increased_bleeding", "moderate").
interaction("drug3", "drug4", "mild_nausea", "mild").
interaction("drug4", "drug3", "mild_nausea", "mild").
interaction("drug5", "drug3", "reduced_bp_effect", "moderate").
interaction("drug3", "drug5", "reduced_bp_effect", "moderate").

severity_cost("severe", 100).
severity_cost("moderate", 50).
severity_cost("mild", 20).

{ prescribe(D) : drug(D) } N :- max_drugs(N).

:- prescribe(D), drug_contraindication(D, C), patient_contraindication(C).

treated(C) :- patient_condition(C), prescribe(D), treats(D, C).

num_treated(N) :- N = #count { C : treated(C) }.

has_interaction(D1, D2, Type, Severity) :- 
    prescribe(D1), prescribe(D2), D1 < D2,
    interaction(D1, D2, Type, Severity).

total_interaction_cost(Cost) :- 
    Cost = #sum { C, D1, D2 : has_interaction(D1, D2, _, Sev), severity_cost(Sev, C) }.
total_interaction_cost(0) :- not has_interaction(_, _, _, _).

#minimize { Cost@2 : total_interaction_cost(Cost) }.
#maximize { N@1 : num_treated(N) }.
"""

ctl = clingo.Control(["0"])
ctl.add("base", [], asp_program)
ctl.ground([("base", [])])

best_solution = None

def on_model(model):
    global best_solution
    
    prescribed = []
    for atom in model.symbols(atoms=True):
        if atom.name == "prescribe" and len(atom.arguments) == 1:
            drug_id = str(atom.arguments[0]).strip('"')
            prescribed.append(drug_id)
    
    treated = []
    for atom in model.symbols(atoms=True):
        if atom.name == "treated" and len(atom.arguments) == 1:
            condition = str(atom.arguments[0]).strip('"')
            treated.append(condition)
    
    interactions = []
    for atom in model.symbols(atoms=True):
        if atom.name == "has_interaction" and len(atom.arguments) == 4:
            d1 = str(atom.arguments[0]).strip('"')
            d2 = str(atom.arguments[1]).strip('"')
            interaction_type = str(atom.arguments[2]).strip('"')
            severity = str(atom.arguments[3]).strip('"')
            interactions.append({
                "drugs": [d1, d2],
                "interaction": interaction_type,
                "severity": severity
            })
    
    best_solution = {
        "prescribed": sorted(prescribed),
        "treated": sorted(treated),
        "interactions": interactions
    }

result = ctl.solve(on_model=on_model)

if result.satisfiable and best_solution:
    drug_info = {
        "drug1": {"max_dose": 4000},
        "drug2": {"max_dose": 10},
        "drug3": {"max_dose": 40},
        "drug4": {"max_dose": 2000},
        "drug5": {"max_dose": 2400}
    }
    
    frequency_map = {
        "drug1": "twice_daily",
        "drug2": "once_daily",
        "drug3": "once_daily",
        "drug4": "twice_daily",
        "drug5": "twice_daily"
    }
    
    all_conditions = ["pain", "hypertension", "diabetes"]
    patient_contraindications = ["bleeding_disorder"]
    
    prescribed_drugs = []
    for drug_id in best_solution['prescribed']:
        dose = drug_info[drug_id]["max_dose"] // 2
        prescribed_drugs.append({
            "drug_id": drug_id,
            "dose": dose,
            "frequency": frequency_map[drug_id]
        })
    
    treated_conditions = best_solution['treated']
    untreated_conditions = [c for c in all_conditions if c not in treated_conditions]
    
    num_treated = len(treated_conditions)
    total_conditions = len(all_conditions)
    coverage_bonus = (num_treated / total_conditions) * 0.5
    
    interaction_penalty = 0
    for interaction in best_solution['interactions']:
        severity = interaction['severity']
        if severity == "severe":
            interaction_penalty += 0.3
        elif severity == "moderate":
            interaction_penalty += 0.15
        elif severity == "mild":
            interaction_penalty += 0.05
    
    safety_score = 0.5 + coverage_bonus - interaction_penalty
    safety_score = max(0.0, min(1.0, safety_score))
    
    output = {
        "prescribed_drugs": prescribed_drugs,
        "treated_conditions": treated_conditions,
        "untreated_conditions": untreated_conditions,
        "safety_analysis": {
            "interactions_detected": best_solution['interactions'],
            "contraindications_avoided": patient_contraindications,
            "safety_score": round(safety_score, 2)
        }
    }
    
    print(json.dumps(output, indent=2))
else:
    print(json.dumps({"error": "No solution exists", "reason": "Unable to find valid prescription"}))
