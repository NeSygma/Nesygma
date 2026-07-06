import clingo
import json

def generate_graph_facts():
    """Generate all edge facts with weights and forbidden edges"""
    facts = []
    forbidden = set()
    
    facts.append("vertex(0..99).")
    
    for i in range(99):
        facts.append(f"edge({i},{i+1},1).")
    
    for N in range(24):
        B = 2 + 4*N
        if B+3 <= 99:
            facts.append(f"edge({B},{B+2},3).")
            facts.append(f"edge({B+2},{B+1},3).")
            facts.append(f"edge({B+1},{B+3},3).")
    
    for N in range(25):
        S = 4*N
        if S+2 <= 99:
            facts.append(f"edge({S},{S+2},4).")
    
    for N in range(24):
        T = 1 + 4*N
        if T+3 <= 99:
            facts.append(f"edge({T},{T+3},5).")
    
    for K in range(20):
        U = 5*K
        if U+4 <= 99:
            facts.append(f"edge({U},{U+4},6).")
    
    forbidden.add((0, 2))
    forbidden.add((1, 3))
    
    for N in range(12):
        F = 2 + 8*N
        if F+2 <= 99:
            forbidden.add((F, F+2))
    
    for N in range(13):
        G = 8*N
        if G+2 <= 99:
            forbidden.add((G, G+2))
    
    for N in range(12):
        H = 1 + 8*N
        if H+3 <= 99:
            forbidden.add((H, H+3))
    
    for M in range(10):
        L = 10*M + 5
        if L+4 <= 99:
            forbidden.add((L, L+4))
    
    for (u, v) in forbidden:
        facts.append(f"forbidden({u},{v}).")
    
    return "\n".join(facts)

def reconstruct_path(edges):
    """Reconstruct ordered path from list of edges"""
    adj = {}
    for u, v in edges:
        adj[u] = v
    
    path = [0]
    current = 0
    while current in adj:
        current = adj[current]
        path.append(current)
    
    return path

def solve_hamiltonian_paths():
    """Solve for all minimum-cost Hamiltonian paths"""
    
    ctl = clingo.Control(["0"])
    
    graph_facts = generate_graph_facts()
    ctl.add("base", [], graph_facts)
    
    program = """
    1 { in_path(U,V) : edge(U,V,_), not forbidden(U,V) } 1 :- vertex(V), V != 0.
    1 { in_path(U,V) : edge(U,V,_), not forbidden(U,V) } 1 :- vertex(U), U != 99.
    
    reached(0).
    reached(V) :- reached(U), in_path(U,V).
    
    :- vertex(V), not reached(V).
    
    total_cost(C) :- C = #sum { W,U,V : in_path(U,V), edge(U,V,W) }.
    
    :- total_cost(C), C != 99.
    """
    
    ctl.add("base", [], program)
    ctl.ground([("base", [])])
    
    all_paths = []
    min_cost = None
    
    def on_model(model):
        nonlocal min_cost
        path_edges = []
        cost = None
        
        for atom in model.symbols(atoms=True):
            if atom.name == "in_path" and len(atom.arguments) == 2:
                u = atom.arguments[0].number
                v = atom.arguments[1].number
                path_edges.append((u, v))
            elif atom.name == "total_cost" and len(atom.arguments) == 1:
                cost = atom.arguments[0].number
        
        if cost is not None:
            min_cost = cost
        
        if path_edges:
            path = reconstruct_path(path_edges)
            all_paths.append(path)
    
    result = ctl.solve(on_model=on_model)
    
    return all_paths, min_cost, result.satisfiable

paths, cost, satisfiable = solve_hamiltonian_paths()

output = {
    "paths": paths,
    "count": len(paths),
    "exists": satisfiable,
    "min_cost": cost
}

print(json.dumps(output))
