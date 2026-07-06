import clingo
import json

program = """
vertex(1..18).

edge(1,2). edge(2,1).
edge(1,4). edge(4,1).
edge(1,5). edge(5,1).
edge(2,4). edge(4,2).
edge(2,5). edge(5,2).
edge(3,4). edge(4,3).
edge(3,9). edge(9,3).
edge(4,5). edge(5,4).
edge(4,18). edge(18,4).
edge(6,7). edge(7,6).
edge(6,9). edge(9,6).
edge(6,10). edge(10,6).
edge(7,9). edge(9,7).
edge(8,9). edge(9,8).
edge(8,14). edge(14,8).
edge(9,10). edge(10,9).
edge(11,12). edge(12,11).
edge(11,14). edge(14,11).
edge(12,14). edge(14,12).
edge(13,14). edge(14,13).
edge(13,17). edge(17,13).
edge(15,16). edge(16,15).
edge(15,17). edge(17,15).
edge(16,17). edge(17,16).
edge(17,18). edge(18,17).

vertex_type(1, "c"). vertex_type(5, "c"). vertex_type(10, "c"). 
vertex_type(15, "c").
vertex_type(2, "s"). vertex_type(6, "s"). vertex_type(7, "s"). 
vertex_type(11, "s"). vertex_type(12, "s"). vertex_type(16, "s").
vertex_type(3, "r"). vertex_type(8, "r"). vertex_type(13, "r"). 
vertex_type(18, "r").

cost(4, 2). cost(9, 2).
cost(14, 3). cost(17, 3).
cost(1, 5). cost(2, 5). cost(3, 5). cost(5, 5). 
cost(6, 5). cost(7, 5). cost(8, 5).
cost(10, 8). cost(11, 8). cost(12, 8). cost(13, 8). 
cost(15, 8). cost(16, 8). cost(18, 8).

{ in_set(V) } :- vertex(V).

:- in_set(V1), in_set(V2), edge(V1, V2).

dominated(V) :- in_set(V).
dominated(V) :- vertex_type(V, "c"), edge(V, N), in_set(N).
dominated(V) :- vertex_type(V, "s"), edge(V, N), in_set(N).
dominated(V) :- vertex_type(V, "r"), 
    #count { N : edge(V, N), in_set(N) } >= 2.

:- vertex(V), not dominated(V).

total_cost(C) :- C = #sum { Cost, V : in_set(V), cost(V, Cost) }.

:- total_cost(C), C > 10.
:- total_cost(C), C != 10.
"""

ctl = clingo.Control(["1"])
ctl.add("base", [], program)
ctl.ground([("base", [])])

solution_data = None

def on_model(model):
    global solution_data
    dominating_set = []
    total_cost = 0
    
    for atom in model.symbols(atoms=True):
        if atom.name == "in_set" and len(atom.arguments) == 1:
            vertex = atom.arguments[0].number
            dominating_set.append(vertex)
        elif atom.name == "total_cost" and len(atom.arguments) == 1:
            total_cost = atom.arguments[0].number
    
    dominating_set.sort()
    solution_data = {
        "dominating_set": dominating_set,
        "total_cost": total_cost
    }

result = ctl.solve(on_model=on_model)

if result.satisfiable and solution_data:
    print(json.dumps(solution_data))
else:
    print(json.dumps({"error": "No solution exists"}))
