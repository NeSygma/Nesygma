import clingo
import json

def solve_argumentation_framework():
    ctl = clingo.Control(["0"])
    
    program = """
    arg(a1). arg(a2). arg(a3). arg(a4). arg(a5). arg(a6).
    arg(a7). arg(a8). arg(a9). arg(a10). arg(a11). arg(a12).
    arg(a13). arg(a14). arg(a15). arg(a16).
    
    level(a1, 1). level(a2, 1). level(a3, 1). level(a4, 1). level(a5, 1). level(a6, 1).
    level(a7, 2). level(a8, 2). level(a9, 2). level(a10, 2). level(a11, 2). level(a12, 2).
    level(a13, 3). level(a14, 3). level(a15, 3). level(a16, 3).
    
    strong_attack(a2, a1). strong_attack(a9, a8). strong_attack(a14, a13). strong_attack(a15, a16).
    strong_attack(a1, a14). strong_attack(a16, a15). strong_attack(a1, a3). strong_attack(a1, a4).
    strong_attack(a13, a7). strong_attack(a13, a10). strong_attack(a3, a5). strong_attack(a5, a3).
    
    weak_attack(a8, a2). weak_attack(a13, a9). weak_attack(a8, a5). weak_attack(a8, a6).
    weak_attack(a16, a11). weak_attack(a16, a12). weak_attack(a2, a7). weak_attack(a10, a13).
    
    successful_attack(A, B) :- strong_attack(A, B).
    successful_attack(A, B) :- weak_attack(A, B), level(A, LA), level(B, LB), LA > LB.
    
    { in_ext(A) } :- arg(A).
    
    :- in_ext(A), in_ext(B), successful_attack(A, B).
    
    attacked_by_ext(B) :- in_ext(A), successful_attack(A, B).
    
    :- in_ext(A), successful_attack(B, A), not attacked_by_ext(B).
    """
    
    ctl.add("base", [], program)
    ctl.ground([("base", [])])
    
    admissible_sets = []
    
    def on_model(model):
        extension = set()
        for atom in model.symbols(atoms=True):
            if atom.name == "in_ext" and len(atom.arguments) == 1:
                arg_name = str(atom.arguments[0])
                extension.add(arg_name)
        admissible_sets.append(extension)
    
    result = ctl.solve(on_model=on_model)
    
    if not result.satisfiable:
        return {"error": "No solution exists", "reason": "No admissible sets found"}
    
    preferred_extensions = []
    for ext1 in admissible_sets:
        is_maximal = True
        for ext2 in admissible_sets:
            if ext1 < ext2:
                is_maximal = False
                break
        if is_maximal:
            preferred_extensions.append(sorted(list(ext1)))
    
    return {
        "hierarchical_stable_extensions": preferred_extensions
    }

if __name__ == "__main__":
    result = solve_argumentation_framework()
    print(json.dumps(result))
