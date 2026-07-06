import clingo
import json

sudoku_clues = [
    (0, 0, 5), (0, 4, 7), (0, 8, 2),
    (4, 0, 4), (4, 4, 5), (4, 8, 1),
    (8, 0, 3), (8, 4, 8), (8, 8, 9)
]

mine_count_clues = [(0, 1), (3, 1), (5, 7)]

asp_program = """
row(0..8).
col(0..8).
value(1..9).
box(0..2).

1 { cell(R, C, V) : value(V) } 1 :- row(R), col(C).

:- row(R), value(V), #count { C : cell(R, C, V) } != 1.

:- col(C), value(V), #count { R : cell(R, C, V) } != 1.

:- box(BR), box(BC), value(V),
   #count { R, C : cell(R, C, V), R/3 == BR, C/3 == BC } != 1.

neighbor(R1, C1, R2, C2) :- row(R1), col(C1), row(R2), col(C2),
    R2 >= R1-1, R2 <= R1+1, C2 >= C1-1, C2 <= C1+1,
    (R1, C1) != (R2, C2).

is_mine(R, C) :- cell(R, C, V), V \\ 2 == 0.

mine_count(R, C, Count) :- row(R), col(C),
    Count = #count { R2, C2 : neighbor(R, C, R2, C2), is_mine(R2, C2) }.

:- mine_clue(R, C), cell(R, C, V), mine_count(R, C, Count), V != Count.

:~ sudoku_hint(R, C, V), not cell(R, C, V). [1@1, R, C]
"""

facts = []
for r, c in mine_count_clues:
    facts.append(f"mine_clue({r}, {c}).")
for r, c, v in sudoku_clues:
    facts.append(f"sudoku_hint({r}, {c}, {v}).")

asp_program = "\n".join(facts) + "\n" + asp_program

ctl = clingo.Control(["1"])
ctl.add("base", [], asp_program)
ctl.ground([("base", [])])

solution_data = None

def on_model(model):
    global solution_data
    grid = [[0 for _ in range(9)] for _ in range(9)]
    mines = []
    
    for atom in model.symbols(atoms=True):
        if atom.name == "cell" and len(atom.arguments) == 3:
            r = atom.arguments[0].number
            c = atom.arguments[1].number
            v = atom.arguments[2].number
            grid[r][c] = v
            if v % 2 == 0:
                mines.append([r, c])
    
    solution_data = {"grid": grid, "mines": sorted(mines)}

result = ctl.solve(on_model=on_model)

if result.satisfiable and solution_data:
    grid = solution_data["grid"]
    
    is_valid_sudoku = True
    for row in grid:
        if sorted(row) != list(range(1, 10)):
            is_valid_sudoku = False
    for c in range(9):
        col = [grid[r][c] for r in range(9)]
        if sorted(col) != list(range(1, 10)):
            is_valid_sudoku = False
    for br in range(3):
        for bc in range(3):
            box = [grid[r][c] for r in range(br*3, br*3+3) 
                   for c in range(bc*3, bc*3+3)]
            if sorted(box) != list(range(1, 10)):
                is_valid_sudoku = False
    
    mine_clues_satisfied = True
    for r, c in mine_count_clues:
        value = grid[r][c]
        mine_count = 0
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < 9 and 0 <= nc < 9:
                    if grid[nr][nc] % 2 == 0:
                        mine_count += 1
        if value != mine_count:
            mine_clues_satisfied = False
    
    sudoku_clues_preserved = True
    for r, c, v in sudoku_clues:
        if grid[r][c] != v:
            sudoku_clues_preserved = False
    
    solution_data["is_valid_sudoku"] = is_valid_sudoku
    solution_data["sudoku_clues_preserved"] = sudoku_clues_preserved
    solution_data["mine_clues_satisfied"] = mine_clues_satisfied
    
    print(json.dumps(solution_data))
else:
    print(json.dumps({"error": "No solution exists"}))
