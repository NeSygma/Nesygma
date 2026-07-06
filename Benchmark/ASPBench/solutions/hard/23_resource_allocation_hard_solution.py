import clingo
import json

asp_program = """
task(0, research, 40, 20, 10, 30, 5).
task(1, research, 60, 30, 25, 20, 10).
task(2, research, 70, 25, 20, 15, 5).
task(3, research, 55, 20, 15, 25, 10).
task(4, development, 80, 40, 30, 20, 20).
task(5, development, 90, 35, 25, 30, 15).
task(6, development, 75, 30, 40, 25, 18).
task(7, development, 85, 45, 35, 15, 22).
task(8, deployment, 65, 15, 20, 40, 8).
task(9, deployment, 80, 20, 30, 35, 12).
task(10, deployment, 70, 25, 25, 30, 10).
task(11, deployment, 95, 30, 35, 45, 15).

capacity(compute, 150).
capacity(bandwidth, 120).
capacity(storage, 140).
capacity(specialists, 60).

{ selected(ID) } :- task(ID, _, _, _, _, _, _).

category_selected(Cat) :- selected(ID), task(ID, Cat, _, _, _, _, _).

dev_selected :- selected(ID), task(ID, development, _, _, _, _, _).

diversity_bonus :- category_selected(research), 
                   category_selected(development), 
                   category_selected(deployment).

:- capacity(compute, Cap), 
   #sum { C,ID : selected(ID), task(ID, _, _, C, _, _, _) } > Cap.

:- capacity(bandwidth, Cap), 
   #sum { B,ID : selected(ID), task(ID, _, _, _, B, _, _) } > Cap.

:- capacity(storage, Cap), 
   #sum { S,ID : selected(ID), task(ID, _, _, _, _, S, _) } > Cap.

base_specialists(Total) :- 
   Total = #sum { Sp,ID : selected(ID), task(ID, _, _, _, _, _, Sp) }.

conditional_specialists(Extra) :- 
   dev_selected,
   Extra = #sum { 5,ID : selected(ID), task(ID, deployment, _, _, _, _, _) }.

conditional_specialists(0) :- not dev_selected.

total_specialists(Total) :- 
   base_specialists(Base), 
   conditional_specialists(Extra), 
   Total = Base + Extra.

:- capacity(specialists, Cap), total_specialists(Total), Total > Cap.

:- selected(4), not selected(0).

:- selected(1), selected(7).

base_value(V) :- V = #sum { Val,ID : selected(ID), task(ID, _, Val, _, _, _, _) }.

total_value(V) :- base_value(Base), diversity_bonus, V = Base + 100.
total_value(V) :- base_value(V), not diversity_bonus.

:- total_value(V), V < 470.

#show selected/1.
#show total_value/1.
#show diversity_bonus/0.
"""

tasks_data = [
    (0, "research", 40, 20, 10, 30, 5),
    (1, "research", 60, 30, 25, 20, 10),
    (2, "research", 70, 25, 20, 15, 5),
    (3, "research", 55, 20, 15, 25, 10),
    (4, "development", 80, 40, 30, 20, 20),
    (5, "development", 90, 35, 25, 30, 15),
    (6, "development", 75, 30, 40, 25, 18),
    (7, "development", 85, 45, 35, 15, 22),
    (8, "deployment", 65, 15, 20, 40, 8),
    (9, "deployment", 80, 20, 30, 35, 12),
    (10, "deployment", 70, 25, 25, 30, 10),
    (11, "deployment", 95, 30, 35, 45, 15),
]

ctl = clingo.Control(["1"])
ctl.add("base", [], asp_program)
ctl.ground([("base", [])])

solution_data = None

def on_model(model):
    global solution_data
    selected_tasks = []
    total_val = 0
    bonus = False
    
    for atom in model.symbols(atoms=True):
        if atom.name == "selected" and len(atom.arguments) == 1:
            selected_tasks.append(atom.arguments[0].number)
        elif atom.name == "total_value" and len(atom.arguments) == 1:
            total_val = atom.arguments[0].number
        elif atom.name == "diversity_bonus" and len(atom.arguments) == 0:
            bonus = True
    
    selected_tasks.sort()
    solution_data = {
        'selected_tasks': selected_tasks,
        'total_value': total_val,
        'bonus': bonus
    }

result = ctl.solve(on_model=on_model)

if result.satisfiable and solution_data:
    selected = solution_data['selected_tasks']
    compute_used = 0
    bandwidth_used = 0
    storage_used = 0
    specialists_used = 0
    
    for task_id in selected:
        tid, cat, val, comp, band, stor, spec = tasks_data[task_id]
        compute_used += comp
        bandwidth_used += band
        storage_used += stor
        specialists_used += spec
    
    has_dev = any(tasks_data[tid][1] == "development" for tid in selected)
    if has_dev:
        deployment_count = sum(1 for tid in selected if tasks_data[tid][1] == "deployment")
        specialists_used += deployment_count * 5
    
    output = {
        "selected_tasks": selected,
        "total_value": solution_data['total_value'],
        "bonus_achieved": solution_data['bonus'],
        "resource_usage": {
            "compute": compute_used,
            "bandwidth": bandwidth_used,
            "storage": storage_used,
            "specialists": specialists_used
        }
    }
    
    print(json.dumps(output, indent=2))
else:
    print(json.dumps({"error": "No solution exists", "reason": "Constraints cannot be satisfied"}))
