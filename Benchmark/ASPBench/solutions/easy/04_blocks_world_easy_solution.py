import clingo
import json

ctl = clingo.Control(["1"])

program = """
block(a; b; c).
location(table; a; b; c).

#const max_time = 3.
time(0..max_time).

on(c, a, 0).
on(a, table, 0).
on(b, table, 0).

:- not on(a, b, max_time).
:- not on(b, c, max_time).
:- not on(c, table, max_time).

clear(B, T) :- block(B), time(T), not on(_, B, T).
clear(table, T) :- time(T).

1 { move(B, From, To, T) : on(B, From, T), clear(B, T), clear(To, T), 
    location(To), From != To, B != To } 1 :- time(T), T < max_time.

on(B, To, T+1) :- move(B, From, To, T).

on(B, L, T+1) :- on(B, L, T), time(T+1), not move(B, L, _, T).

:- on(B, L1, T), on(B, L2, T), L1 != L2.

:- on(B1, L, T), on(B2, L, T), B1 != B2, L != table.

#show move/4.
"""

ctl.add("base", [], program)
ctl.ground([("base", [])])

solution = None

def on_model(m):
    global solution
    atoms = m.symbols(atoms=True)
    
    moves = []
    for atom in atoms:
        if atom.name == "move" and len(atom.arguments) == 4:
            block = str(atom.arguments[0])
            from_loc = str(atom.arguments[1])
            to_loc = str(atom.arguments[2])
            timestep = atom.arguments[3].number
            
            moves.append({
                "step": timestep + 1,
                "action": "move",
                "block": block.upper(),
                "from": from_loc if from_loc == "table" else from_loc.upper(),
                "to": to_loc if to_loc == "table" else to_loc.upper()
            })
    
    moves.sort(key=lambda x: x["step"])
    
    solution = {
        "plan_length": len(moves),
        "actions": moves
    }

result = ctl.solve(on_model=on_model)

if result.satisfiable:
    print(json.dumps(solution, indent=2))
else:
    print(json.dumps({"error": "No solution exists", 
                      "reason": "Problem is unsatisfiable"}))
