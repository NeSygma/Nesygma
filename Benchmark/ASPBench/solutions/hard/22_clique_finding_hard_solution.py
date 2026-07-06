import clingo
import json

vertices = [
    (0, "alpha", 20), (1, "alpha", 20), (2, "alpha", 15), (3, "alpha", 20),
    (4, "beta", 30), (5, "alpha", 15), (6, "beta", 30), (7, "beta", 30),
    (8, "beta", 18), (9, "delta", 10), (10, "delta", 10), (11, "beta", 12),
    (12, "gamma", 25), (13, "gamma", 25), (14, "gamma", 20), (15, "delta", 5),
    (16, "delta", 5), (17, "gamma", 19), (18, "alpha", 40), (19, "beta", 40)
]

edges = [
    (0,1), (0,3), (0,4), (0,6), (0,7), (0,9), (0,10),
    (1,3), (1,4), (1,6), (1,7), (1,9),
    (2,5), (2,8), (2,11), (2,14), (2,17), (2,18),
    (3,4), (3,6), (3,7), (3,9),
    (4,6), (4,7), (4,9),
    (5,8), (5,11), (5,14), (5,17), (5,19),
    (6,7), (6,9),
    (7,9),
    (8,11), (8,14), (8,17),
    (11,14), (11,17),
    (12,13),
    (14,17),
    (15,16)
]

def generate_asp_facts():
    facts = []
    for v, vtype, weight in vertices:
        facts.append(f'vertex({v}, "{vtype}", {weight}).')
    for v1, v2 in edges:
        if v1 < v2:
            facts.append(f'edge({v1}, {v2}).')
        else:
            facts.append(f'edge({v2}, {v1}).')
    return "\n".join(facts)

asp_program = """
{ in_clique(V) } :- vertex(V, _, _).

:- in_clique(V1), in_clique(V2), V1 < V2, not edge(V1, V2).

:- vertex(_, Type, _), #count { V : in_clique(V), vertex(V, Type, _) } > 2.

:- #sum { W, V : in_clique(V), vertex(V, _, W) } > 100.

#maximize { 1, V : in_clique(V) }.
"""

ctl = clingo.Control(["0"])
full_program = generate_asp_facts() + "\n" + asp_program
ctl.add("base", [], full_program)
ctl.ground([("base", [])])

solution_data = None
best_size = 0

def on_model(model):
    global solution_data, best_size
    clique_vertices = []
    vertex_info = {}
    
    for atom in model.symbols(atoms=True):
        if atom.name == "in_clique" and len(atom.arguments) == 1:
            v = atom.arguments[0].number
            clique_vertices.append(v)
    
    if len(clique_vertices) < best_size:
        return
    
    best_size = len(clique_vertices)
    
    for v, vtype, weight in vertices:
        vertex_info[v] = {"type": vtype, "weight": weight}
    
    clique_vertices.sort()
    
    clique_edges = []
    for i, v1 in enumerate(clique_vertices):
        for v2 in clique_vertices[i+1:]:
            edge_tuple = (min(v1, v2), max(v1, v2))
            if edge_tuple in edges:
                clique_edges.append([v1, v2])
    
    total_weight = sum(vertex_info[v]["weight"] for v in clique_vertices)
    
    type_dist = {}
    for v in clique_vertices:
        vtype = vertex_info[v]["type"]
        type_dist[vtype] = type_dist.get(vtype, 0) + 1
    
    solution_data = {
        "clique": clique_vertices,
        "clique_size": len(clique_vertices),
        "clique_edges": clique_edges,
        "clique_total_weight": total_weight,
        "clique_type_distribution": type_dist
    }

result = ctl.solve(on_model=on_model)

if result.satisfiable and solution_data:
    print(json.dumps(solution_data, indent=2))
else:
    print(json.dumps({"error": "No solution exists"}))
