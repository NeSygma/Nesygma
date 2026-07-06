import clingo
import json

asp_program = """
position(1..12).
car_type(a). car_type(b). car_type(c). car_type(d).
option(1). option(2). option(3). option(4). option(5).

type_count(a, 3).
type_count(b, 3).
type_count(c, 4).
type_count(d, 2).

has_option(a, 1).
has_option(b, 3).
has_option(b, 4).
has_option(c, 2).
has_option(d, 5).

1 { assigned(P, T) : car_type(T) } 1 :- position(P).

:- car_type(T), type_count(T, Count), #count { P : assigned(P, T) } != Count.

effective_option1(P) :- assigned(P, T), has_option(T, 1).
effective_option1(P) :- assigned(P, T), has_option(T, 5).

:- assigned(1, T), has_option(T, 4).
:- assigned(12, T), has_option(T, 4).

:- assigned(P, T1), assigned(P+1, T2), has_option(T1, 2), has_option(T2, 2), 
   position(P), position(P+1).
:- assigned(P, T1), assigned(P+2, T2), has_option(T1, 2), has_option(T2, 2), 
   position(P), position(P+2).

:- position(P), position(P+3), 
   #count { Pos : effective_option1(Pos), Pos >= P, Pos <= P+3 } > 2.

preceded_by_ev(P) :- position(P), P > 1, assigned(P-1, T), has_option(T, 4).

:- preceded_by_ev(P), position(P+3),
   #count { Pos : assigned(Pos, T), has_option(T, 3), Pos >= P, Pos <= P+3 } > 1.

:- position(P), position(P+3), not preceded_by_ev(P),
   #count { Pos : assigned(Pos, T), has_option(T, 3), Pos >= P, Pos <= P+3 } > 2.
"""

ctl = clingo.Control(["1"])
ctl.add("base", [], asp_program)
ctl.ground([("base", [])])

solution_data = None

def on_model(model):
    global solution_data
    solution_data = {}
    for atom in model.symbols(atoms=True):
        if atom.name == "assigned" and len(atom.arguments) == 2:
            pos = atom.arguments[0].number
            car_type = str(atom.arguments[1])
            solution_data[pos] = car_type

result = ctl.solve(on_model=on_model)

if result.satisfiable:
    type_options = {
        'a': [1],
        'b': [3, 4],
        'c': [2],
        'd': [5]
    }
    
    sequence = []
    for pos in range(1, 13):
        car_type = solution_data[pos]
        sequence.append({
            "position": pos,
            "car_type": car_type.upper(),
            "options": type_options[car_type]
        })
    
    output = {
        "solution_found": True,
        "sequence": sequence
    }
else:
    output = {
        "solution_found": False,
        "error": "No valid sequence exists"
    }

print(json.dumps(output, indent=2))
