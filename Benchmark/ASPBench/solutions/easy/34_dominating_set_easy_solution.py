import clingo
import json

vertices = list(range(1, 8))
edges = [
    (1, 2), (1, 3),
    (2, 1), (2, 3), (2, 4),
    (3, 1), (3, 2), (3, 5),
    (4, 2), (4, 6),
    (5, 3), (5, 6), (5, 7),
    (6, 4), (6, 5), (6, 7),
    (7, 5), (7, 6)
]

facts = []
for v in vertices:
    facts.append(f"vertex({v}).")

for v1, v2 in edges:
    facts.append(f"edge({v1},{v2}).")

asp_program = """
% Facts (vertices and edges)
""" + "\n".join(facts) + """

% Choice rule: Select vertices for the dominating set
{ in_domset(V) } :- vertex(V).

% A vertex is dominated if it's in the dominating set
dominated(V) :- in_domset(V).

% A vertex is dominated if it's adjacent to a vertex in the dominating set
dominated(V) :- vertex(V), edge(V, U), in_domset(U).

% Constraint: Every vertex must be dominated
:- vertex(V), not dominated(V).

% Optimization: Minimize the size of the dominating set
#minimize { 1,V : in_domset(V) }.
"""

ctl = clingo.Control(["0"])
ctl.add("base", [], asp_program)
ctl.ground([("base", [])])

solution = None

def on_model(model):
    global solution
    domset = []
    for atom in model.symbols(atoms=True):
        if atom.name == "in_domset" and len(atom.arguments) == 1:
            vertex = atom.arguments[0].number
            domset.append(vertex)
    
    domset.sort()
    solution = {
        "dominating_set": domset,
        "size": len(domset)
    }

result = ctl.solve(on_model=on_model)

if result.satisfiable:
    print(json.dumps(solution))
else:
    print(json.dumps({"error": "No solution exists"}))
