import clingo
import json
import math

teams = ["A", "B", "C", "D"]
locations = {
    "A": (0, 0),
    "B": (3, 4),
    "C": (6, 0),
    "D": (2, 8)
}

def euclidean_distance(loc1, loc2):
    return math.sqrt((loc1[0] - loc2[0])**2 + (loc1[1] - loc2[1])**2)

distances = {}
for t1 in teams:
    for t2 in teams:
        if t1 != t2:
            dist = euclidean_distance(locations[t1], locations[t2])
            distances[(t1, t2)] = dist

def generate_asp_program():
    facts = []
    
    for team in teams:
        facts.append(f'team("{team}").')
    
    facts.append('round(1..6).')
    
    for (t1, t2), dist in distances.items():
        dist_int = int(round(dist * 10))
        facts.append(f'distance("{t1}", "{t2}", {dist_int}).')
    
    for i, t1 in enumerate(teams):
        for t2 in teams[i+1:]:
            facts.append(f'pair("{t1}", "{t2}").')
    
    facts_str = "\n".join(facts)
    
    rules = """
{ match(T1, T2, R) : round(R) } = 1 :- pair(T1, T2), team(T1), team(T2).
{ match(T2, T1, R) : round(R) } = 1 :- pair(T1, T2), team(T1), team(T2).

:- round(R), #count { T1, T2 : match(T1, T2, R) } != 2.

home_games(T, R, N) :- team(T), round(R), N = #count { T2 : match(T, T2, R) }.
away_games(T, R, N) :- team(T), round(R), N = #count { T1 : match(T1, T, R) }.
total_games(T, R, Total) :- home_games(T, R, H), away_games(T, R, A), Total = H + A.
:- total_games(T, R, Total), Total != 1.

plays_home(T, R) :- match(T, _, R).
:- team(T), round(R), R <= 4, plays_home(T, R), plays_home(T, R+1), plays_home(T, R+2).

plays_away(T, R) :- match(_, T, R).
:- team(T), round(R), R <= 4, plays_away(T, R), plays_away(T, R+1), plays_away(T, R+2).

travel(Away, Home, R, Dist) :- match(Home, Away, R), distance(Away, Home, Dist).

total_dist(Total) :- Total = #sum { Dist, Away, Home, R : travel(Away, Home, R, Dist) }.

:- total_dist(Total), Total > 750.

#show match/3.
#show total_dist/1.
"""
    
    return facts_str + "\n" + rules

asp_program = generate_asp_program()

ctl = clingo.Control(["1"])
ctl.add("base", [], asp_program)
ctl.ground([("base", [])])

solution_data = None

def on_model(model):
    global solution_data
    
    matches_by_round = {r: [] for r in range(1, 7)}
    
    for atom in model.symbols(atoms=True):
        if atom.name == "match" and len(atom.arguments) == 3:
            home = str(atom.arguments[0]).strip('"')
            away = str(atom.arguments[1]).strip('"')
            round_num = atom.arguments[2].number
            matches_by_round[round_num].append({"home": home, "away": away})
    
    solution_data = {"matches_by_round": matches_by_round}

result = ctl.solve(on_model=on_model)

if result.satisfiable:
    schedule = []
    for r in range(1, 7):
        schedule.append(solution_data["matches_by_round"][r])
    
    total_distance = 0
    for r in range(1, 7):
        for match in solution_data["matches_by_round"][r]:
            home = match["home"]
            away = match["away"]
            total_distance += distances[(away, home)]
    
    output = {
        "schedule": schedule,
        "total_distance": round(total_distance, 1),
        "feasible": True
    }
    
    print(json.dumps(output, indent=2))
else:
    output = {
        "error": "No solution exists",
        "reason": "Could not find a schedule satisfying all constraints with distance <= 75"
    }
    print(json.dumps(output, indent=2))
