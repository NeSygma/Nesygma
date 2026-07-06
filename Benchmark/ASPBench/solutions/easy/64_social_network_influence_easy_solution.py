import clingo
import json

asp_program = """
user("user1", 80, 100, "influencer").
user("user2", 30, 50, "regular").
user("user3", 50, 80, "regular").
user("user4", 90, 150, "influencer").
user("user5", 40, 60, "regular").
user("user6", 60, 90, "regular").
user("user7", 70, 120, "influencer").
user("user8", 20, 40, "regular").

connection("user1", "user2", 6).
connection("user1", "user3", 7).
connection("user2", "user3", 4).
connection("user2", "user5", 5).
connection("user3", "user4", 3).
connection("user4", "user5", 8).
connection("user4", "user6", 6).
connection("user5", "user7", 5).
connection("user6", "user7", 7).
connection("user7", "user8", 4).

#const max_seeds = 2.
#const budget = 300.

user_id(U) :- user(U, _, _, _).

0 { seed(U) : user_id(U) } max_seeds.

:- #sum { Cost, U : seed(U), user(U, _, Cost, _) } > budget.

directly_influenced(To) :- seed(From), connection(From, To, Strength), Strength >= 3, not seed(To).

secondary_influenced(To) :- directly_influenced(From), connection(From, To, Strength), 
                             Strength >= 2, not seed(To), not directly_influenced(To).

reached(U) :- seed(U).
reached(U) :- directly_influenced(U).
reached(U) :- secondary_influenced(U).

total_reach(N) :- N = #count { U : reached(U) }.

:- total_reach(N), N < 7.

#show seed/1.
#show directly_influenced/1.
#show secondary_influenced/1.
#show total_reach/1.
"""

users = {
    "user1": {"weight": 0.8, "cost": 100, "category": "influencer"},
    "user2": {"weight": 0.3, "cost": 50, "category": "regular"},
    "user3": {"weight": 0.5, "cost": 80, "category": "regular"},
    "user4": {"weight": 0.9, "cost": 150, "category": "influencer"},
    "user5": {"weight": 0.4, "cost": 60, "category": "regular"},
    "user6": {"weight": 0.6, "cost": 90, "category": "regular"},
    "user7": {"weight": 0.7, "cost": 120, "category": "influencer"},
    "user8": {"weight": 0.2, "cost": 40, "category": "regular"}
}

connections = [
    ("user1", "user2", 0.6), ("user1", "user3", 0.7), ("user2", "user3", 0.4),
    ("user2", "user5", 0.5), ("user3", "user4", 0.3), ("user4", "user5", 0.8),
    ("user4", "user6", 0.6), ("user5", "user7", 0.5), ("user6", "user7", 0.7),
    ("user7", "user8", 0.4)
]

def calculate_expected_reach(seed_user, all_seeds, connections, users):
    direct_from_seed = set()
    for from_u, to_u, strength in connections:
        if from_u == seed_user and strength >= 0.3 and to_u not in all_seeds:
            direct_from_seed.add(to_u)
    
    secondary_from_seed = set()
    for from_u, to_u, strength in connections:
        if from_u in direct_from_seed and strength >= 0.2 and to_u not in all_seeds and to_u not in direct_from_seed:
            secondary_from_seed.add(to_u)
    
    return 1 + len(direct_from_seed) + len(secondary_from_seed)

ctl = clingo.Control(["1"])
ctl.add("base", [], asp_program)
ctl.ground([("base", [])])

solution_data = None

def on_model(model):
    global solution_data
    seeds, direct, secondary, total = [], [], [], 0
    
    for atom in model.symbols(atoms=True):
        if atom.name == "seed":
            seeds.append(str(atom.arguments[0]).strip('"'))
        elif atom.name == "directly_influenced":
            direct.append(str(atom.arguments[0]).strip('"'))
        elif atom.name == "secondary_influenced":
            secondary.append(str(atom.arguments[0]).strip('"'))
        elif atom.name == "total_reach":
            total = int(str(atom.arguments[0]))
    
    solution_data = {"seeds": seeds, "direct": direct, "secondary": secondary, "total_reach": total}

result = ctl.solve(on_model=on_model)

if result.satisfiable:
    seeds = solution_data["seeds"]
    direct_influenced = solution_data["direct"]
    secondary_influenced = solution_data["secondary"]
    total_reach = solution_data["total_reach"]
    
    total_budget_used = sum(users[s]["cost"] for s in seeds)
    
    selected_seeds = []
    for seed in seeds:
        expected_reach = calculate_expected_reach(seed, seeds, connections, users)
        selected_seeds.append({
            "user_id": seed,
            "cost": users[seed]["cost"],
            "expected_reach": float(expected_reach)
        })
    
    cascade_connections = []
    for from_u, to_u, strength in connections:
        if (from_u in seeds and to_u in direct_influenced) or \
           (from_u in direct_influenced and to_u in secondary_influenced):
            cascade_connections.append(strength)
    
    influence_probability = sum(cascade_connections) / len(cascade_connections) if cascade_connections else 0.0
    
    cascade_depth = 1
    if direct_influenced:
        cascade_depth = 2
    if secondary_influenced:
        cascade_depth = 3
    
    total_users = len(users)
    coverage_ratio = total_reach / total_users
    efficiency_score = total_reach / total_budget_used if total_budget_used > 0 else 0
    
    output = {
        "selected_seeds": selected_seeds,
        "cascade_analysis": {
            "total_budget_used": total_budget_used,
            "direct_influence": sorted(direct_influenced),
            "secondary_influence": sorted(secondary_influenced),
            "total_reach": total_reach,
            "influence_probability": round(influence_probability, 2)
        },
        "network_metrics": {
            "coverage_ratio": round(coverage_ratio, 3),
            "efficiency_score": round(efficiency_score, 3),
            "cascade_depth": cascade_depth
        }
    }
    
    print(json.dumps(output, indent=2))
else:
    print(json.dumps({"error": "No solution exists", "reason": "Could not find seed selection meeting constraints"}))
