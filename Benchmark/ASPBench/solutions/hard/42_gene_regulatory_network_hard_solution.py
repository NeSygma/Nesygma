import clingo
import json

program = """
gene("master_reg").
gene("m1_g1"). gene("m1_g2"). gene("m1_g3").
gene("m2_g1"). gene("m2_g2"). gene("m2_g3").
gene("reporter").

module1("m1_g1"). module1("m1_g2"). module1("m1_g3").
module2("m2_g1"). module2("m2_g2"). module2("m2_g3").

{ active(G) } :- gene(G).

inactive(G) :- gene(G), not active(G).

m1_count(N) :- N = #count { G : active(G), module1(G) }.
m2_count(N) :- N = #count { G : active(G), module2(G) }.

:- active("master_reg"), m1_count(N1), m2_count(N2), N1 != N2.
:- m1_count(N), m2_count(N), inactive("master_reg").

:- inactive("master_reg"), active("m1_g1"), active("m1_g2").
:- inactive("master_reg"), inactive("m1_g1"), inactive("m1_g2").

:- inactive("master_reg"), active("m1_g2"), active("m1_g3").
:- inactive("master_reg"), inactive("m1_g2"), inactive("m1_g3").

:- inactive("master_reg"), inactive("m1_g3").

:- active("master_reg"), active("m1_g1").
:- active("master_reg"), active("m1_g2").
:- active("master_reg"), active("m1_g3").

:- inactive("master_reg"), active("m2_g1"), active("m1_g1").
:- inactive("master_reg"), active("m2_g1"), active("m1_g2").
:- inactive("master_reg"), inactive("m2_g1"), inactive("m1_g1"), 
   inactive("m1_g2").

:- inactive("master_reg"), active("m2_g2"), m1_count(N), N != 2.
:- inactive("master_reg"), inactive("m2_g2"), m1_count(2).

:- inactive("master_reg"), active("m2_g3"), inactive("m2_g1").
:- inactive("master_reg"), active("m2_g3"), active("m2_g2").
:- inactive("master_reg"), inactive("m2_g3"), active("m2_g1"), 
   inactive("m2_g2").

:- active("master_reg"), active("m2_g1"), active("m2_g2").
:- active("master_reg"), inactive("m2_g1"), inactive("m2_g2").

:- active("master_reg"), active("m2_g2"), active("m2_g3").
:- active("master_reg"), inactive("m2_g2"), inactive("m2_g3").

:- active("master_reg"), active("m2_g3"), active("m2_g1").
:- active("master_reg"), inactive("m2_g3"), inactive("m2_g1").

m2_inactive_count(N) :- N = #count { G : inactive(G), module2(G) }.

:- active("reporter"), m2_inactive_count(N), N < 2.
:- m2_inactive_count(N), N >= 2, inactive("reporter").

#show active/1.
"""

ctl = clingo.Control(["0"])
ctl.add("base", [], program)
ctl.ground([("base", [])])

steady_states = []

def on_model(model):
    state = {}
    genes = ["master_reg", "m1_g1", "m1_g2", "m1_g3", 
             "m2_g1", "m2_g2", "m2_g3", "reporter"]
    for gene in genes:
        state[gene] = 0
    
    for atom in model.symbols(atoms=True):
        if atom.name == "active" and len(atom.arguments) == 1:
            gene_name = str(atom.arguments[0]).strip('"')
            state[gene_name] = 1
    
    steady_states.append(state)

result = ctl.solve(on_model=on_model)

if result.satisfiable:
    output = {"steady_states": steady_states}
    print(json.dumps(output, indent=2))
else:
    print(json.dumps({"error": "No solution exists", 
                      "reason": "No steady states found"}))
