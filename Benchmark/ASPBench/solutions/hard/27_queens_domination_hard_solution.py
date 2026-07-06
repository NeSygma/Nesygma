import clingo
import json

def solve_queen_domination():
    ctl = clingo.Control(["1"])
    
    program = """
    row(0..8).
    col(0..8).
    
    { queen(R, C) : row(R), col(C) }.
    
    dominated(R, C) :- queen(R, C).
    dominated(R, C) :- queen(R, C2), row(R), col(C), col(C2).
    dominated(R, C) :- queen(R2, C), row(R), col(C), row(R2).
    dominated(R, C) :- queen(R2, C2), row(R), col(C), R - C == R2 - C2.
    dominated(R, C) :- queen(R2, C2), row(R), col(C), R + C == R2 + C2.
    
    :- row(R), col(C), not dominated(R, C).
    :- #count { R, C : queen(R, C) } != 5.
    """
    
    ctl.add("base", [], program)
    ctl.ground([("base", [])])
    
    solution = None
    
    def on_model(m):
        nonlocal solution
        queens = []
        for atom in m.symbols(atoms=True):
            if atom.name == "queen" and len(atom.arguments) == 2:
                row = atom.arguments[0].number
                col = atom.arguments[1].number
                queens.append([row, col])
        queens.sort()
        solution = {"queens": queens}
    
    result = ctl.solve(on_model=on_model)
    
    if result.satisfiable:
        return solution
    else:
        return {"error": "No solution exists"}

solution = solve_queen_domination()
print(json.dumps(solution))
