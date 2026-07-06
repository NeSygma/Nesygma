import clingo
import json

row_clues = [
    [(1,10), (2,4), (1,10)],
    [(1,10), (2,4), (1,10)],
    [(1,2), (2,4), (1,2)],
    [(1,2), (2,4), (1,2)],
    [(1,2), (2,4), (1,2)],
    [(1,2), (2,4), (1,2)],
    [(1,2), (2,4), (1,2)],
    [(1,2), (2,4), (1,2)],
    [(1,2), (3,8), (1,2)],
    [(1,2), (3,8), (1,2)],
    [(1,2), (2,6), (3,8), (2,6), (1,2)],
    [(1,2), (2,6), (3,8), (2,6), (1,2)],
    [(1,2), (2,6), (3,8), (2,6), (1,2)],
    [(1,2), (2,6), (3,8), (2,6), (1,2)],
    [(1,2), (3,8), (1,2)],
    [(1,2), (3,8), (1,2)],
    [(1,2), (2,4), (1,2)],
    [(1,2), (2,4), (1,2)],
    [(1,2), (2,4), (1,2)],
    [(1,2), (2,4), (1,2)],
    [(1,2), (2,4), (1,2)],
    [(1,2), (2,4), (1,2)],
    [(1,10), (2,4), (1,10)],
    [(1,10), (2,4), (1,10)],
]

col_clues = [
    [(1,24)],
    [(1,24)],
    [(1,2), (2,4), (1,2)],
    [(1,2), (2,4), (1,2)],
    [(1,2), (2,4), (1,2)],
    [(1,2), (2,4), (1,2)],
    [(1,2), (2,4), (1,2)],
    [(1,2), (2,4), (1,2)],
    [(1,2), (3,8), (1,2)],
    [(1,2), (3,8), (1,2)],
    [(2,8), (3,8), (2,8)],
    [(2,8), (3,8), (2,8)],
    [(2,8), (3,8), (2,8)],
    [(2,8), (3,8), (2,8)],
    [(1,2), (3,8), (1,2)],
    [(1,2), (3,8), (1,2)],
    [(1,2), (2,4), (1,2)],
    [(1,2), (2,4), (1,2)],
    [(1,2), (2,4), (1,2)],
    [(1,2), (2,4), (1,2)],
    [(1,2), (2,4), (1,2)],
    [(1,2), (2,4), (1,2)],
    [(1,24)],
    [(1,24)],
]

main_diagonal = [1, 1, 0, 0, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 0, 0, 1, 1]
anti_diagonal = [1, 1, 0, 0, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 0, 0, 1, 1]

