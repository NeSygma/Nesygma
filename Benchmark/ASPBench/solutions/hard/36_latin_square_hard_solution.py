import clingo
import json

asp_program = """
row(1..8).
col(1..8).
val(1..8).

even(2). even(4). even(6). even(8).
odd(1). odd(3). odd(5). odd(7).

prefilled(1,1,1).
prefilled(1,8,8).
prefilled(2,2,6).
prefilled(3,3,4).
prefilled(4,4,5).
prefilled(5,5,7).
prefilled(6,6,4).
prefilled(7,7,6).
prefilled(8,8,3).
prefilled(8,1,8).

cell(R, C, V) :- prefilled(R, C, V).
1 { cell(R, C, V) : val(V) } 1 :- row(R), col(C), not prefilled(R, C, _).

:- row(R), val(V), #count { C : cell(R, C, V) } != 1.
:- col(C), val(V), #count { R : cell(R, C, V) } != 1.
:- row(R), col(C), C < 8, cell(R, C, V1), cell(R, C+1, V2), V1 + V2 <= 5.
:- #count { R, C : cell(R, C, V), even(V), R >= 1, R <= 4, C >= 1, C <= 4 } != 8.
:- #count { R, C : cell(R, C, V), odd(V), R >= 5, R <= 8, C >= 5, C <= 8 } != 8.
:- #sum { V, C : cell(1, C, V), C >= 1, C <= 4 } != 14.
:- #sum { V, R : cell(R, 1, V), R >= 1, R <= 4 } != 10.

#show cell/3.
"""

ctl = clingo.Control(["1"])
ctl.add("base", [], asp_program)
ctl.ground([("base", [])])

solution_grid = None

def on_model(model):
    global solution_grid
    grid = [[0 for _ in range(8)] for _ in range(8)]
    for atom in model.symbols(atoms=True):
        if atom.name == "cell" and len(atom.arguments) == 3:
            r = atom.arguments[0].number
            c = atom.arguments[1].number
            v = atom.arguments[2].number
            grid[r-1][c-1] = v
    solution_grid = grid

result = ctl.solve(on_model=on_model)

if result.satisfiable:
    output = {"grid": solution_grid}
    print(json.dumps(output))
else:
    print(json.dumps({"error": "No solution exists"}))
