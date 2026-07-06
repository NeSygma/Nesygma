import clingo
import json

def generate_asp_program():
    program = """
% Facts - Rooms
room(r1). room(r2). room(r3). room(r4).

% Room Equipment
has_equipment(r1, projector). has_equipment(r1, whiteboard). 
has_equipment(r1, video). has_equipment(r1, confcall).
has_equipment(r2, projector). has_equipment(r2, whiteboard). 
has_equipment(r2, confcall).
has_equipment(r3, whiteboard). has_equipment(r3, confcall).
has_equipment(r4, projector). has_equipment(r4, video).

% Meetings
meeting(m1). meeting(m2). meeting(m3). meeting(m4). meeting(m5).
meeting(m6). meeting(m7). meeting(m8). meeting(m9). meeting(m10).
meeting(m11). meeting(m12). meeting(m13). meeting(m14). meeting(m15).
meeting(m16). meeting(m17). meeting(m18). meeting(m19). meeting(m20).

% Meeting Equipment Requirements
requires_equipment(m1, projector).
requires_equipment(m2, whiteboard).
requires_equipment(m3, confcall).
requires_equipment(m4, video). requires_equipment(m4, projector).
requires_equipment(m5, projector). requires_equipment(m5, confcall).
requires_equipment(m6, whiteboard). requires_equipment(m6, confcall).
requires_equipment(m7, projector). requires_equipment(m7, whiteboard). 
requires_equipment(m7, confcall).
requires_equipment(m8, video). requires_equipment(m8, confcall).
requires_equipment(m9, projector). requires_equipment(m9, video).
requires_equipment(m10, projector). requires_equipment(m10, whiteboard).
requires_equipment(m11, projector).
requires_equipment(m12, whiteboard).
requires_equipment(m13, confcall).
requires_equipment(m14, video). requires_equipment(m14, projector).
requires_equipment(m15, projector). requires_equipment(m15, confcall).
requires_equipment(m16, whiteboard). requires_equipment(m16, confcall).
requires_equipment(m17, projector). requires_equipment(m17, whiteboard). 
requires_equipment(m17, confcall).
requires_equipment(m18, video). requires_equipment(m18, confcall).
requires_equipment(m19, projector). requires_equipment(m19, video).
requires_equipment(m20, projector). requires_equipment(m20, whiteboard).

% People
person(p1). person(p2). person(p3). person(p4). person(p5).
person(p6). person(p7). person(p8). person(p9). person(p10).
person(p11). person(p12). person(p13). person(p14). person(p15).
person(p16). person(p17). person(p18). person(p19). person(p20).

% Meeting Attendees
attends(p1, m1). attends(p3, m1). attends(p6, m1). attends(p8, m1).
attends(p2, m2). attends(p4, m2). attends(p7, m2). attends(p9, m2).
attends(p3, m3). attends(p5, m3). attends(p8, m3). attends(p10, m3).
attends(p4, m4). attends(p6, m4). attends(p9, m4). attends(p11, m4).
attends(p5, m5). attends(p7, m5). attends(p10, m5). attends(p12, m5).
attends(p6, m6). attends(p8, m6). attends(p11, m6). attends(p13, m6).
attends(p7, m7). attends(p9, m7). attends(p12, m7). attends(p14, m7).
attends(p8, m8). attends(p10, m8). attends(p13, m8). attends(p15, m8).
attends(p9, m9). attends(p11, m9). attends(p14, m9). attends(p16, m9).
attends(p10, m10). attends(p12, m10). attends(p15, m10). 
attends(p17, m10).
attends(p11, m11). attends(p13, m11). attends(p16, m11). 
attends(p18, m11).
attends(p12, m12). attends(p14, m12). attends(p17, m12). 
attends(p19, m12).
attends(p13, m13). attends(p15, m13). attends(p18, m13). 
attends(p20, m13).
attends(p14, m14). attends(p16, m14). attends(p19, m14). attends(p1, m14).
attends(p15, m15). attends(p17, m15). attends(p20, m15). attends(p2, m15).
attends(p16, m16). attends(p18, m16). attends(p1, m16). attends(p3, m16).
attends(p17, m17). attends(p19, m17). attends(p2, m17). attends(p4, m17).
attends(p18, m18). attends(p20, m18). attends(p3, m18). attends(p5, m18).
attends(p19, m19). attends(p1, m19). attends(p4, m19). attends(p6, m19).
attends(p20, m20). attends(p2, m20). attends(p5, m20). attends(p7, m20).

% Days and Slots
day(1..5).
slot(1..4).

% Choice Rule: Each meeting assigned to exactly one (day, slot, room)
% Constrain at source: only generate assignments to rooms with required 
% equipment
1 { scheduled(M, D, S, R) : day(D), slot(S), room(R), 
    not missing_equipment(M, R) } 1 :- meeting(M).

% Helper: A meeting is missing equipment from a room if it requires 
% equipment the room doesn't have
missing_equipment(M, R) :- meeting(M), room(R), requires_equipment(M, E), 
                           not has_equipment(R, E).

% Constraint: No person can attend two meetings at the same (day, slot)
:- scheduled(M1, D, S, R1), scheduled(M2, D, S, R2), M1 != M2,
   attends(P, M1), attends(P, M2).

% Constraint: Each room can host at most one meeting per (day, slot)
:- scheduled(M1, D, S, R), scheduled(M2, D, S, R), M1 != M2.

#show scheduled/4.
"""
    return program

def solve_meeting_scheduling():
    ctl = clingo.Control(["1"])
    
    program = generate_asp_program()
    ctl.add("base", [], program)
    
    ctl.ground([("base", [])])
    
    solution = None
    
    def on_model(m):
        nonlocal solution
        atoms = m.symbols(atoms=True)
        schedule = []
        
        for atom in atoms:
            if atom.name == "scheduled" and len(atom.arguments) == 4:
                meeting = str(atom.arguments[0])
                day = atom.arguments[1].number
                slot = atom.arguments[2].number
                room = str(atom.arguments[3])
                
                schedule.append({
                    "meeting": meeting,
                    "day": day,
                    "slot": slot,
                    "room": room
                })
        
        schedule.sort(key=lambda x: int(x["meeting"][1:]))
        solution = schedule
    
    result = ctl.solve(on_model=on_model)
    
    if result.satisfiable and solution:
        output = {
            "schedule": solution,
            "feasible": True
        }
    else:
        output = {
            "error": "No solution exists",
            "feasible": False
        }
    
    return output

result = solve_meeting_scheduling()
print(json.dumps(result, indent=2))
