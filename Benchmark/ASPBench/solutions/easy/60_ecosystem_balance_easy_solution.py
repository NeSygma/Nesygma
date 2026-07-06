import clingo
import json
import math

asp_program = """
species("Grass", 100).
species("Rabbits", 30).
species("Foxes", 10).
species("Hawks", 5).

eats("Rabbits", "Grass").
eats("Foxes", "Rabbits").
eats("Hawks", "Rabbits").
eats("Hawks", "Foxes").

producer("Grass").

pop_value(1..100).

1 { population(S, P) : pop_value(P) } 1 :- species(S, _).

rate_value(1..5).

1 { consumes(Pred, Prey, R) : rate_value(R) } 1 :- eats(Pred, Prey).

:- population(S, P), P < 1.

:- population(S, P), species(S, Cap), P > Cap.

:- population("Rabbits", R), population("Grass", G), R * 2 > G.

:- population("Foxes", F), population("Rabbits", R), F * 10 > R * 3.

:- population("Hawks", H), population("Rabbits", R), population("Foxes", F),
   H * 5 > R + F.

#maximize { P@1, S : population(S, P) }.
"""

ctl = clingo.Control(["0"])
ctl.add("base", [], asp_program)
ctl.ground([("base", [])])

solution_data = None

def on_model(model):
    global solution_data
    solution_data = {
        'populations': {},
        'consumption_rates': []
    }
    
    for atom in model.symbols(atoms=True):
        if atom.name == "population":
            species = str(atom.arguments[0]).strip('"')
            pop = atom.arguments[1].number
            solution_data['populations'][species] = pop
        elif atom.name == "consumes":
            predator = str(atom.arguments[0]).strip('"')
            prey = str(atom.arguments[1]).strip('"')
            rate = atom.arguments[2].number
            solution_data['consumption_rates'].append({
                'predator': predator,
                'prey': prey,
                'rate_scaled': rate
            })

result = ctl.solve(on_model=on_model)

if result.satisfiable:
    grass = solution_data['populations']['Grass']
    rabbits = solution_data['populations']['Rabbits']
    foxes = solution_data['populations']['Foxes']
    hawks = solution_data['populations']['Hawks']
    
    food_web = []
    for rel in solution_data['consumption_rates']:
        food_web.append({
            "predator": rel['predator'],
            "prey": rel['prey'],
            "consumption_rate": rel['rate_scaled'] / 10.0
        })
    
    total_pop = grass + rabbits + foxes + hawks
    proportions = [grass/total_pop, rabbits/total_pop, foxes/total_pop, hawks/total_pop]
    biodiversity_index = -sum(p * math.log(p) if p > 0 else 0 for p in proportions) / math.log(4)
    
    rabbit_ratio = rabbits / (0.5 * grass) if grass > 0 else 0
    fox_ratio = foxes / (0.3 * rabbits) if rabbits > 0 else 0
    hawk_ratio = hawks / (0.2 * (rabbits + foxes)) if (rabbits + foxes) > 0 else 0
    stability_score = (rabbit_ratio + fox_ratio + hawk_ratio) / 3
    
    sustainability = (
        all(p > 0 for p in [grass, rabbits, foxes, hawks]) and
        rabbits <= 0.5 * grass and
        foxes <= 0.3 * rabbits and
        hawks <= 0.2 * (rabbits + foxes)
    )
    
    output = {
        "stable_populations": {
            "Grass": grass,
            "Rabbits": rabbits,
            "Foxes": foxes,
            "Hawks": hawks
        },
        "food_web": food_web,
        "ecosystem_health": {
            "biodiversity_index": round(biodiversity_index, 3),
            "stability_score": round(stability_score, 3),
            "sustainability": sustainability
        },
        "balance_achieved": sustainability
    }
    
    print(json.dumps(output, indent=2))
else:
    print(json.dumps({"error": "No solution exists", "reason": "Constraints cannot be satisfied"}))
