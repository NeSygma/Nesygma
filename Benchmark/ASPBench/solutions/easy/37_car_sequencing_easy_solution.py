import clingo
import json

program = """
position(1..6).
car_type(a; b; c).

car_count(a, 1).
car_count(b, 2).
car_count(c, 3).

has_option(a, 1).
has_option(a, 2).
has_option(b, 3).
has_option(c, 1).

capacity(1, 2, 3).
capacity(2, 1, 2).
capacity(3, 1, 2).

1 { assigned(P, T) : car_type(T) } 1 :- position(P).

type_count(T, N) :- car_type(T), N = #count { P : assigned(P, T) }.
:- type_count(T, N), car_count(T, Required), N != Required.

car_has_option(P, O) :- assigned(P, T), has_option(T, O).

:- capacity(Option, MaxCount, WindowSize),
   position(Start),
   Start + WindowSize - 1 <= 6,
   #count { P : car_has_option(P, Option), P >= Start, P < Start + WindowSize } > MaxCount.

#show assigned/2.
"""

ctl = clingo.Control(["1"])
ctl.add("base", [], program)
ctl.ground([("base", [])])

solution_data = None

def on_model(model):
    global solution_data
    atoms = model.symbols(atoms=True)
    
    assignments = {}
    for atom in atoms:
        if atom.name == "assigned" and len(atom.arguments) == 2:
            pos = atom.arguments[0].number
            car_type = str(atom.arguments[1]).upper()
            assignments[pos] = car_type
    
    sequence = [assignments[i] for i in sorted(assignments.keys())]
    
    solution_data = {
        "sequence": sequence,
        "length": len(sequence)
    }

result = ctl.solve(on_model=on_model)

if result.satisfiable:
    print(json.dumps(solution_data))
else:
    print(json.dumps({"error": "No solution exists", "reason": "Constraints cannot be satisfied"}))
