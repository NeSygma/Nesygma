import clingo
import json

program = """
vertex(1..8).

edge(1,2). edge(2,1).
edge(1,3). edge(3,1).
edge(1,4). edge(4,1).
edge(2,5). edge(5,2).
edge(3,6). edge(6,3).
edge(3,7). edge(7,3).
edge(4,8). edge(8,4).
edge(5,6). edge(6,5).
edge(6,7). edge(7,6).
edge(7,8). edge(8,7).

{ in_set(V) } :- vertex(V).

:- in_set(V1), in_set(V2), edge(V1, V2).

#maximize { 1,V : in_set(V) }.
"""

ctl = clingo.Control(["0"])
ctl.add("base", [], program)
ctl.ground([("base", [])])

solution = None

def on_model(model):
    global solution
    independent_set = []
    for atom in model.symbols(atoms=True):
        if atom.name == "in_set" and len(atom.arguments) == 1:
            vertex = atom.arguments[0].number
            independent_set.append(vertex)
    
    independent_set.sort()
    
    solution = {
        "independent_set": independent_set,
        "size": len(independent_set)
    }

result = ctl.solve(on_model=on_model)

if result.satisfiable:
    print(json.dumps(solution))
else:
    print(json.dumps({"error": "No solution exists", "reason": "Problem is unsatisfiable"}))
