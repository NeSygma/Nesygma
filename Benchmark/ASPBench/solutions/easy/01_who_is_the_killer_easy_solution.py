import clingo
import json

def solve_agatha_murder():
    ctl = clingo.Control(["1"])
    
    program = """
    person(0, "Agatha").
    person(1, "Butler").
    person(2, "Charles").
    
    victim(0).
    
    1 { killed(X, 0) : person(X, _) } 1.
    
    :- killed(X, Y), not hates(X, Y).
    
    :- killed(X, Y), richer(X, Y).
    
    :- hates(0, Z), hates(2, Z).
    
    hates(0, 0).
    hates(0, 2).
    
    hates(1, X) :- person(X, _), not richer(X, 0).
    
    hates(1, X) :- hates(0, X).
    
    :- person(X, _), not has_someone_not_hated(X).
    has_someone_not_hated(X) :- person(X, _), person(Y, _), not hates(X, Y).
    
    { richer(X, Y) : person(X, _), person(Y, _), X != Y }.
    
    :- richer(X, Y), richer(Y, X).
    
    #show killed/2.
    """
    
    ctl.add("base", [], program)
    ctl.ground([("base", [])])
    
    solution = None
    
    def on_model(m):
        nonlocal solution
        atoms = m.symbols(atoms=True)
        
        killer_id = None
        killer_name = None
        
        for atom in atoms:
            if atom.name == "killed" and len(atom.arguments) == 2:
                killer_id = atom.arguments[0].number
                names = {0: "Agatha", 1: "Butler", 2: "Charles"}
                killer_name = names[killer_id]
        
        if killer_id is not None:
            solution = {
                "killer": killer_id,
                "killer_name": killer_name
            }
    
    result = ctl.solve(on_model=on_model)
    
    if result.satisfiable and solution:
        return solution
    else:
        return {"error": "No solution exists", "reason": "Constraints are unsatisfiable"}

result = solve_agatha_murder()
print(json.dumps(result))
