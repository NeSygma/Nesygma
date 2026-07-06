import clingo
import json

asp_program = """
vertex(0;1;2;3;4;5;6).

terminal(0).
terminal(5).
terminal(6).

edge(0,1,3). edge(1,0,3).
edge(0,2,5). edge(2,0,5).
edge(1,3,2). edge(3,1,2).
edge(1,4,4). edge(4,1,4).
edge(2,3,1). edge(3,2,1).
edge(2,5,6). edge(5,2,6).
edge(3,4,3). edge(4,3,3).
edge(3,5,3). edge(5,3,3).
edge(3,6,2). edge(6,3,2).
edge(4,5,2). edge(5,4,2).
edge(5,6,4). edge(6,5,4).

{ in_tree(V1, V2) : edge(V1, V2, _), V1 < V2 }.

in_tree_vertex(V) :- in_tree(V, _).
in_tree_vertex(V) :- in_tree(_, V).

:- terminal(T), not in_tree_vertex(T).

root(0).

reachable(V) :- root(V).
reachable(V2) :- reachable(V1), in_tree(V1, V2).
reachable(V1) :- reachable(V2), in_tree(V1, V2).

:- in_tree_vertex(V), not reachable(V).

num_vertices(N) :- N = #count { V : in_tree_vertex(V) }.
num_edges(N) :- N = #count { V1, V2 : in_tree(V1, V2) }.

:- num_vertices(NV), num_edges(NE), NE != NV - 1.

total_weight(W) :- W = #sum { Weight, V1, V2 : in_tree(V1, V2), 
                               edge(V1, V2, Weight) }.

:- total_weight(W), W > 10.

#show in_tree/2.
#show total_weight/1.
"""

ctl = clingo.Control(["1"])
ctl.add("base", [], asp_program)
ctl.ground([("base", [])])

solution_data = None

def on_model(model):
    global solution_data
    
    atoms = model.symbols(atoms=True)
    
    tree_edges = []
    tree_vertices = set()
    total_weight = 0
    
    edge_weights = {}
    for atom in atoms:
        if atom.name == "edge" and len(atom.arguments) == 3:
            e1 = atom.arguments[0].number
            e2 = atom.arguments[1].number
            w = atom.arguments[2].number
            edge_weights[(e1, e2)] = w
    
    for atom in atoms:
        if atom.name == "in_tree" and len(atom.arguments) == 2:
            v1 = atom.arguments[0].number
            v2 = atom.arguments[1].number
            tree_vertices.add(v1)
            tree_vertices.add(v2)
            
            weight = edge_weights.get((v1, v2), edge_weights.get((v2, v1), 0))
            tree_edges.append({"from": v1, "to": v2, "weight": weight})
            total_weight += weight
        
        elif atom.name == "total_weight" and len(atom.arguments) == 1:
            total_weight = atom.arguments[0].number
    
    terminals = [0, 5, 6]
    steiner_vertices = sorted([v for v in tree_vertices if v not in terminals])
    
    connected_components = [{"component": 1, 
                            "vertices": sorted(list(tree_vertices))}]
    
    solution_data = {
        "total_weight": total_weight,
        "tree_edges": sorted(tree_edges, key=lambda x: (x["from"], x["to"])),
        "steiner_vertices": steiner_vertices,
        "terminals": sorted(terminals),
        "connected_components": connected_components
    }

result = ctl.solve(on_model=on_model)

if result.satisfiable:
    print(json.dumps(solution_data, indent=2))
else:
    print(json.dumps({"error": "No solution exists", 
                     "reason": "Problem is unsatisfiable"}))
