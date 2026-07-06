import clingo
import json

asp_program = """
disk(1..4).
peg(a;b;c).

time(0..15).
action_time(0..14).

on_peg(1, a, 0).
on_peg(2, a, 0).
on_peg(3, a, 0).
on_peg(4, a, 0).

top(D, P, T) :- on_peg(D, P, T), not on_peg(D2, P, T) : disk(D2), D2 < D.

1 { move(D, P1, P2, T) : top(D, P1, T), peg(P2), P1 != P2 } 1 :- action_time(T).

:- move(D, _, P2, T), top(D2, P2, T), D > D2.

on_peg(D, P2, T+1) :- move(D, _, P2, T).

on_peg(D, P, T+1) :- on_peg(D, P, T), time(T+1), not move(D, P, _, T).

:- on_peg(D, P1, T), on_peg(D, P2, T), P1 != P2.

:- disk(D), not on_peg(D, c, 15).
"""

ctl = clingo.Control(["1"])
ctl.add("base", [], asp_program)
ctl.ground([("base", [])])

solution_moves = []
found_solution = False

def on_model(model):
    global solution_moves, found_solution
    found_solution = True
    
    moves = []
    for atom in model.symbols(atoms=True):
        if atom.name == "move" and len(atom.arguments) == 4:
            disk = atom.arguments[0].number
            from_peg = str(atom.arguments[1]).upper()
            to_peg = str(atom.arguments[2]).upper()
            time_step = atom.arguments[3].number
            moves.append({
                "disk": disk,
                "from_peg": from_peg,
                "to_peg": to_peg,
                "time": time_step
            })
    
    moves.sort(key=lambda x: x["time"])
    solution_moves = moves

result = ctl.solve(on_model=on_model)

if result.satisfiable and found_solution:
    output = {
        "moves": [],
        "total_moves": len(solution_moves),
        "is_optimal": len(solution_moves) == 15
    }
    
    for i, move in enumerate(solution_moves, 1):
        output["moves"].append({
            "step": i,
            "disk": move["disk"],
            "from_peg": move["from_peg"],
            "to_peg": move["to_peg"]
        })
    
    print(json.dumps(output, indent=2))
else:
    print(json.dumps({"error": "No solution exists", "reason": "UNSAT"}))
