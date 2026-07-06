import clingo
import json

asp_program = """
general(g1). general(g2). general(g3). general(g4). general(g5). general(g6).

rank(g1, commander). rank(g2, lieutenant). rank(g3, lieutenant).
rank(g4, sergeant). rank(g5, sergeant). rank(g6, sergeant).

weight(g1, 3). weight(g2, 2). weight(g3, 2).
weight(g4, 1). weight(g5, 1). weight(g6, 1).

order(g1, 3). order(g2, 2). order(g3, 2).
order(g4, 1). order(g5, 1). order(g6, 1).

initial(g1, 1). initial(g2, 1). initial(g3, 0).
initial(g4, 0). initial(g5, 1). initial(g6, 1).

trust(g1, g2). trust(g2, g1).

trust_bonus(1).

round(0). round(1). round(2).

value(0). value(1).

2 { traitor(G) : general(G) } 2.

honest(G) :- general(G), not traitor(G).

belief(G, 0, V) :- initial(G, V).

message(From, To, R, V) :- 
    honest(From), general(To), From != To,
    round(R), R > 0, R <= 2,
    belief(From, R-1, V).

message(From, To, R, OppositeV) :- 
    traitor(From), general(To), From != To,
    round(R), R > 0, R <= 2,
    belief(From, R-1, V),
    order(From, OF), order(To, OT), OF >= OT,
    value(OppositeV), OppositeV != V.

message(From, To, R, V) :- 
    traitor(From), general(To), From != To,
    round(R), R > 0, R <= 2,
    belief(From, R-1, V),
    order(From, OF), order(To, OT), OF < OT.

msg_weight(From, To, R, W) :- 
    message(From, To, R, _),
    weight(From, W),
    not trust(To, From).

msg_weight(From, To, R, W + B) :- 
    message(From, To, R, _),
    weight(From, W),
    trust(To, From),
    trust_bonus(B).

weight_for_0(G, R, Sum) :- 
    honest(G), round(R), R > 0, R <= 2,
    Sum = #sum { W, From : message(From, G, R, 0), msg_weight(From, G, R, W) }.

weight_for_1(G, R, Sum) :- 
    honest(G), round(R), R > 0, R <= 2,
    Sum = #sum { W, From : message(From, G, R, 1), msg_weight(From, G, R, W) }.

belief(G, R, 1) :- 
    honest(G), round(R), R > 0, R <= 2,
    weight_for_1(G, R, W1),
    weight_for_0(G, R, W0),
    W1 > W0.

belief(G, R, 0) :- 
    honest(G), round(R), R > 0, R <= 2,
    weight_for_0(G, R, W0),
    weight_for_1(G, R, W1),
    W0 > W1.

belief(G, R, 0) :- 
    honest(G), round(R), R > 0, R <= 2,
    weight_for_0(G, R, W),
    weight_for_1(G, R, W).

belief(G, R, V) :- 
    traitor(G), round(R), R > 0, R <= 2,
    belief(G, R-1, V).

final_consensus(V) :- 
    value(V),
    honest(G) : belief(G, 2, V).

:- #count { V : final_consensus(V) } != 1.

#show traitor/1.
#show belief/3.
#show final_consensus/1.
"""

ctl = clingo.Control(["1"])
ctl.add("base", [], asp_program)
ctl.ground([("base", [])])

solution_found = False
traitors = []
beliefs = {}
consensus = None

def on_model(model):
    global solution_found, traitors, beliefs, consensus
    solution_found = True
    
    for atom in model.symbols(atoms=True):
        if atom.name == "traitor" and len(atom.arguments) == 1:
            traitors.append(str(atom.arguments[0]).upper())
        elif atom.name == "belief" and len(atom.arguments) == 3:
            gen = str(atom.arguments[0]).upper()
            rnd = atom.arguments[1].number
            val = atom.arguments[2].number
            if gen not in beliefs:
                beliefs[gen] = {}
            beliefs[gen][rnd] = val
        elif atom.name == "final_consensus" and len(atom.arguments) == 1:
            consensus = atom.arguments[0].number

result = ctl.solve(on_model=on_model)

if solution_found and result.satisfiable:
    honest_generals = [g for g in ["G1", "G2", "G3", "G4", "G5", "G6"] 
                       if g not in traitors]
    
    final_beliefs = []
    for gen in sorted(honest_generals):
        if gen in beliefs and 2 in beliefs[gen]:
            final_beliefs.append({
                "general": gen,
                "belief": beliefs[gen][2]
            })
    
    output = {
        "consensus_value": consensus,
        "final_beliefs": final_beliefs
    }
    
    print(json.dumps(output, indent=2))
else:
    output = {"error": "No solution exists", 
              "reason": "Could not find valid traitor assignment"}
    print(json.dumps(output, indent=2))
