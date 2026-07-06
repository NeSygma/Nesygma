import clingo
import json

asp_program = """
die(a;b;c).
face(1..6).
value(0;1;2;3;4;5;6).

1 { face_value(D, F, V) : value(V) } 1 :- die(D), face(F).

wins(D1, D2, Count) :- die(D1), die(D2), D1 != D2,
    Count = #count { F1, F2 : face_value(D1, F1, V1), face_value(D2, F2, V2), V1 > V2 }.

:- wins(a, b, Count), Count <= 18.
:- wins(b, c, Count), Count <= 18.
:- wins(c, a, Count), Count <= 18.

:- face_value(a, 1, V1), face_value(a, F, V2), F > 1, V2 < V1.

#show face_value/3.
#show wins/3.
"""

ctl = clingo.Control(["1", "--configuration=tweety"])
ctl.add("base", [], asp_program)
ctl.ground([("base", [])])

dice_solution = None
wins_solution = None

def extract_model(model):
    global dice_solution, wins_solution
    
    dice_faces = {'a': {}, 'b': {}, 'c': {}}
    win_counts = {}
    
    for atom in model.symbols(atoms=True):
        if atom.name == "face_value":
            die = str(atom.arguments[0])
            face = atom.arguments[1].number
            value = atom.arguments[2].number
            dice_faces[die][face] = value
        elif atom.name == "wins":
            d1 = str(atom.arguments[0])
            d2 = str(atom.arguments[1])
            count = atom.arguments[2].number
            win_counts[f"{d1}_{d2}"] = count
    
    dice_solution = dice_faces
    wins_solution = win_counts

result = ctl.solve(on_model=extract_model)

if result.satisfiable and dice_solution:
    final_solution = {
        "dice": {
            "A": [dice_solution['a'][i] for i in sorted(dice_solution['a'].keys())],
            "B": [dice_solution['b'][i] for i in sorted(dice_solution['b'].keys())],
            "C": [dice_solution['c'][i] for i in sorted(dice_solution['c'].keys())]
        },
        "win_probabilities": {
            "A_beats_B": wins_solution['a_b'] / 36,
            "B_beats_C": wins_solution['b_c'] / 36,
            "C_beats_A": wins_solution['c_a'] / 36
        }
    }
    print(json.dumps(final_solution, indent=2))
else:
    print(json.dumps({"error": "No solution exists", "reason": "Could not find dice configuration satisfying nontransitive property"}))
