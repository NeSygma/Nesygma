import clingo
import json

problem_data = {
  "users": [
    {"id": "u1", "cost": 250, "category": "influencer", "activation_threshold": 10},
    {"id": "u2", "cost": 80, "category": "regular", "activation_threshold": 60},
    {"id": "u3", "cost": 70, "category": "regular", "activation_threshold": 90},
    {"id": "u4", "cost": 150, "category": "expert", "activation_threshold": 100},
    {"id": "u5", "cost": 90, "category": "regular", "activation_threshold": 70},
    {"id": "u6", "cost": 200, "category": "influencer", "activation_threshold": 120},
    {"id": "u7", "cost": 300, "category": "influencer", "activation_threshold": 10},
    {"id": "u8", "cost": 110, "category": "regular", "activation_threshold": 40},
    {"id": "u9", "cost": 60, "category": "regular", "activation_threshold": 80},
    {"id": "u10", "cost": 220, "category": "expert", "activation_threshold": 150},
    {"id": "u11", "cost": 50, "category": "regular", "activation_threshold": 50},
    {"id": "u12", "cost": 130, "category": "regular", "activation_threshold": 90},
    {"id": "u13", "cost": 280, "category": "influencer", "activation_threshold": 10},
    {"id": "u14", "cost": 85, "category": "regular", "activation_threshold": 60},
    {"id": "u15", "cost": 180, "category": "expert", "activation_threshold": 10},
    {"id": "u16", "cost": 95, "category": "regular", "activation_threshold": 50},
    {"id": "u17", "cost": 40, "category": "regular", "activation_threshold": 100},
    {"id": "u18", "cost": 190, "category": "expert", "activation_threshold": 110},
    {"id": "u19", "cost": 210, "category": "influencer", "activation_threshold": 130},
    {"id": "u20", "cost": 75, "category": "regular", "activation_threshold": 70},
    {"id": "u21", "cost": 100, "category": "expert", "activation_threshold": 80},
    {"id": "u22", "cost": 120, "category": "regular", "activation_threshold": 10},
    {"id": "u23", "cost": 140, "category": "regular", "activation_threshold": 120},
    {"id": "u24", "cost": 160, "category": "expert", "activation_threshold": 90},
    {"id": "u25", "cost": 240, "category": "influencer", "activation_threshold": 10}
  ],
  "connections": [
    {"from": "u1", "to": "u2", "strength": 70},
    {"from": "u1", "to": "u5", "strength": 50},
    {"from": "u7", "to": "u8", "strength": 50},
    {"from": "u7", "to": "u9", "strength": 30},
    {"from": "u15", "to": "u16", "strength": 60},
    {"from": "u22", "to": "u5", "strength": 30},
    {"from": "u2", "to": "u3", "strength": 40},
    {"from": "u8", "to": "u3", "strength": 50},
    {"from": "u8", "to": "u9", "strength": 60}
  ],
  "budget": {"total": 1000, "influencer": 600},
  "max_seeds": 5,
  "required_seed_category": "expert"
}

def generate_facts(data):
    facts = []
    
    for user in data["users"]:
        uid = user["id"]
        cost = user["cost"]
        category = user["category"]
        threshold = user["activation_threshold"]
        facts.append(f'user("{uid}").')
        facts.append(f'cost("{uid}", {cost}).')
        facts.append(f'category("{uid}", "{category}").')
        facts.append(f'threshold("{uid}", {threshold}).')
    
    for conn in data["connections"]:
        from_u = conn["from"]
        to_u = conn["to"]
        strength = conn["strength"]
        facts.append(f'connection("{from_u}", "{to_u}", {strength}).')
    
    facts.append(f'total_budget({data["budget"]["total"]}).')
    facts.append(f'max_seeds({data["max_seeds"]}).')
    
    for user in data["users"]:
        if user["category"] == "expert":
            facts.append(f'key_user("{user["id"]}").')
            break
    
    return "\n".join(facts)

asp_program = """
{ seed(U) : user(U) } :- user(_).

:- #count { U : seed(U) } > M, max_seeds(M).

:- #sum { C,U : seed(U), cost(U,C) } > B, total_budget(B).

activated(U) :- seed(U).

activated(U) :- user(U), threshold(U, T),
    #sum { S,From : activated(From), connection(From, U, S) } >= T.

activated_count(N) :- N = #count { U : activated(U) }.

key_activated :- key_user(K), activated(K).

score(S) :- activated_count(N), 
    S = N * 10 + 50, key_activated.
score(S) :- activated_count(N), 
    S = N * 10, not key_activated.

#maximize { S : score(S) }.

#show seed/1.
#show activated/1.
#show score/1.
"""

ctl = clingo.Control(["0"])

facts_program = generate_facts(problem_data)
full_program = facts_program + "\n" + asp_program
ctl.add("base", [], full_program)

ctl.ground([("base", [])])

best_solution = None
best_score = -1

def on_model(model):
    global best_solution, best_score
    
    seeds = []
    activated = []
    score_val = 0
    
    for atom in model.symbols(atoms=True):
        if atom.name == "seed" and len(atom.arguments) == 1:
            user_id = str(atom.arguments[0]).strip('"')
            seeds.append(user_id)
        
        elif atom.name == "activated" and len(atom.arguments) == 1:
            user_id = str(atom.arguments[0]).strip('"')
            activated.append(user_id)
        
        elif atom.name == "score" and len(atom.arguments) == 1:
            score_val = atom.arguments[0].number
    
    if score_val > best_score:
        best_score = score_val
        
        total_cost = sum(u["cost"] for u in problem_data["users"] if u["id"] in seeds)
        
        key_user_id = "u4"
        key_activated = key_user_id in activated
        
        best_solution = {
            "selected_seeds": sorted(seeds),
            "activated_users": sorted(activated),
            "total_cost": total_cost,
            "total_activated_count": len(activated),
            "key_user_activated": key_activated,
            "final_score": score_val
        }

result = ctl.solve(on_model=on_model)

if result.satisfiable and best_solution:
    print(json.dumps(best_solution, indent=2))
else:
    print(json.dumps({"error": "No solution exists", "reason": "Problem is unsatisfiable"}))