def generate_asp_program():
    program_parts = []
    
    program_parts.append("row(0..23).")
    program_parts.append("col(0..23).")
    program_parts.append("color(0..3).")
    program_parts.append("")
    
    for row_idx, clues in enumerate(row_clues):
        for run_idx, (color, length) in enumerate(clues):
            program_parts.append(f"row_clue({row_idx}, {run_idx}, {color}, {length}).")
    program_parts.append("")
    
    for col_idx, clues in enumerate(col_clues):
        for run_idx, (color, length) in enumerate(clues):
            program_parts.append(f"col_clue({col_idx}, {run_idx}, {color}, {length}).")
    program_parts.append("")
    
    for idx, color in enumerate(main_diagonal):
        program_parts.append(f"main_diag({idx}, {color}).")
    program_parts.append("")
    
    for idx, color in enumerate(anti_diagonal):
        program_parts.append(f"anti_diag({idx}, {color}).")
    program_parts.append("")
    
    program_parts.append("1 { cell(R, C, Color) : color(Color) } 1 :- row(R), col(C).")
    program_parts.append("")
    
    program_parts.append(":- main_diag(I, Color), not cell(I, I, Color).")
    program_parts.append("")
    
    program_parts.append(":- anti_diag(I, Color), not cell(I, 23-I, Color).")
    program_parts.append("")
    
    program_parts.append("1 { row_run_pos(R, RunIdx, StartCol) : col(StartCol) } 1 :- row_clue(R, RunIdx, _, _).")
    program_parts.append("")
    
    program_parts.append(":- row_run_pos(R, RunIdx, Start), row_clue(R, RunIdx, _, Len), Start + Len > 24.")
    program_parts.append("")
    
    program_parts.append(":- row_run_pos(R, RunIdx, Start), row_clue(R, RunIdx, ReqColor, Len),")
    program_parts.append("   col(C), C >= Start, C < Start + Len,")
    program_parts.append("   cell(R, C, ActualColor), ActualColor != ReqColor.")
    program_parts.append("")
    
    program_parts.append(":- row_run_pos(R, I1, C1), row_run_pos(R, I2, C2),")
    program_parts.append("   row_clue(R, I1, _, L1), I2 = I1 + 1, C2 < C1 + L1.")
    program_parts.append("")
    
    program_parts.append(":- row_run_pos(R, I1, C1), row_run_pos(R, I2, C2),")
    program_parts.append("   row_clue(R, I1, SameColor, L1), row_clue(R, I2, SameColor, _),")
    program_parts.append("   I1 < I2, C2 < C1 + L1 + 1.")
    program_parts.append("")
    
    program_parts.append("1 { col_run_pos(C, RunIdx, StartRow) : row(StartRow) } 1 :- col_clue(C, RunIdx, _, _).")
    program_parts.append("")
    
    program_parts.append(":- col_run_pos(C, RunIdx, Start), col_clue(C, RunIdx, _, Len), Start + Len > 24.")
    program_parts.append("")
    
    program_parts.append(":- col_run_pos(C, RunIdx, Start), col_clue(C, RunIdx, ReqColor, Len),")
    program_parts.append("   row(R), R >= Start, R < Start + Len,")
    program_parts.append("   cell(R, C, ActualColor), ActualColor != ReqColor.")
    program_parts.append("")
    
    program_parts.append(":- col_run_pos(C, I1, R1), col_run_pos(C, I2, R2),")
    program_parts.append("   col_clue(C, I1, _, L1), I2 = I1 + 1, R2 < R1 + L1.")
    program_parts.append("")
    
    program_parts.append(":- col_run_pos(C, I1, R1), col_run_pos(C, I2, R2),")
    program_parts.append("   col_clue(C, I1, SameColor, L1), col_clue(C, I2, SameColor, _),")
    program_parts.append("   I1 < I2, R2 < R1 + L1 + 1.")
    program_parts.append("")
    
    program_parts.append("in_row_run(R, C) :- row_run_pos(R, RunIdx, Start), row_clue(R, RunIdx, _, Len),")
    program_parts.append("                    col(C), C >= Start, C < Start + Len.")
    program_parts.append("")
    
    program_parts.append("in_col_run(R, C) :- col_run_pos(C, RunIdx, Start), col_clue(C, RunIdx, _, Len),")
    program_parts.append("                    row(R), R >= Start, R < Start + Len.")
    program_parts.append("")
    
    program_parts.append(":- cell(R, C, Color), Color != 0, not in_row_run(R, C).")
    program_parts.append(":- cell(R, C, Color), Color != 0, not in_col_run(R, C).")
    program_parts.append("")
    
    return "\n".join(program_parts)

asp_program = generate_asp_program()

ctl = clingo.Control(["1"])
ctl.add("base", [], asp_program)
ctl.ground([("base", [])])

solution_grid = None

def on_model(model):
    global solution_grid
    solution_grid = [[0 for _ in range(24)] for _ in range(24)]
    for atom in model.symbols(atoms=True):
        if atom.name == "cell" and len(atom.arguments) == 3:
            row = atom.arguments[0].number
            col = atom.arguments[1].number
            color = atom.arguments[2].number
            solution_grid[row][col] = color

result = ctl.solve(on_model=on_model)

if result.satisfiable and solution_grid:
    output = {
        "grid": solution_grid,
        "valid": True,
        "palette": {
            "0": "white",
            "1": "red",
            "2": "green",
            "3": "blue"
        }
    }
    print(json.dumps(output))
else:
    print(json.dumps({"error": "No solution exists", "valid": False}))
