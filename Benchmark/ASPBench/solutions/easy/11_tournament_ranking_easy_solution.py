import clingo
import json

def solve_tournament_ranking():
    ctl = clingo.Control(["0"])
    
    program = """
    team("A"). team("B"). team("C"). team("D"). team("E").
    
    beat("A", "B").
    beat("B", "C").
    beat("C", "A").
    beat("A", "D").
    beat("D", "E").
    beat("E", "C").
    beat("B", "E").
    beat("D", "C").
    beat("A", "E").
    beat("B", "D").
    
    position(1..5).
    
    1 { rank(T, P) : position(P) } 1 :- team(T).
    1 { rank(T, P) : team(T) } 1 :- position(P).
    
    violation(X, Y) :- beat(X, Y), rank(X, PX), rank(Y, PY), PY < PX.
    
    #minimize { 1,X,Y : violation(X,Y) }.
    """
    
    ctl.add("base", [], program)
    ctl.ground([("base", [])])
    
    best_solution = None
    best_violations = float('inf')
    
    def on_model(m):
        nonlocal best_solution, best_violations
        atoms = m.symbols(atoms=True)
        
        ranking_dict = {}
        violations_set = set()
        
        for atom in atoms:
            if atom.name == "rank" and len(atom.arguments) == 2:
                team = str(atom.arguments[0]).strip('"')
                position = atom.arguments[1].number
                ranking_dict[position] = team
            elif atom.name == "violation" and len(atom.arguments) == 2:
                winner = str(atom.arguments[0]).strip('"')
                loser = str(atom.arguments[1]).strip('"')
                violations_set.add((winner, loser))
        
        ranking = [ranking_dict[i] for i in sorted(ranking_dict.keys())]
        num_violations = len(violations_set)
        
        if num_violations < best_violations:
            best_violations = num_violations
            best_solution = {
                "ranking": ranking,
                "violations": num_violations,
                "valid": len(ranking) == 5 and len(set(ranking)) == 5
            }
    
    result = ctl.solve(on_model=on_model)
    
    if result.satisfiable and best_solution:
        return best_solution
    else:
        return {"error": "No solution exists", "reason": "Problem is UNSAT"}

solution = solve_tournament_ranking()
print(json.dumps(solution))
