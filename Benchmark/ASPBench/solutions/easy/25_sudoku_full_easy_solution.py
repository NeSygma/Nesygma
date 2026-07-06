import clingo
import json

def parse_puzzle():
    """Parse the Sudoku puzzle and extract clues"""
    puzzle_str = """
5 3 _ | _ 7 _ | _ _ _
6 _ _ | 1 9 5 | _ _ _
_ 9 8 | _ _ _ | _ 6 _
------+-------+------
8 _ _ | _ 6 _ | _ _ 3
4 _ _ | 8 _ 3 | _ _ 1
7 _ _ | _ 2 _ | _ _ 6
------+-------+------
_ 6 _ | _ _ _ | 2 8 _
_ _ _ | 4 1 9 | _ _ 5
_ _ _ | _ 8 _ | _ 7 9
"""
    
    clues = []
    row = 1
    for line in puzzle_str.strip().split('\n'):
        if '---' in line:
            continue
        line = line.replace('|', ' ')
        values = line.split()
        col = 1
        for val in values:
            if val != '_':
                clues.append((row, col, int(val)))
            col += 1
        row += 1
    
    return clues

def generate_sudoku_asp(clues):
    """Generate ASP program for Sudoku"""
    asp_program = """
row(1..9).
col(1..9).
val(1..9).

box(R, C, B) :- row(R), col(C),
    B = ((R-1)/3)*3 + (C-1)/3 + 1.

"""
    
    for r, c, v in clues:
        asp_program += f"clue({r}, {c}, {v}).\n"
    
    asp_program += """
1 { cell(R, C, V) : val(V) } 1 :- row(R), col(C).

cell(R, C, V) :- clue(R, C, V).

:- row(R), val(V), #count { C : cell(R, C, V) } != 1.

:- col(C), val(V), #count { R : cell(R, C, V) } != 1.

:- val(V), B = 1..9, #count { R, C : cell(R, C, V), box(R, C, B) } != 1.
"""
    
    return asp_program

def solve_sudoku(asp_code):
    """Solve Sudoku using clingo"""
    ctl = clingo.Control(["1"])
    ctl.add("base", [], asp_code)
    ctl.ground([("base", [])])
    
    solution_grid = None
    found_solution = False
    
    def on_model(model):
        nonlocal solution_grid, found_solution
        found_solution = True
        
        grid = [[0 for _ in range(9)] for _ in range(9)]
        
        for atom in model.symbols(atoms=True):
            if atom.name == "cell" and len(atom.arguments) == 3:
                r = atom.arguments[0].number
                c = atom.arguments[1].number
                v = atom.arguments[2].number
                grid[r-1][c-1] = v
        
        solution_grid = grid
    
    result = ctl.solve(on_model=on_model)
    
    if result.satisfiable and found_solution:
        return solution_grid
    else:
        return None

def verify_sudoku(grid, original_clues):
    """Verify that the solution satisfies all Sudoku constraints"""
    clues_preserved = True
    for r, c, v in original_clues:
        if grid[r-1][c-1] != v:
            clues_preserved = False
            break
    
    for row in grid:
        if sorted(row) != list(range(1, 10)):
            return False, clues_preserved
    
    for c in range(9):
        col = [grid[r][c] for r in range(9)]
        if sorted(col) != list(range(1, 10)):
            return False, clues_preserved
    
    for box_r in range(3):
        for box_c in range(3):
            box_vals = []
            for r in range(box_r * 3, box_r * 3 + 3):
                for c in range(box_c * 3, box_c * 3 + 3):
                    box_vals.append(grid[r][c])
            if sorted(box_vals) != list(range(1, 10)):
                return False, clues_preserved
    
    return True, clues_preserved

def main():
    clues = parse_puzzle()
    asp_code = generate_sudoku_asp(clues)
    solution_grid = solve_sudoku(asp_code)
    
    if solution_grid:
        is_valid, clues_preserved = verify_sudoku(solution_grid, clues)
        
        output = {
            "grid": solution_grid,
            "is_valid": is_valid,
            "clues_preserved": clues_preserved
        }
        
        print(json.dumps(output, indent=2))
    else:
        print(json.dumps({"error": "No solution exists"}))

if __name__ == "__main__":
    main()
