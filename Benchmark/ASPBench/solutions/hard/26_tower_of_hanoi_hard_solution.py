import clingo
import json

asp_program = """
#const max_time = 19.

disk(1..4).
peg(a;b;c;d).
time(0..max_time-1).

on_peg(1,a,0).
on_peg(2,a,0).
on_peg(3,a,0).
on_peg(4,a,0).

top(D, P, T) :- on_peg(D, P, T), not blocked(D, P, T).
blocked(D, P, T) :- on_peg(D, P, T), on_peg(D2, P, T), D2 < D.

1 { move(D, P1, P2, T) : top(D, P1, T), peg(P2), P1 != P2 } 1 :- time(T).

:- move(D, _, P2, T), top(D2, P2, T), D > D2.

on_peg(D, P2, T+1) :- move(D, _, P2, T).

on_peg(D, P, T+1) :- on_peg(D, P, T), time(T), T+1 <= max_time, not move(D, P, _, T).

:- on_peg(D, P1, T), on_peg(D, P2, T), P1 != P2.

visited(D, P) :- move(D, _, P, _).

:- disk(D), not visited(D, b).
:- disk(D), not visited(D, c).

:- disk(D), not on_peg(D, d, max_time).

#show move/4.
"""

ctl = clingo.Control(["1"])
ctl.add("base", [], asp_program)
ctl.ground([("base", [])])

solution_moves = []

def on_model(model):
    global solution_moves
    solution_moves = []
    
    for atom in model.symbols(atoms=True):
        if atom.name == "move" and len(atom.arguments) == 4:
            disk = atom.arguments[0].number
            from_peg = str(atom.arguments[1]).upper()
            to_peg = str(atom.arguments[2]).upper()
            step = atom.arguments[3].number
            
            solution_moves.append({
                "disk": disk,
                "from_peg": from_peg,
                "to_peg": to_peg,
                "step": step
            })
    
    solution_moves.sort(key=lambda x: x["step"])

result = ctl.solve(on_model=on_model)

if result.satisfiable:
    formatted_moves = []
    for move in solution_moves:
        formatted_moves.append({
            "step": move["step"] + 1,
            "disk": move["disk"],
            "from_peg": move["from_peg"],
            "to_peg": move["to_peg"]
        })
    
    final_solution = {
        "moves": formatted_moves,
        "total_moves": len(formatted_moves)
    }
    
    print(json.dumps(final_solution, indent=2))
else:
    print(json.dumps({"error": "No solution exists", "reason": "UNSAT"}))
