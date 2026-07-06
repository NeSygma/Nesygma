import clingo
import json

def solve_queen_domination():
    ctl = clingo.Control(["1"])
    
    program = """
    row(0..7).
    col(0..7).
    cell(R, C) :- row(R), col(C).
    
    { queen(R, C) : cell(R, C) }.
    
    dominated(R, C) :- queen(R, C).
    dominated(R, C) :- queen(R, C2), cell(R, C), col(C2).
    dominated(R, C) :- queen(R2, C), cell(R, C), row(R2).
    dominated(R, C) :- queen(R2, C2), cell(R, C), R - C == R2 - C2.
    dominated(R, C) :- queen(R2, C2), cell(R, C), R + C == R2 + C2.
    
    :- cell(R, C), not dominated(R, C).
    :- #count { R, C : queen(R, C) } > 5.
    
    #minimize { 1, R, C : queen(R, C) }.
    """
    
    ctl.add("base", [], program)
    ctl.ground([("base", [])])
    
    solution = None
    
    def on_model(model):
        nonlocal solution
        queens = []
        dominated_squares = []
        
        for atom in model.symbols(atoms=True):
            if atom.name == "queen" and len(atom.arguments) == 2:
                r = atom.arguments[0].number
                c = atom.arguments[1].number
                queens.append([r, c])
            elif atom.name == "dominated" and len(atom.arguments) == 2:
                r = atom.arguments[0].number
                c = atom.arguments[1].number
                dominated_squares.append([r, c])
        
        queens.sort()
        dominated_squares.sort()
        
        solution = {
            "queens": queens,
            "num_queens": len(queens),
            "dominated_squares": dominated_squares
        }
    
    result = ctl.solve(on_model=on_model)
    
    if result.satisfiable:
        return solution
    else:
        return {"error": "No solution exists", 
                "reason": "Could not find valid queen placement"}

solution = solve_queen_domination()
print(json.dumps(solution, indent=2))
