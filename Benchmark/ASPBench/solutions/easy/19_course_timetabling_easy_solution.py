import clingo
import json

program = """
course(0, 0, 25).
course(1, 1, 20).
course(2, 2, 30).
course(3, 1, 15).
course(4, 0, 35).

room(0, 40).
room(1, 25).
room(2, 20).

time_slot(0).
time_slot(1).
time_slot(2).
time_slot(3).

teacher_available(0, 0).
teacher_available(0, 1).
teacher_available(0, 2).
teacher_available(1, 1).
teacher_available(1, 2).
teacher_available(1, 3).
teacher_available(2, 0).
teacher_available(2, 2).
teacher_available(2, 3).

1 { scheduled(C, R, T) : room(R, _), time_slot(T) } 1 :- course(C, _, _).

:- scheduled(C1, R, T), scheduled(C2, R, T), C1 != C2.

:- scheduled(C1, R1, T), scheduled(C2, R2, T), 
   course(C1, Teacher, _), course(C2, Teacher, _), C1 != C2.

:- scheduled(C, R, T), course(C, _, Students), room(R, Capacity), 
   Students > Capacity.

:- scheduled(C, R, T), course(C, Teacher, _), 
   not teacher_available(Teacher, T).

#show scheduled/3.
"""

ctl = clingo.Control(["1"])
ctl.add("base", [], program)
ctl.ground([("base", [])])

solution = None

def on_model(model):
    global solution
    solution = {"assignments": []}
    
    for atom in model.symbols(atoms=True):
        if atom.name == "scheduled" and len(atom.arguments) == 3:
            course = atom.arguments[0].number
            room = atom.arguments[1].number
            time_slot = atom.arguments[2].number
            
            solution["assignments"].append({
                "course": course,
                "room": room,
                "time_slot": time_slot
            })
    
    solution["assignments"].sort(key=lambda x: x["course"])

result = ctl.solve(on_model=on_model)

if result.satisfiable:
    print(json.dumps(solution, indent=2))
else:
    error_solution = {
        "error": "No solution exists", 
        "reason": "Constraints cannot be satisfied"
    }
    print(json.dumps(error_solution, indent=2))
