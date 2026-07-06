
import clingo
import json

asp_program = """
vertex(0). vertex(1). vertex(2). vertex(3). vertex(4). vertex(5). vertex(6). vertex(7).
vertex(8). vertex(9). vertex(10). vertex(11). vertex(12). vertex(13). vertex(14). vertex(15).

cost(2, 3). cost(10, 3). cost(14, 3).
cost(0, 1). cost(1, 1). cost(3, 1). cost(4, 1). cost(5, 1). cost(6, 1). cost(7, 1).
cost(8, 1). cost(9, 1). cost(11, 1). cost(12, 1). cost(13, 1). cost(15, 1).

standard_edge(1, 3). standard_edge(1, 4). standard_edge(2, 6). standard_edge(3, 7).
standard_edge(4, 8). standard_edge(5, 11). standard_edge(6, 7). standard_edge(7, 12).
standard_edge(8, 12). standard_edge(11, 13). standard_edge(12, 13). standard_edge(13, 14).

heavy_edge(0, 5). heavy_edge(9, 10). heavy_edge(14, 15).

master(0). master(15).

antagonistic(1, 2). antagonistic(8, 9).

{ selected(V) } :- vertex(V).

:- standard_edge(U, V), not selected(U), not selected(V).

covered_heavy(U, V) :- heavy_edge(U, V), selected(U), selected(V).
covered_heavy(U, V) :- heavy_edge(U, V), master(U), selected(U).
covered_heavy(U, V) :- heavy_edge(U, V), master(V), selected(V).

:- heavy_edge(U, V), not covered_heavy(U, V).

:- antagonistic(U, V), selected(U), selected(V).

total_cost(C) :- C = #sum { Cost, V : selected(V), cost(V, Cost) }.

:- total_cost(C), C > 12.

#minimize { Cost, V : selected(V), cost(V, Cost) }.
"""

ctl = clingo.Control(["1"])
ctl.add("base", [], asp_program)
ctl.ground([("base", [])])

solution_data = None

def on_model(model):
    global solution_data
    vertex_cover = []
    total_cost = 0
    
    for atom in model.symbols(atoms=True):
        if atom.name == "selected" and len(atom.arguments) == 1:
            vertex = int(str(atom.arguments[0]))
            vertex_cover.append(vertex)
        elif atom.name == "total_cost" and len(atom.arguments) == 1:
            total_cost = int(str(atom.arguments[0]))
    
    vertex_cover.sort()
    solution_data = {
        "vertex_cover": vertex_cover,
        "total_cost": total_cost
    }

result = ctl.solve(on_model=on_model)

if result.satisfiable and solution_data:
    print(json.dumps(solution_data))
else:
    print(json.dumps({"error": "No solution exists", 
                      "reason": "Could not find valid vertex cover"}))
