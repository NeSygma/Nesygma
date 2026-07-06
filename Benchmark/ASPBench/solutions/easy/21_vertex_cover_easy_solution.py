import clingo
import json

def solve_vertex_cover():
    ctl = clingo.Control(["1"])
    
    program = """
    vertex(0..5).
    
    edge(0,1). edge(0,2). edge(1,3). edge(2,3).
    edge(2,4). edge(3,5). edge(4,5). edge(1,5).
    
    { in_cover(V) } :- vertex(V).
    
    :- edge(U,V), not in_cover(U), not in_cover(V).
    
    covered(U,V) :- edge(U,V), in_cover(U).
    covered(U,V) :- edge(U,V), in_cover(V).
    
    cover_size(N) :- N = #count { V : in_cover(V) }.
    :- cover_size(N), N > 3.
    """
    
    ctl.add("base", [], program)
    ctl.ground([("base", [])])
    
    solution = None
    
    def on_model(model):
        nonlocal solution
        atoms = model.symbols(atoms=True)
        
        vertex_cover = []
        covered_edges = set()
        
        for atom in atoms:
            if atom.name == "in_cover" and len(atom.arguments) == 1:
                vertex = atom.arguments[0].number
                vertex_cover.append(vertex)
            elif atom.name == "covered" and len(atom.arguments) == 2:
                u = atom.arguments[0].number
                v = atom.arguments[1].number
                if u < v:
                    covered_edges.add((u, v))
                else:
                    covered_edges.add((v, u))
        
        vertex_cover.sort()
        covered_edges_list = sorted(list(covered_edges))
        
        solution = {
            "vertex_cover": vertex_cover,
            "cover_size": len(vertex_cover),
            "covered_edges": covered_edges_list
        }
    
    result = ctl.solve(on_model=on_model)
    
    if result.satisfiable:
        return solution
    else:
        return {"error": "No solution exists", "reason": "Problem is UNSAT"}

solution = solve_vertex_cover()
print(json.dumps(solution, indent=2))
