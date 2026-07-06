import clingo
import json

program = """
row(1..3).
col(1..3).
num(1..9).

1 { cell(R, C, N) : num(N) } 1 :- row(R), col(C).

:- num(N), #count { R, C : cell(R, C, N) } != 1.

:- row(R), #sum { N, C : cell(R, C, N) } != 15.

:- col(C), #sum { N, R : cell(R, C, N) } != 15.

:- #sum { N, R : cell(R, R, N) } != 15.

:- #sum { N, R : cell(R, 4-R, N) } != 15.

#show cell/3.
"""

ctl = clingo.Control(["1"])
ctl.add("base", [], program)
ctl.ground([("base", [])])

solution_data = None

def on_model(model):
    global solution_data
    atoms = model.symbols(atoms=True)
    square = [[0 for _ in range(3)] for _ in range(3)]
    
    for atom in atoms:
        if atom.name == "cell" and len(atom.arguments) == 3:
            row = atom.arguments[0].number - 1
            col = atom.arguments[1].number - 1
            value = atom.arguments[2].number
            square[row][col] = value
    
    solution_data = square

result = ctl.solve(on_model=on_model)

if result.satisfiable and solution_data:
    output = {
        "square": solution_data,
        "magic_sum": 15,
        "valid": True
    }
    print(json.dumps(output))
else:
    print(json.dumps({"error": "No solution exists", "reason": "UNSAT"}))
