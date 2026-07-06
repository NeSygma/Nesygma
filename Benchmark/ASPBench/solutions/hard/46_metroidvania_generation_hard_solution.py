import clingo
import json

asp_program = """
% ===== FACTS =====
room("Start"). room("Goal").
room("R1"). room("R2"). room("R3"). room("R4"). room("R5").
room("R6"). room("R7"). room("R8"). room("R9"). room("R10").

regular_room("R1"). regular_room("R2"). regular_room("R3"). regular_room("R4"). regular_room("R5").
regular_room("R6"). regular_room("R7"). regular_room("R8"). regular_room("R9"). regular_room("R10").

item("RedKey"). item("BlueKey"). item("GreenKey"). item("YellowKey").
item("Boots"). item("Grapple").

key("RedKey"). key("BlueKey"). key("GreenKey"). key("YellowKey").
equipment("Boots"). equipment("Grapple").

special_type("Flooded"). special_type("Chasm").

requirement("null"). requirement("RedKey"). requirement("BlueKey"). 
requirement("GreenKey"). requirement("YellowKey").

room_pair(R1, R2) :- room(R1), room(R2), R1 != R2, R1 != "Goal".

% ===== CHOICE RULES =====
1 { item_in(I, R) : regular_room(R) } 1 :- item(I).
1 { room_type(R, "Flooded") : regular_room(R) } 1.
1 { room_type(R, "Chasm") : regular_room(R) } 1.
0 { conn(R1, R2, Req) : requirement(Req) } 1 :- room_pair(R1, R2).

% ===== CONSTRAINTS =====
:- room_type(R, "Flooded"), room_type(R, "Chasm").
:- item_in("Boots", R), room_type(R, "Flooded").
:- item_in("Grapple", R), room_type(R, "Chasm").
:- item_in("YellowKey", R), not room_type(R, "Chasm").
:- #count { R : conn(R, "Goal", _) } != 1.
:- conn("Goal", _, _).

bidirectional(R1, R2) :- conn(R1, R2, _), conn(R2, R1, _), R1 < R2.
:- #count { R1, R2 : bidirectional(R1, R2) } < 10.
:- #count { R1, R2 : bidirectional(R1, R2) } > 15.

oneway_pair(R1, R2) :- R1 < R2, R1 != "Goal", R2 != "Goal",
    conn(R1, R2, _), not conn(R2, R1, _).
oneway_pair(R1, R2) :- R1 < R2, R1 != "Goal", R2 != "Goal",
    conn(R2, R1, _), not conn(R1, R2, _).
:- #count { R1, R2 : oneway_pair(R1, R2) } != 1.

keyed_path(R1, R2) :- conn(R1, R2, Req), key(Req).
:- keyed_path(R1, R2), not conn(R2, R1, "null").

:- #count { R : conn("Start", R, _) } < 1.

% ===== REACHABILITY =====
step(0..20).
reachable("Start", 0).

item_available(I, S) :- item_in(I, R), reachable(R, S1), step(S), S1 < S.
have_item(I, S) :- item_available(I, S2), step(S), S2 <= S.

can_traverse(R1, R2, S) :- conn(R1, R2, "null"), step(S).
can_traverse(R1, R2, S) :- conn(R1, R2, Req), key(Req), have_item(Req, S), step(S).

can_enter(R, S) :- room(R), not room_type(R, "Flooded"), not room_type(R, "Chasm"), step(S).
can_enter(R, S) :- room_type(R, "Flooded"), have_item("Boots", S), step(S).
can_enter(R, S) :- room_type(R, "Chasm"), have_item("Grapple", S), step(S).

reachable(R2, S) :- 
    reachable(R1, S1),
    can_traverse(R1, R2, S1),
    can_enter(R2, S1),
    step(S), S1 < S.

:- room(R), not reachable(R, _).

first_reachable(R, S) :- reachable(R, S), not reachable(R, S-1), step(S), S > 0.
first_reachable("Start", 0).

goal_step(S) :- first_reachable("Goal", S).
:- room(R), R != "Goal", goal_step(SG), not reachable(R, SG-1).

#show item_in/2.
#show room_type/2.
#show conn/3.
"""

ctl = clingo.Control(["1"])
ctl.add("base", [], asp_program)
ctl.ground([("base", [])])

solution = None

def on_model(m):
    global solution
    atoms = m.symbols(atoms=True)
    
    special_types = {}
    item_locations = {}
    connections = []
    
    for atom in atoms:
        if atom.match("room_type", 2):
            room = str(atom.arguments[0]).strip('"')
            rtype = str(atom.arguments[1]).strip('"')
            special_types[rtype] = room
        elif atom.match("item_in", 2):
            item = str(atom.arguments[0]).strip('"')
            room = str(atom.arguments[1]).strip('"')
            item_locations[item] = room
        elif atom.match("conn", 3):
            from_room = str(atom.arguments[0]).strip('"')
            to_room = str(atom.arguments[1]).strip('"')
            req = str(atom.arguments[2]).strip('"')
            connections.append({
                "from": from_room,
                "to": to_room,
                "requires": None if req == "null" else req
            })
    
    connections.sort(key=lambda x: (x["from"], x["to"]))
    solution = {
        "special_room_types": special_types,
        "item_locations": item_locations,
        "connections": connections,
        "solution_validity": {
            "all_rooms_reachable": True,
            "goal_is_last": True
        }
    }

result = ctl.solve(on_model=on_model)

if result.satisfiable:
    print(json.dumps(solution, indent=2))
else:
    print(json.dumps({"error": "No solution exists"}))
