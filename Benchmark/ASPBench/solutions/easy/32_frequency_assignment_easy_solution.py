import clingo
import json

program = """
transmitter("A"). transmitter("B"). transmitter("C").
transmitter("D"). transmitter("E"). transmitter("F").

frequency(1). frequency(2). frequency(3). frequency(4). frequency(5).

interferes("A", "B"). interferes("B", "A").
interferes("A", "C"). interferes("C", "A").
interferes("B", "D"). interferes("D", "B").
interferes("B", "E"). interferes("E", "B").
interferes("C", "D"). interferes("D", "C").
interferes("C", "F"). interferes("F", "C").
interferes("D", "E"). interferes("E", "D").
interferes("E", "F"). interferes("F", "E").

1 { assigned(T, F) : frequency(F) } 1 :- transmitter(T).

:- interferes(T1, T2), assigned(T1, F), assigned(T2, F).

:- interferes(T1, T2), assigned(T1, F1), assigned(T2, F2), |F1 - F2| == 1.

used(F) :- assigned(_, F).

:- #count { F : used(F) } > 3.
"""

ctl = clingo.Control(["1"])
ctl.add("base", [], program)
ctl.ground([("base", [])])

solution = None

def on_model(model):
    global solution
    assignments = []
    frequencies_used_set = set()
    
    for atom in model.symbols(atoms=True):
        if atom.name == "assigned" and len(atom.arguments) == 2:
            transmitter = str(atom.arguments[0]).strip('"')
            frequency = atom.arguments[1].number
            assignments.append({
                "transmitter": transmitter,
                "frequency": frequency
            })
            frequencies_used_set.add(frequency)
    
    assignments.sort(key=lambda x: x["transmitter"])
    
    solution = {
        "assignments": assignments,
        "frequencies_used": len(frequencies_used_set)
    }

result = ctl.solve(on_model=on_model)

if result.satisfiable:
    print(json.dumps(solution, indent=2))
else:
    print(json.dumps({"error": "No solution exists", 
                      "reason": "Problem constraints cannot be satisfied"}))
