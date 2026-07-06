import clingo
import json

asp_program = """
row(0..13).
col(0..13).
cell(R, C) :- row(R), col(C).

pattern_type(block).
pattern_type(boat).
pattern_type(loaf).

pattern_shape(block, 0, 0).
pattern_shape(block, 0, 1).
pattern_shape(block, 1, 0).
pattern_shape(block, 1, 1).

pattern_shape(boat, 0, 0).
pattern_shape(boat, 0, 1).
pattern_shape(boat, 1, 0).
pattern_shape(boat, 1, 2).
pattern_shape(boat, 2, 1).

pattern_shape(loaf, 0, 1).
pattern_shape(loaf, 0, 2).
pattern_shape(loaf, 1, 0).
pattern_shape(loaf, 1, 3).
pattern_shape(loaf, 2, 1).
pattern_shape(loaf, 2, 3).
pattern_shape(loaf, 3, 2).

1 { placed(P, R, C) : cell(R, C) } 1 :- pattern_type(P).

:- placed(P, R, C), pattern_shape(P, DR, DC), R + DR > 13.
:- placed(P, R, C), pattern_shape(P, DR, DC), C + DC > 13.

alive(R + DR, C + DC) :- placed(P, R, C), pattern_shape(P, DR, DC).

:- placed(P1, R1, C1), placed(P2, R2, C2), (P1, R1, C1) != (P2, R2, C2),
   pattern_shape(P1, DR1, DC1), pattern_shape(P2, DR2, DC2),
   R1 + DR1 == R2 + DR2, C1 + DC1 == C2 + DC2.

neighbor(R, C, NR, NC) :- cell(R, C), cell(NR, NC),
   |R - NR| <= 1, |C - NC| <= 1, (R, C) != (NR, NC).

neighbor_count(R, C, N) :- cell(R, C),
   N = #count { NR, NC : neighbor(R, C, NR, NC), alive(NR, NC) }.

:- alive(R, C), neighbor_count(R, C, N), N != 2, N != 3.

:- cell(R, C), not alive(R, C), neighbor_count(R, C, 3).

#show placed/3.
#show alive/2.
"""

ctl = clingo.Control(["1"])
ctl.add("base", [], asp_program)
ctl.ground([("base", [])])

solution_data = None

def on_model(model):
    global solution_data
    placed_patterns = {}
    alive_cells = set()
    
    for atom in model.symbols(atoms=True):
        if atom.name == "placed" and len(atom.arguments) == 3:
            pattern_name = str(atom.arguments[0])
            r = atom.arguments[1].number
            c = atom.arguments[2].number
            placed_patterns[pattern_name] = (r, c)
        elif atom.name == "alive" and len(atom.arguments) == 2:
            r = atom.arguments[0].number
            c = atom.arguments[1].number
            alive_cells.add((r, c))
    
    solution_data = {
        'placed_patterns': placed_patterns,
        'alive_cells': alive_cells
    }

result = ctl.solve(on_model=on_model)

if result.satisfiable and solution_data is not None:
    grid = [[0 for _ in range(14)] for _ in range(14)]
    
    for r, c in solution_data['alive_cells']:
        grid[r][c] = 1
    
    pattern_shapes = {
        'block': [(0, 0), (0, 1), (1, 0), (1, 1)],
        'boat': [(0, 0), (0, 1), (1, 0), (1, 2), (2, 1)],
        'loaf': [(0, 1), (0, 2), (1, 0), (1, 3), (2, 1), (2, 3), (3, 2)]
    }
    
    patterns_output = []
    for pattern_name, (anchor_r, anchor_c) in solution_data['placed_patterns'].items():
        cells = [(anchor_r + dr, anchor_c + dc) for dr, dc in pattern_shapes[pattern_name]]
        min_row = min(r for r, c in cells)
        max_row = max(r for r, c in cells)
        min_col = min(c for r, c in cells)
        max_col = max(c for r, c in cells)
        
        patterns_output.append({
            "name": pattern_name,
            "bbox": [min_row, min_col, max_row, max_col]
        })
    
    patterns_output.sort(key=lambda x: x['name'])
    
    output = {
        "grid": grid,
        "patterns": patterns_output
    }
    
    print(json.dumps(output, indent=2))
else:
    print(json.dumps({"error": "No solution exists"}))
