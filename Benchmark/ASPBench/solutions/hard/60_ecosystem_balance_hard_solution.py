import clingo
import json

asp_program = """
species("Grass"; "Rabbits"; "Foxes"; "Hawks").
zone("Forest"; "Meadow").
season("Summer"; "Winter").
level(0; 1; 2).

eats("Rabbits", "Grass").
eats("Foxes", "Rabbits").
eats("Hawks", "Foxes").

1 { population(S, Z, Se, L) : level(L) } 1 :- species(S), zone(Z), season(Se).

:- population("Grass", "Forest", _, L), L > 1.
:- population("Foxes", "Meadow", _, L), L != 0.
:- population("Hawks", _, _, L), L > 1.

:- population("Grass", _, "Winter", L), L > 1.
:- population("Rabbits", _, "Winter", L), L > 1.

:- population(Predator, Z, Se, PredLevel), 
   population(Prey, Z, Se, PreyLevel),
   eats(Predator, Prey),
   PredLevel > PreyLevel.

species_total(S, Total) :- species(S), 
   Total = #sum { L,Z,Se : population(S, Z, Se, L) }.
:- species_total(S, Total), Total < 1.

hawks_total(Total) :- Total = #sum { L,Z,Se : population("Hawks", Z, Se, L) }.
:- hawks_total(Total), Total != 2.
"""

ctl = clingo.Control(["1"])
ctl.add("base", [], asp_program)
ctl.ground([("base", [])])

solution_data = None

def on_model(model):
    global solution_data
    solution_data = {
        "population_levels": [],
        "predator_prey_relationships": [
            {"predator": "Rabbits", "prey": "Grass"},
            {"predator": "Foxes", "prey": "Rabbits"},
            {"predator": "Hawks", "prey": "Foxes"}
        ],
        "balance_achieved": True
    }
    
    for atom in model.symbols(atoms=True):
        if atom.name == "population" and len(atom.arguments) == 4:
            species = str(atom.arguments[0]).strip('"')
            zone = str(atom.arguments[1]).strip('"')
            season = str(atom.arguments[2]).strip('"')
            level = atom.arguments[3].number
            
            solution_data["population_levels"].append({
                "species": species,
                "zone": zone,
                "season": season,
                "level": level
            })
    
    solution_data["population_levels"].sort(
        key=lambda x: (x["species"], x["zone"], x["season"])
    )

result = ctl.solve(on_model=on_model)

if result.satisfiable and solution_data:
    print(json.dumps(solution_data, indent=2))
else:
    error_output = {
        "error": "No solution exists",
        "reason": "The constraints are unsatisfiable"
    }
    print(json.dumps(error_output, indent=2))
