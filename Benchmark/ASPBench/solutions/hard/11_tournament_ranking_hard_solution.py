import clingo
import json
import random

def generate_match_data():
    """Generate match results using seed 42"""
    teams = [f"T{i+1:02d}" for i in range(30)]
    random.seed(42)
    matches = []
    for i in range(30):
        for j in range(i+1, 30):
            weight = random.randint(1, 5)
            if (i+j) % 2 == 0:
                winner = teams[i]
                loser = teams[j]
            else:
                winner = teams[j]
                loser = teams[i]
            matches.append((winner, loser, weight))
    return teams, matches

def build_asp_program(teams, matches):
    """Build the complete ASP program"""
    facts = []
    
    for team in teams:
        facts.append(f'team("{team}").')
    
    facts.append('position(1..30).')
    
    seeds = [f"T{i+1:02d}" for i in range(10)]
    for seed in seeds:
        facts.append(f'seed("{seed}").')
    
    groups = {
        'a': teams[0:5], 'b': teams[5:10], 'c': teams[10:15],
        'd': teams[15:20], 'e': teams[20:25], 'f': teams[25:30]
    }
    
    for group_name, group_teams in groups.items():
        for team in group_teams:
            facts.append(f'in_group("{team}", "{group_name}").')
    
    for winner, loser, weight in matches:
        facts.append(f'beats("{winner}", "{loser}", {weight}).')
    
    must_above = [
        ("T05", "T18"), ("T10", "T11"), ("T07", "T28"), ("T08", "T19"),
        ("T02", "T27"), ("T04", "T21"), ("T03", "T12"), ("T06", "T17"),
        ("T09", "T25"), ("T01", "T30"), ("T13", "T29"), ("T14", "T20"),
        ("T15", "T16"), ("T22", "T08"), ("T23", "T03"), ("T24", "T07"),
        ("T26", "T05"), ("T25", "T14"), ("T20", "T22"), ("T28", "T15")
    ]
    for above, below in must_above:
        facts.append(f'must_above("{above}", "{below}").')
    
    adjacency_bans = [
        ("T02", "T03"), ("T04", "T05"), ("T06", "T07"), ("T08", "T09"),
        ("T10", "T11"), ("T12", "T13"), ("T14", "T15"), ("T16", "T17"),
        ("T18", "T19"), ("T20", "T21"), ("T22", "T23"), ("T24", "T25"),
        ("T26", "T27"), ("T28", "T29"), ("T01", "T30")
    ]
    for t1, t2 in adjacency_bans:
        facts.append(f'cannot_be_adjacent("{t1}", "{t2}").')
    
    forbid_top = [
        ("T27", 3), ("T14", 5), ("T18", 4), ("T21", 2),
        ("T22", 6), ("T19", 8), ("T16", 7), ("T29", 10)
    ]
    for team, max_pos in forbid_top:
        facts.append(f'forbid_top("{team}", {max_pos}).')
    
    forbid_block = [
        ("T14", 11, 15), ("T20", 5, 9), ("T23", 13, 17),
        ("T02", 21, 25), ("T09", 26, 30)
    ]
    for team, start, end in forbid_block:
        facts.append(f'forbid_block("{team}", {start}, {end}).')
    
    rules = """
1 { rank(T, P) : position(P) } 1 :- team(T).
1 { rank(T, P) : team(T) } 1 :- position(P).

:- must_above(T1, T2), rank(T1, P1), rank(T2, P2), P1 >= P2.
:- cannot_be_adjacent(T1, T2), rank(T1, P1), rank(T2, P2), |P1 - P2| == 1.
:- forbid_top(T, MaxPos), rank(T, P), P <= MaxPos.
:- forbid_block(T, Start, End), rank(T, P), P >= Start, P <= End.

group_count_in_window(G, WinStart, Count) :- 
    position(WinStart), WinStart <= 26,
    in_group(_, G),
    Count = #count { T : rank(T, P), in_group(T, G), P >= WinStart, P < WinStart + 5 }.

:- group_count_in_window(G, WinStart, Count), Count > 2.

seed_in_top10(Count) :- Count = #count { T : seed(T), rank(T, P), P <= 10 }.
:- seed_in_top10(Count), Count < 6.

violation(Winner, Loser, Weight) :- 
    beats(Winner, Loser, Weight),
    rank(Winner, PWinner),
    rank(Loser, PLoser),
    PWinner > PLoser.

total_violations(Total) :- Total = #sum { W, Winner, Loser : violation(Winner, Loser, W) }.
:- total_violations(Total), Total > 650.
"""
    
    return "\n".join(facts) + "\n" + rules

def solve_tournament_ranking():
    """Solve the tournament ranking problem"""
    teams, matches = generate_match_data()
    
    ctl = clingo.Control(["1"])
    
    full_program = build_asp_program(teams, matches)
    ctl.add("base", [], full_program)
    ctl.ground([("base", [])])
    
    solution = None
    
    def on_model(model):
        nonlocal solution
        ranking_dict = {}
        violations_list = []
        
        for atom in model.symbols(atoms=True):
            if atom.name == "rank" and len(atom.arguments) == 2:
                team = str(atom.arguments[0]).strip('"')
                position = atom.arguments[1].number
                ranking_dict[position] = team
            elif atom.name == "violation" and len(atom.arguments) == 3:
                winner = str(atom.arguments[0]).strip('"')
                loser = str(atom.arguments[1]).strip('"')
                weight = atom.arguments[2].number
                violations_list.append((winner, loser, weight))
        
        ranking = [ranking_dict[i] for i in range(1, 31)]
        total_violations = sum(w for _, _, w in violations_list)
        
        total_abs_deviation = 0
        for pos, team in enumerate(ranking, 1):
            expected_pos = int(team[1:])
            total_abs_deviation += abs(pos - expected_pos)
        
        solution = {
            "ranking": ranking,
            "violations": total_violations,
            "valid": True,
            "total_abs_deviation": total_abs_deviation
        }
    
    result = ctl.solve(on_model=on_model)
    
    if result.satisfiable:
        return solution
    else:
        return {
            "error": "No solution exists",
            "reason": "Could not find a ranking satisfying all constraints with violations <= 650"
        }

solution = solve_tournament_ranking()
print(json.dumps(solution, indent=2))
