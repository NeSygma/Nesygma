import clingo
import json

asp_program = """
drug(cardio_ease).
drug(metformax).
drug(anxio_calm).
drug(pain_off).
drug(glucopain).
drug(hydro_stress).
drug(renal_guard).
drug(pain_plus).

treats(cardio_ease, hypertension).
treats(metformax, diabetes).
treats(anxio_calm, anxiety).
treats(pain_off, pain).
treats(glucopain, diabetes).
treats(glucopain, pain).
treats(hydro_stress, hypertension).
treats(hydro_stress, anxiety).
treats(renal_guard, hypertension).
treats(pain_plus, pain).

cost(cardio_ease, 50).
cost(metformax, 40).
cost(anxio_calm, 70).
cost(pain_off, 60).
cost(glucopain, 110).
cost(hydro_stress, 90).
cost(renal_guard, 120).
cost(pain_plus, 80).

toxicity(cardio_ease, 20).
toxicity(metformax, 25).
toxicity(anxio_calm, 30).
toxicity(pain_off, 15).
toxicity(glucopain, 40).
toxicity(hydro_stress, 35).
toxicity(renal_guard, 10).
toxicity(pain_plus, 25).

max_dose(cardio_ease, 100).
max_dose(metformax, 1000).
max_dose(anxio_calm, 50).
max_dose(pain_off, 400).
max_dose(glucopain, 600).
max_dose(hydro_stress, 200).
max_dose(renal_guard, 150).
max_dose(pain_plus, 300).

standard_contraindication(renal_guard, renal_failure).
genetic_contraindication(glucopain, g6pd_deficiency).

interaction(metformax, pain_plus, reduced_efficacy, moderate).
interaction(pain_plus, metformax, reduced_efficacy, moderate).

conditional_interaction(hydro_stress, metformax, diabetes, severe).
conditional_interaction(metformax, hydro_stress, diabetes, severe).

synergy(pain_plus, anxio_calm, anxiety, 2).
synergy(anxio_calm, pain_plus, anxiety, 2).

patient_condition(hypertension).
patient_condition(diabetes).
patient_condition(anxiety).
patient_condition(pain).

patient_contraindication(renal_failure).
patient_genetic(g6pd_deficiency).

max_drugs(4).
max_budget(250).
max_toxicity(100).

{ selected(D) : drug(D) } :- max_drugs(M).

:- #count { D : selected(D) } > M, max_drugs(M).

total_cost(C) :- C = #sum { Cost, D : selected(D), cost(D, Cost) }.
:- total_cost(C), max_budget(B), C > B.

total_toxicity(T) :- T = #sum { Tox, D : selected(D), toxicity(D, Tox) }.
:- total_toxicity(T), max_toxicity(M), T > M.

:- selected(D), standard_contraindication(D, C), patient_contraindication(C).
:- selected(D), genetic_contraindication(D, G), patient_genetic(G).

active_interaction(D1, D2, Type, severe) :- 
    selected(D1), selected(D2), D1 < D2,
    interaction(D1, D2, Type, severe).

active_interaction(D1, D2, conditional, severe) :- 
    selected(D1), selected(D2), D1 < D2,
    conditional_interaction(D1, D2, Cond, severe),
    patient_condition(Cond).

:- active_interaction(_, _, _, severe).

treated(Cond) :- patient_condition(Cond), selected(D), treats(D, Cond).
:- patient_condition(Cond), not treated(Cond).

:- total_cost(C), C > 220.

#show selected/1.
#show total_cost/1.
#show total_toxicity/1.
#show treated/1.
"""

