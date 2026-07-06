import clingo
import json

program = """
vertex(1). vertex(2). vertex(3). vertex(4). vertex(5). vertex(6).

edge(1, 2). edge(1, 3).
edge(2, 4). edge(2, 5).
edge(3, 4). edge(3, 6).
edge(4, 2). edge(4, 5).
edge(5, 3). edge(5, 6).
edge(6, 1). edge(6, 4).

{ removed(V) : vertex(V) }.

active(V) :- vertex(V), not removed(V).

active_edge(V1, V2) :- edge(V1, V2), active(V1), active(V2).

1 { level(V, L) : L = 0..5 } 1 :- active(V).

:- active_edge(V1, V2), level(V1, L1), level(V2, L2), L1 >= L2.

#minimize { 1,V : removed(V) }.
"""

ctl = clingo.Control(["0"])
ctl.add("base", [], program)
ctl.ground([("base", [])])

solution_data = None

def on_model(model):
    global solution_data
    
    removed_vertices = []
    active_vertices = []
    
    for atom in model.symbols(atoms=True):
        if atom.name == "removed" and len(atom.arguments) == 1:
            vertex = atom.arguments[0].number
            removed_vertices.append(vertex)
        elif atom.name == "active" and len(atom.arguments) == 1:
            vertex = atom.arguments[0].number
            active_vertices.append(vertex)
    
    removed_vertices.sort()
    active_vertices.sort()
    
    solution_data = {
        "feedback_set": removed_vertices,
        "size": len(removed_vertices),
        "remaining_vertices": active_vertices
    }

result = ctl.solve(on_model=on_model)

if result.satisfiable and solution_data:
    print(json.dumps(solution_data))
else:
    print(json.dumps({"error": "No solution exists"}))
