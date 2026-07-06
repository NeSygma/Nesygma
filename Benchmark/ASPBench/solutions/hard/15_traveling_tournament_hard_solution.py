import clingo
import json
import math


def generate_asp_program():
    coords = {
        'a': (0, 0),
        'b': (10, 0),
        'c': (5, 8),
        'd': (0, 15),
        'e': (10, 15),
        'f': (15, 8)
    }
    
    distance_facts = []
    for t1, (x1, y1) in coords.items():
        for t2, (x2, y2) in coords.items():
            if t1 != t2:
                dist_squared = (x2 - x1)**2 + (y2 - y1)**2
                dist = int(math.sqrt(dist_squared) * 10)
                distance_facts.append(f"loc_distance({t1}, {t2}, {dist}).")
    
    next_round_facts = [f"next_round({r}, {r+1})." for r in range(1, 10)]
    prev_round_facts = [f"prev_round({r+1}, {r})." for r in range(0, 10)]
    
    program = f"""
team(a; b; c; d; e; f).
round(1..10).
round0(0..10).

{' '.join(next_round_facts)}
{' '.join(prev_round_facts)}

home_city(a, 0, 0).
home_city(b, 10, 0).
home_city(c, 5, 8).
home_city(d, 0, 15).
home_city(e, 10, 15).
home_city(f, 15, 8).

{' '.join(distance_facts)}

{{ match(Home, Away, R) : round(R) }} 1 :- team(Home), team(Away), Home != Away.

:- team(Home), team(Away), Home != Away, #count {{ R : match(Home, Away, R) }} != 1.

plays_home(T, R) :- match(T, _, R).
plays_away(T, R) :- match(_, T, R).

:- team(T), round(R), plays_home(T, R), plays_away(T, R).
:- team(T), round(R), not plays_home(T, R), not plays_away(T, R).

:- round(R), #count {{ Home, Away : match(Home, Away, R) }} != 3.

:- team(T), round(R1), next_round(R1, R2), next_round(R2, R3), next_round(R3, R4),
   plays_home(T, R1), plays_home(T, R2), plays_home(T, R3), plays_home(T, R4).

:- team(T), round(R1), next_round(R1, R2), next_round(R2, R3), next_round(R3, R4),
   plays_away(T, R1), plays_away(T, R2), plays_away(T, R3), plays_away(T, R4).

:- match(a, b, 1).
:- match(b, a, 1).
:- match(c, d, 1).
:- match(d, c, 1).

has_home_stand(T) :- team(T), round(R), next_round(R, R2), plays_home(T, R), plays_home(T, R2).
:- team(T), not has_home_stand(T).

at_city(T, T, 0) :- team(T).
at_city(T, T, R) :- plays_home(T, R), round(R).
at_city(T, Host, R) :- plays_away(T, R), match(Host, T, R).

:- plays_away(T, R), next_round(R, R2), prev_round(R, RPrev),
   match(Host, T, R),
   at_city(T, PrevLoc, RPrev),
   loc_distance(PrevLoc, Host, Dist),
   Dist > 140,
   not plays_home(T, R2).

#show match/3.
"""
    return program


def solve_tournament():
    ctl = clingo.Control(["1"])
    
    program = generate_asp_program()
    ctl.add("base", [], program)
    ctl.ground([("base", [])])
    
    solution = None
    
    def on_model(m):
        nonlocal solution
        atoms = m.symbols(atoms=True)
        
        matches = {}
        for atom in atoms:
            if atom.name == "match" and len(atom.arguments) == 3:
                home = str(atom.arguments[0]).upper()
                away = str(atom.arguments[1]).upper()
                round_num = atom.arguments[2].number
                
                if round_num not in matches:
                    matches[round_num] = []
                matches[round_num].append({"home": home, "away": away})
        
        schedule = []
        for r in range(1, 11):
            if r in matches:
                schedule.append(matches[r])
            else:
                schedule.append([])
        
        solution = {
            "schedule": schedule,
            "feasible": True
        }
    
    result = ctl.solve(on_model=on_model)
    
    if result.satisfiable:
        return solution
    else:
        return {"schedule": [], "feasible": False}


solution = solve_tournament()
print(json.dumps(solution, indent=2))
