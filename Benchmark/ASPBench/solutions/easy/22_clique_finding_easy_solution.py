import clingo
import json

def generate_asp_program(vertices, edges):
    """Generate ASP program for maximum clique problem"""
    facts = []
    
    for v in vertices:
        facts.append(f"vertex({v}).")
    
    for u, v in edges:
        facts.append(f"edge({u},{v}).")
        facts.append(f"edge({v},{u}).")
    
    rules = """
{ in_clique(V) } :- vertex(V).

:- in_clique(U), in_clique(V), U < V, not edge(U, V).

#maximize { 1,V : in_clique(V) }.
"""
    
    return "\n".join(facts) + "\n" + rules

def solve_maximum_clique(asp_program):
    """Solve the maximum clique problem using clingo"""
    ctl = clingo.Control()
    ctl.add("base", [], asp_program)
    ctl.ground([("base", [])])
    
    best_solution = None
    best_size = 0
    
    def on_model(model):
        nonlocal best_solution, best_size
        clique_vertices = []
        for atom in model.symbols(atoms=True):
            if atom.name == "in_clique" and len(atom.arguments) == 1:
                vertex = atom.arguments[0].number
                clique_vertices.append(vertex)
        
        if len(clique_vertices) > best_size:
            best_size = len(clique_vertices)
            best_solution = sorted(clique_vertices)
    
    result = ctl.solve(on_model=on_model)
    return result, best_solution, best_size

def format_solution(clique_vertices, edges):
    """Format the solution as required JSON output"""
    if not clique_vertices:
        return {"error": "No clique found"}
    
    clique_edges = []
    edge_set = set(edges + [(v, u) for u, v in edges])
    
    for i in range(len(clique_vertices)):
        for j in range(i + 1, len(clique_vertices)):
            u, v = clique_vertices[i], clique_vertices[j]
            if (u, v) in edge_set:
                clique_edges.append([u, v])
    
    clique_edges.sort()
    
    return {
        "clique": clique_vertices,
        "clique_size": len(clique_vertices),
        "clique_edges": clique_edges
    }

vertices = [0, 1, 2, 3, 4, 5, 6]
edges = [
    (0, 1), (0, 2), (0, 3),
    (1, 2), (1, 3), (1, 4),
    (2, 3), (2, 5),
    (3, 4), (3, 5),
    (4, 5), (4, 6),
    (5, 6)
]

asp_program = generate_asp_program(vertices, edges)
result, clique_vertices, clique_size = solve_maximum_clique(asp_program)

if result.satisfiable:
    solution = format_solution(clique_vertices, edges)
    print(json.dumps(solution))
else:
    print(json.dumps({"error": "No solution exists"}))
