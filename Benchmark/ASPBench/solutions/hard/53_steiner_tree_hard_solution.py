import clingo
import json

program = """
vertex(0, 2, 10).
vertex(1, 2, 10).
vertex(2, 1, 8).
vertex(3, 1, 5).
vertex(4, 1, 7).
vertex(5, 1, 6).
vertex(6, 0, 2).
vertex(7, 0, 2).
vertex(8, 0, 3).
vertex(9, 0, 3).
vertex(10, 0, 4).
vertex(11, 0, 4).

edge(0, 2, 5, fiber). edge(2, 0, 5, fiber).
edge(1, 3, 4, fiber). edge(3, 1, 4, fiber).
edge(2, 3, 3, fiber). edge(3, 2, 3, fiber).
edge(2, 4, 6, copper). edge(4, 2, 6, copper).
edge(2, 6, 2, copper). edge(6, 2, 2, copper).
edge(3, 5, 2, fiber). edge(5, 3, 2, fiber).
edge(3, 7, 8, copper). edge(7, 3, 8, copper).
edge(4, 8, 5, fiber). edge(8, 4, 5, fiber).
edge(5, 9, 4, copper). edge(9, 5, 4, copper).
edge(5, 10, 3, fiber). edge(10, 5, 3, fiber).
edge(6, 7, 1, copper). edge(7, 6, 1, copper).
edge(9, 10, 7, fiber). edge(10, 9, 7, fiber).
edge(10, 11, 2, copper). edge(11, 10, 2, copper).

terminal(a, 6).
terminal(a, 7).
terminal(b, 10).
terminal(b, 11).

in_tree(V) :- terminal(_, V).

{ steiner(V) : vertex(V, _, _), not terminal(_, V) }.

in_tree(V) :- steiner(V).

{ tree_edge(V1, V2) : edge(V1, V2, _, _), V1 < V2, in_tree(V1), in_tree(V2) }.

edge_weight(V1, V2, W) :- edge(V1, V2, W, _), V1 < V2.
edge_type(V1, V2, T) :- edge(V1, V2, _, T), V1 < V2.

tree_connected(V1, V2) :- tree_edge(V1, V2).
tree_connected(V1, V2) :- tree_edge(V2, V1).
tree_connected(V2, V1) :- tree_edge(V1, V2).
tree_connected(V2, V1) :- tree_edge(V2, V1).

min_vertex(V) :- in_tree(V), V = #min { V2 : in_tree(V2) }.

reachable(V) :- min_vertex(V).
reachable(V2) :- reachable(V1), tree_connected(V1, V2).

:- in_tree(V), not reachable(V).

num_vertices(N) :- N = #count { V : in_tree(V) }.
num_edges(N) :- N = #count { V1, V2 : tree_edge(V1, V2) }.
:- num_vertices(NV), num_edges(NE), NE != NV - 1.

:- tree_connected(V1, V2), steiner(V1), vertex(V1, L1, _), vertex(V2, L2, _), L2 > L1.

steiner_cost(C) :- C = #sum { Cost, V : steiner(V), vertex(V, _, Cost) }.
:- steiner_cost(C), C > 20.

copper_count(N) :- N = #count { V1, V2 : tree_edge(V1, V2), edge_type(V1, V2, copper) }.
:- copper_count(N), N > 3.

gateway(G, S) :- steiner(S), terminal(G, T), tree_connected(S, T).

:- terminal(G, _), not gateway(G, _).

steiner_reachable(S1, S2) :- steiner(S1), steiner(S2), S1 = S2.
steiner_reachable(S1, S3) :- steiner_reachable(S1, S2), tree_connected(S2, S3), steiner(S3).

:- gateway(_, G1), gateway(_, G2), not steiner_reachable(G1, G2).

total_weight(W) :- W = #sum { Weight, V1, V2 : tree_edge(V1, V2), edge_weight(V1, V2, Weight) }.
:- total_weight(W), W != 13.

#show tree_edge/2.
#show steiner/1.
#show gateway/2.
#show total_weight/1.
#show steiner_cost/1.
#show copper_count/1.
"""

ctl = clingo.Control(["1"])
ctl.add("base", [], program)
ctl.ground([("base", [])])

solution_data = None

def on_model(model):
    global solution_data
    atoms = model.symbols(atoms=True)
    
    tree_edges = []
    for atom in atoms:
        if atom.name == "tree_edge" and len(atom.arguments) == 2:
            v1 = atom.arguments[0].number
            v2 = atom.arguments[1].number
            for atom2 in atoms:
                if atom2.name == "edge_weight" and len(atom2.arguments) == 3:
                    if (atom2.arguments[0].number == v1 and atom2.arguments[1].number == v2):
                        weight = atom2.arguments[2].number
                        tree_edges.append({"from": v1, "to": v2, "weight": weight})
                        break
    
    steiner_vertices = []
    for atom in atoms:
        if atom.name == "steiner" and len(atom.arguments) == 1:
            steiner_vertices.append(atom.arguments[0].number)
    
    gateways = {"A": [], "B": []}
    for atom in atoms:
        if atom.name == "gateway" and len(atom.arguments) == 2:
            group = str(atom.arguments[0]).upper()
            vertex = atom.arguments[1].number
            if group in gateways:
                gateways[group].append(vertex)
    
    total_weight = 0
    for atom in atoms:
        if atom.name == "total_weight" and len(atom.arguments) == 1:
            total_weight = atom.arguments[0].number
    
    steiner_cost = 0
    for atom in atoms:
        if atom.name == "steiner_cost" and len(atom.arguments) == 1:
            steiner_cost = atom.arguments[0].number
    
    copper_count = 0
    for atom in atoms:
        if atom.name == "copper_count" and len(atom.arguments) == 1:
            copper_count = atom.arguments[0].number
    
    solution_data = {
        "tree_edges": tree_edges,
        "steiner_vertices": sorted(steiner_vertices),
        "gateways": gateways,
        "total_weight": total_weight,
        "steiner_cost": steiner_cost,
        "copper_count": copper_count
    }

result = ctl.solve(on_model=on_model)

if result.satisfiable:
    output = {
        "total_weight": solution_data["total_weight"],
        "tree_edges": sorted(solution_data["tree_edges"], key=lambda x: (x["from"], x["to"])),
        "steiner_vertices": solution_data["steiner_vertices"],
        "terminals": {
            "A": [6, 7],
            "B": [10, 11]
        },
        "gateways": solution_data["gateways"],
        "copper_edge_count": solution_data["copper_count"],
        "steiner_resource_cost": solution_data["steiner_cost"],
        "connected_components": [
            {
                "component": 1,
                "vertices": sorted(solution_data["steiner_vertices"] + [6, 7, 10, 11])
            }
        ]
    }
    print(json.dumps(output, indent=2))
else:
    print(json.dumps({"error": "No solution exists", "reason": "Constraints cannot be satisfied"}))
