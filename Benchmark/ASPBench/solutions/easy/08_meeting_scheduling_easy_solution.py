import clingo
import json

asp_program = """
% Facts from problem description

% Meetings
meeting(m1). meeting(m2). meeting(m3). meeting(m4). meeting(m5).

% Days and slots
day(1..3).
slot(1..3).

% Rooms
room(r1). room(r2).

% People
person(p1). person(p2). person(p3). person(p4). person(p5).

% Required attendees
requires(m1, p1). requires(m1, p2). requires(m1, p3).
requires(m2, p1). requires(m2, p5).
requires(m3, p2). requires(m3, p3).
requires(m4, p1). requires(m4, p4).
requires(m5, p1). requires(m5, p2). requires(m5, p3).

% Time preferences
prefers(m1, 1, 1).
prefers(m2, 1, 2).
prefers(m4, 3, 3).

% Choice rule: Each meeting gets exactly one (day, slot, room) assignment
1 { scheduled(M, D, S, R) : day(D), slot(S), room(R) } 1 :- meeting(M).

% Constraint 1: No person can attend two meetings at the same time
:- scheduled(M1, D, S, _), scheduled(M2, D, S, _), 
   M1 != M2, requires(M1, P), requires(M2, P).

% Constraint 2: Only one meeting per room per time slot
:- scheduled(M1, D, S, R), scheduled(M2, D, S, R), M1 != M2.

% Define preference violations - meeting not at preferred time
violation(M) :- meeting(M), prefers(M, PD, PS), 
                scheduled(M, D, S, _), D != PD.
violation(M) :- meeting(M), prefers(M, PD, PS), 
                scheduled(M, D, S, _), S != PS.

% Optimization: Minimize preference violations
#minimize { 1,M : violation(M) }.

% Display only scheduled meetings
#show scheduled/4.
"""

ctl = clingo.Control(["0"])
ctl.add("base", [], asp_program)
ctl.ground([("base", [])])

solution_data = None
optimal_cost = None

def on_model(model):
    global solution_data, optimal_cost
    
    schedule = []
    for atom in model.symbols(atoms=True):
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
    
    schedule.sort(key=lambda x: (x["day"], x["slot"], x["meeting"]))
    
    cost = model.cost
    if len(cost) > 0:
        optimal_cost = cost[0]
    else:
        optimal_cost = 0
    
    solution_data = {
        "schedule": schedule,
        "conflicts": [],
        "preference_violations": optimal_cost,
        "feasible": True
    }

result = ctl.solve(on_model=on_model)

if result.satisfiable:
    print(json.dumps(solution_data, indent=2))
else:
    print(json.dumps({
        "schedule": [],
        "conflicts": ["No feasible schedule exists"],
        "preference_violations": -1,
        "feasible": False
    }, indent=2))
