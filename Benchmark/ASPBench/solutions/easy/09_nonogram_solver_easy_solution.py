import clingo
import json

def create_asp_program():
    program = """
    row(1..5).
    col(1..5).
    
    row_clue(1, 1, 2).
    row_clue(2, 1, 1).
    row_clue(3, 1, 3).
    row_clue(4, 1, 1).
    row_clue(4, 2, 1).
    row_clue(5, 1, 2).
    
    col_clue(1, 1, 1).
    col_clue(1, 2, 1).
    col_clue(2, 1, 1).
    col_clue(2, 2, 3).
    col_clue(3, 1, 2).
    col_clue(4, 1, 1).
    col_clue(5, 1, 1).
    
    { cell(R, C, 1) } :- row(R), col(C).
    cell(R, C, 0) :- row(R), col(C), not cell(R, C, 1).
    
    1 { row_run_pos(R, Idx, Start) : col(Start) } 1 :- row_clue(R, Idx, _).
    
    :- row_run_pos(R, Idx, Start), row_clue(R, Idx, Len),
       col(C), C >= Start, C < Start + Len,
       cell(R, C, 0).
    
    :- row_run_pos(R, Idx1, Start1), row_run_pos(R, Idx2, Start2),
       row_clue(R, Idx1, Len1), Idx2 = Idx1 + 1,
       Start2 < Start1 + Len1.
    
    :- row_run_pos(R, Idx1, Start1), row_run_pos(R, Idx2, Start2),
       row_clue(R, Idx1, Len1), Idx1 < Idx2,
       Start2 < Start1 + Len1 + 1.
    
    :- row_run_pos(R, Idx, Start), row_clue(R, Idx, Len),
       Start + Len > 6.
    
    in_row_run(R, C) :- row_run_pos(R, Idx, Start), row_clue(R, Idx, Len),
                        col(C), C >= Start, C < Start + Len.
    
    :- cell(R, C, 1), row(R), col(C), not in_row_run(R, C).
    
    1 { col_run_pos(C, Idx, Start) : row(Start) } 1 :- col_clue(C, Idx, _).
    
    :- col_run_pos(C, Idx, Start), col_clue(C, Idx, Len),
       row(R), R >= Start, R < Start + Len,
       cell(R, C, 0).
    
    :- col_run_pos(C, Idx1, Start1), col_run_pos(C, Idx2, Start2),
       col_clue(C, Idx1, Len1), Idx2 = Idx1 + 1,
       Start2 < Start1 + Len1.
    
    :- col_run_pos(C, Idx1, Start1), col_run_pos(C, Idx2, Start2),
       col_clue(C, Idx1, Len1), Idx1 < Idx2,
       Start2 < Start1 + Len1 + 1.
    
    :- col_run_pos(C, Idx, Start), col_clue(C, Idx, Len),
       Start + Len > 6.
    
    in_col_run(R, C) :- col_run_pos(C, Idx, Start), col_clue(C, Idx, Len),
                        row(R), R >= Start, R < Start + Len.
    
    :- cell(R, C, 1), row(R), col(C), not in_col_run(R, C).
    
    #show cell/3.
    """
    return program

def solve_nonogram():
    ctl = clingo.Control(["1"])
    
    program = create_asp_program()
    ctl.add("base", [], program)
    ctl.ground([("base", [])])
    
    solution = None
    
    def on_model(m):
        nonlocal solution
        atoms = m.symbols(atoms=True)
        
        grid = [[0 for _ in range(5)] for _ in range(5)]
        
        for atom in atoms:
            if atom.name == "cell" and len(atom.arguments) == 3:
                row = atom.arguments[0].number - 1
                col = atom.arguments[1].number - 1
                value = atom.arguments[2].number
                grid[row][col] = value
        
        solution = {
            "grid": grid,
            "valid": True
        }
    
    result = ctl.solve(on_model=on_model)
    
    if result.satisfiable:
        return solution
    else:
        return {"error": "No solution exists", "reason": "UNSAT"}

solution = solve_nonogram()
print(json.dumps(solution))