drug_data = {
    'cardio_ease': {'cost': 50, 'toxicity': 20, 'max_dose': 100, 
                    'treats': ['hypertension']},
    'metformax': {'cost': 40, 'toxicity': 25, 'max_dose': 1000, 
                  'treats': ['diabetes']},
    'anxio_calm': {'cost': 70, 'toxicity': 30, 'max_dose': 50, 
                   'treats': ['anxiety']},
    'pain_off': {'cost': 60, 'toxicity': 15, 'max_dose': 400, 
                 'treats': ['pain']},
    'glucopain': {'cost': 110, 'toxicity': 40, 'max_dose': 600, 
                  'treats': ['diabetes', 'pain']},
    'hydro_stress': {'cost': 90, 'toxicity': 35, 'max_dose': 200, 
                     'treats': ['hypertension', 'anxiety']},
    'renal_guard': {'cost': 120, 'toxicity': 10, 'max_dose': 150, 
                    'treats': ['hypertension']},
    'pain_plus': {'cost': 80, 'toxicity': 25, 'max_dose': 300, 
                  'treats': ['pain']}
}

interactions_db = {
    ('metformax', 'pain_plus'): {'interaction': 'reduced_efficacy', 
                                  'severity': 'moderate'},
    ('hydro_stress', 'metformax'): {'interaction': 'conditional', 
                                     'severity': 'severe', 
                                     'condition': 'diabetes'}
}

patient_conditions = ['hypertension', 'diabetes', 'anxiety', 'pain']
patient_contraindications = ['renal_failure']
patient_genetics = ['g6pd_deficiency']

ctl = clingo.Control(["1"])
ctl.add("base", [], asp_program)
ctl.ground([("base", [])])

solution_data = None

def on_model(model):
    global solution_data
    
    selected_drugs = []
    treated_conditions = set()
    total_cost = 0
    total_toxicity = 0
    
    for atom in model.symbols(atoms=True):
        if atom.name == "selected" and len(atom.arguments) == 1:
            drug_id = str(atom.arguments[0])
            selected_drugs.append(drug_id)
        elif atom.name == "treated" and len(atom.arguments) == 1:
            condition = str(atom.arguments[0])
            treated_conditions.add(condition)
        elif atom.name == "total_cost" and len(atom.arguments) == 1:
            total_cost = atom.arguments[0].number
        elif atom.name == "total_toxicity" and len(atom.arguments) == 1:
            total_toxicity = atom.arguments[0].number
    
    solution_data = {
        'selected_drugs': selected_drugs,
        'treated_conditions': sorted(list(treated_conditions)),
        'total_cost': total_cost,
        'total_toxicity': total_toxicity
    }

result = ctl.solve(on_model=on_model)

if result.satisfiable:
    prescribed_drugs = []
    for drug_id in solution_data['selected_drugs']:
        dose = drug_data[drug_id]['max_dose'] // 2
        prescribed_drugs.append({'drug_id': drug_id, 'dose': dose})
    
    prescribed_drugs.sort(key=lambda x: x['drug_id'])
    
    treated_conditions = set()
    for drug_id in solution_data['selected_drugs']:
        treated_conditions.update(drug_data[drug_id]['treats'])
    
    untreated_conditions = [c for c in patient_conditions 
                            if c not in treated_conditions]
    
    interactions_detected = []
    for i, drug1 in enumerate(sorted(solution_data['selected_drugs'])):
        for drug2 in sorted(solution_data['selected_drugs'])[i+1:]:
            pair = tuple(sorted([drug1, drug2]))
            if pair in interactions_db:
                interaction_info = interactions_db[pair]
                if 'condition' in interaction_info:
                    if interaction_info['condition'] in patient_conditions:
                        interactions_detected.append({
                            'drugs': list(pair),
                            'interaction': interaction_info['interaction'],
                            'severity': interaction_info['severity']
                        })
                else:
                    interactions_detected.append({
                        'drugs': list(pair),
                        'interaction': interaction_info['interaction'],
                        'severity': interaction_info['severity']
                    })
    
    output = {
        'prescribed_drugs': prescribed_drugs,
        'treated_conditions': sorted(list(treated_conditions)),
        'untreated_conditions': untreated_conditions,
        'total_cost': solution_data['total_cost'],
        'total_toxicity': solution_data['total_toxicity'],
        'safety_analysis': {
            'interactions_detected': interactions_detected,
            'contraindications_avoided': patient_contraindications,
            'genetic_markers_respected': patient_genetics
        }
    }
    
    print(json.dumps(output, indent=2))
else:
    print(json.dumps({"error": "No solution exists", 
                      "reason": "Constraints cannot be satisfied"}))
