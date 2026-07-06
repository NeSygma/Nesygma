import clingo
import json

asp_program = """
% Facts - Domain definition
nurse(1..4).
day(1..7).
shift(1..3).

coverage(1, 2).
coverage(2, 1).
coverage(3, 1).

weekend(6).
weekend(7).

% --- CHOICE RULES ---
{ assigned(N, D, S) : shift(S) } 1 :- nurse(N), day(D).

% --- HARD CONSTRAINTS ---

% Coverage requirement
:- coverage(S, Required), day(D), 
   #count { N : assigned(N, D, S) } != Required.

% Rest period
:- assigned(N, D, 3), assigned(N, D+1, 1), day(D), D < 7.

% --- SOFT CONSTRAINTS ---

works_day(N, D) :- assigned(N, D, _).

% Consecutive days violations
violation_day_4(N, D) :- works_day(N, D), works_day(N, D-1), 
                          works_day(N, D-2), works_day(N, D-3),
                          day(D), D >= 4.

% Fair distribution
total_shifts(N, Count) :- nurse(N), 
    Count = #count { D, S : assigned(N, D, S) }.

violation_unfair(N) :- total_shifts(N, Count), Count < 6.
violation_unfair(N) :- total_shifts(N, Count), Count > 8.

% Weekend coverage
weekend_worker(N) :- assigned(N, D, _), weekend(D).
violation_weekend :- #count { N : weekend_worker(N) } < 2.

% --- OPTIMIZATION ---
#minimize { 1,N,D : violation_day_4(N, D) }.
#minimize { 1,N : violation_unfair(N) }.
#minimize { 1 : violation_weekend }.
"""

ctl = clingo.Control(["0"])
ctl.add("base", [], asp_program)
ctl.ground([("base", [])])

solution_data = None
optimal_cost = None

def on_model(model):
    global solution_data, optimal_cost
    
    assignments = []
    for atom in model.symbols(atoms=True):
        if atom.name == "assigned" and len(atom.arguments) == 3:
            nurse = atom.arguments[0].number
            day = atom.arguments[1].number
            shift = atom.arguments[2].number
            assignments.append((nurse, day, shift))
    
    optimal_cost = model.cost
    solution_data = assignments

result = ctl.solve(on_model=on_model)

if result.satisfiable:
    roster_dict = {}
    for nurse, day, shift in solution_data:
        if day not in roster_dict:
            roster_dict[day] = {1: [], 2: [], 3: []}
        roster_dict[day][shift].append(nurse)
    
    roster = []
    for day in range(1, 8):
        day_shifts = [
            sorted(roster_dict[day][1]),
            sorted(roster_dict[day][2]),
            sorted(roster_dict[day][3])
        ]
        roster.append(day_shifts)
    
    total_violations = sum(optimal_cost)
    
    output = {
        "roster": roster,
        "violations": total_violations,
        "coverage_met": True
    }
    
    print(json.dumps(output))
else:
    print(json.dumps({"error": "No solution exists", "reason": "UNSAT"}))
