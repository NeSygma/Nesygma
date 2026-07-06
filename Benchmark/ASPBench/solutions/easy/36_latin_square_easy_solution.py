import clingo
import json

program = """
row(1..5).
col(1..5).
value(1..5).

given(1, 1, 1).
given(2, 3, 3).
given(3, 4, 4).
given(4, 5, 5).
given(5, 2, 2).

cell(R, C, V) :- given(R, C, V).

1 { cell(R, C, V) : value(V) } 1 :- row(R), col(C), not given(R, C, _).

:- row(R), value(V), #count { C : cell(R, C, V) } != 1.

:- col(C), value(V), #count { R : cell(R, C, V) } != 1.
"""

ctl = clingo.Control(["1"])
ctl.add("base", [], program)
ctl.ground([("base", [])])

solution_grid = None
solved = False

def on_model(model):
    global solution_grid, solved
    grid = [[0 for _ in range(5)] for _ in range(5)]
    
    for atom in model.symbols(atoms=True):
        if atom.name == "cell" and len(atom.arguments) == 3:
            row = atom.arguments[0].number
            col = atom.arguments[1].number
            val = atom.arguments[2].number
            grid[row-1][col-1] = val
    
    solution_grid = grid
    solved = True

result = ctl.solve(on_model=on_model)

if result.satisfiable and solved:
    output = {
        "grid": solution_grid,
        "solved": True
    }
else:
    output = {
        "error": "No solution exists",
        "reason": "The given constraints cannot be satisfied",
        "solved": False
    }

print(json.dumps(output))
