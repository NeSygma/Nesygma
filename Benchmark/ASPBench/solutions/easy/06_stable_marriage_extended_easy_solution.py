import clingo
import json

def generate_asp_program():
    program = """
    man(m1). man(m2). man(m3). man(m4).
    woman(w1). woman(w2). woman(w3). woman(w4).
    
    prefers_man(m1, w1, 1). prefers_man(m1, w2, 2). prefers_man(m1, w3, 3).
    prefers_man(m2, w2, 1). prefers_man(m2, w3, 2). prefers_man(m2, w4, 3).
    prefers_man(m3, w3, 1). prefers_man(m3, w4, 2). prefers_man(m3, w1, 3).
    prefers_man(m4, w4, 1). prefers_man(m4, w1, 2). prefers_man(m4, w2, 3).
    
    prefers_woman(w1, m4, 1). prefers_woman(w1, m1, 2). prefers_woman(w1, m3, 3).
    prefers_woman(w2, m1, 1). prefers_woman(w2, m2, 2). prefers_woman(w2, m4, 3).
    prefers_woman(w3, m2, 1). prefers_woman(w3, m3, 2). prefers_woman(w3, m1, 3).
    prefers_woman(w4, m3, 1). prefers_woman(w4, m4, 2). prefers_woman(w4, m2, 3).
    
    acceptable(M, W) :- prefers_man(M, W, _), prefers_woman(W, M, _).
    
    { matched(M, W) : acceptable(M, W) } 1 :- man(M).
    
    :- matched(M1, W), matched(M2, W), M1 != M2.
    
    man_prefers(M, W) :- acceptable(M, W), not matched(M, _).
    man_prefers(M, W) :- acceptable(M, W), matched(M, W2), W != W2,
                         prefers_man(M, W, R1), prefers_man(M, W2, R2), R1 < R2.
    
    woman_prefers(W, M) :- acceptable(M, W), not matched(_, W).
    woman_prefers(W, M) :- acceptable(M, W), matched(M2, W), M != M2,
                           prefers_woman(W, M, R1), prefers_woman(W, M2, R2), R1 < R2.
    
    :- acceptable(M, W), not matched(M, W), man_prefers(M, W), woman_prefers(W, M).
    
    #show matched/2.
    """
    return program

def solve_stable_marriage():
    ctl = clingo.Control(["0"])
    
    program = generate_asp_program()
    ctl.add("base", [], program)
    ctl.ground([("base", [])])
    
    all_matchings = []
    
    def on_model(model):
        matching = []
        for atom in model.symbols(atoms=True):
            if atom.name == "matched" and len(atom.arguments) == 2:
                man = str(atom.arguments[0])
                woman = str(atom.arguments[1])
                matching.append([man, woman])
        matching.sort()
        all_matchings.append(matching)
    
    result = ctl.solve(on_model=on_model)
    
    if result.satisfiable:
        return {
            "stable_matchings": all_matchings,
            "count": len(all_matchings)
        }
    else:
        return {
            "error": "No stable matching exists",
            "reason": "The problem constraints are unsatisfiable"
        }

solution = solve_stable_marriage()
print(json.dumps(solution, indent=2))
