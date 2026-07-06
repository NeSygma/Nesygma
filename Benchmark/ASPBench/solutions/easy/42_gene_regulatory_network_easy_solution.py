import clingo
import json

program = """
gene(g1). gene(g2). gene(g3). gene(g4). gene(g5).

{ active(G) } 1 :- gene(G).
inactive(G) :- gene(G), not active(G).

:- active(g1), active(g2).
:- inactive(g2), inactive(g1).

:- active(g2), active(g1).
:- inactive(g1), inactive(g2).

:- active(g3), inactive(g4).
:- active(g3), inactive(g5).
:- active(g4), active(g5), inactive(g3).

:- inactive(g4).

:- inactive(g5).
"""

ctl = clingo.Control(["0"])
ctl.add("base", [], program)
ctl.ground([("base", [])])

steady_states = []

def on_model(model):
    state = {}
    for atom in model.symbols(atoms=True):
        if atom.name == "active":
            gene_name = str(atom.arguments[0])
            state[gene_name] = 1
        elif atom.name == "inactive":
            gene_name = str(atom.arguments[0])
            state[gene_name] = 0
    
    if len(state) == 5:
        steady_states.append(state)

result = ctl.solve(on_model=on_model)

if result.satisfiable:
    output = {"steady_states": steady_states}
    print(json.dumps(output, indent=2))
else:
    print(json.dumps({"error": "No steady states found"}))
