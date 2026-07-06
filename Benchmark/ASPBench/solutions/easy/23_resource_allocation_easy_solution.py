import clingo
import json

program = """
task(0, 50, 30, 20, 10).
task(1, 40, 25, 15, 15).
task(2, 60, 20, 30, 20).
task(3, 35, 15, 25, 10).
task(4, 70, 40, 10, 25).
task(5, 45, 20, 20, 15).

resource_capacity(a, 100).
resource_capacity(b, 80).
resource_capacity(c, 60).

{ selected(T) } :- task(T, _, _, _, _).

:- #sum { ReqA,T : selected(T), task(T, _, ReqA, _, _) } > 100.
:- #sum { ReqB,T : selected(T), task(T, _, _, ReqB, _) } > 80.
:- #sum { ReqC,T : selected(T), task(T, _, _, _, ReqC) } > 60.

total_value(V) :- V = #sum { Val,T : selected(T), task(T, Val, _, _, _) }.

:- total_value(V), V < 180.

resource_used(a, A) :- A = #sum { ReqA,T : selected(T), task(T, _, ReqA, _, _) }.
resource_used(b, B) :- B = #sum { ReqB,T : selected(T), task(T, _, _, ReqB, _) }.
resource_used(c, C) :- C = #sum { ReqC,T : selected(T), task(T, _, _, _, ReqC) }.

#show selected/1.
#show total_value/1.
#show resource_used/2.
"""

ctl = clingo.Control(["1"])
ctl.add("base", [], program)
ctl.ground([("base", [])])

solution_data = None

def on_model(model):
    global solution_data
    
    selected_tasks = []
    total_value = 0
    resource_usage = {}
    
    for atom in model.symbols(atoms=True):
        if atom.name == "selected" and len(atom.arguments) == 1:
            task_id = atom.arguments[0].number
            selected_tasks.append(task_id)
        elif atom.name == "total_value" and len(atom.arguments) == 1:
            total_value = atom.arguments[0].number
        elif atom.name == "resource_used" and len(atom.arguments) == 2:
            res_type = str(atom.arguments[0])
            res_amount = atom.arguments[1].number
            
            if res_type == "a":
                resource_usage["resource_a"] = res_amount
            elif res_type == "b":
                resource_usage["resource_b"] = res_amount
            elif res_type == "c":
                resource_usage["resource_c"] = res_amount
    
    selected_tasks.sort()
    solution_data = {
        "selected_tasks": selected_tasks,
        "total_value": total_value,
        "resource_usage": resource_usage
    }

result = ctl.solve(on_model=on_model)

if result.satisfiable:
    print(json.dumps(solution_data))
else:
    print(json.dumps({"error": "No solution exists", 
                      "reason": "Resource constraints cannot be satisfied"}))
