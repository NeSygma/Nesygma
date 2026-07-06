import clingo
import json

asp_program = """
house(1..5).

color(red; green; white; yellow; blue).
nationality(brit; swede; dane; norwegian; german).
drink(tea; coffee; milk; beer; water).
cigarette(pall_mall; dunhill; blends; blue_master; prince).
pet(dog; birds; cats; horse; zebra).

1 { has_color(H, C) : color(C) } 1 :- house(H).
1 { has_nationality(H, N) : nationality(N) } 1 :- house(H).
1 { has_drink(H, D) : drink(D) } 1 :- house(H).
1 { has_cigarette(H, C) : cigarette(C) } 1 :- house(H).
1 { has_pet(H, P) : pet(P) } 1 :- house(H).

1 { has_color(H, C) : house(H) } 1 :- color(C).
1 { has_nationality(H, N) : house(H) } 1 :- nationality(N).
1 { has_drink(H, D) : house(H) } 1 :- drink(D).
1 { has_cigarette(H, C) : house(H) } 1 :- cigarette(C).
1 { has_pet(H, P) : house(H) } 1 :- pet(P).

:- has_nationality(H, brit), not has_color(H, red).
:- has_color(H, red), not has_nationality(H, brit).

:- has_nationality(H, swede), not has_pet(H, dog).
:- has_pet(H, dog), not has_nationality(H, swede).

:- has_nationality(H, dane), not has_drink(H, tea).
:- has_drink(H, tea), not has_nationality(H, dane).

:- has_color(H1, green), has_color(H2, white), H2 != H1 + 1.

:- has_color(H, green), not has_drink(H, coffee).
:- has_drink(H, coffee), not has_color(H, green).

:- has_cigarette(H, pall_mall), not has_pet(H, birds).
:- has_pet(H, birds), not has_cigarette(H, pall_mall).

:- has_color(H, yellow), not has_cigarette(H, dunhill).
:- has_cigarette(H, dunhill), not has_color(H, yellow).

:- not has_drink(3, milk).

:- not has_nationality(1, norwegian).

:- has_cigarette(H1, blends), not has_pet(H1-1, cats), not has_pet(H1+1, cats).

:- has_pet(H1, horse), not has_cigarette(H1-1, dunhill), not has_cigarette(H1+1, dunhill).

:- has_cigarette(H, blue_master), not has_drink(H, beer).
:- has_drink(H, beer), not has_cigarette(H, blue_master).

:- has_nationality(H, german), not has_cigarette(H, prince).
:- has_cigarette(H, prince), not has_nationality(H, german).

:- has_nationality(H1, norwegian), not has_color(H1-1, blue), not has_color(H1+1, blue).

:- has_cigarette(H1, blends), not has_drink(H1-1, water), not has_drink(H1+1, water).

#show has_color/2.
#show has_nationality/2.
#show has_drink/2.
#show has_cigarette/2.
#show has_pet/2.
"""

def capitalize_value(value):
    if value == "pall_mall":
        return "Pall Mall"
    elif value == "blue_master":
        return "Blue Master"
    return value.capitalize()

ctl = clingo.Control(["1"])
ctl.add("base", [], asp_program)
ctl.ground([("base", [])])

solution_data = None

def on_model(model):
    global solution_data
    solution_data = {}
    
    for atom in model.symbols(atoms=True):
        if atom.name == "has_color":
            house = atom.arguments[0].number
            color = str(atom.arguments[1])
            if house not in solution_data:
                solution_data[house] = {}
            solution_data[house]["color"] = color
            
        elif atom.name == "has_nationality":
            house = atom.arguments[0].number
            nationality = str(atom.arguments[1])
            if house not in solution_data:
                solution_data[house] = {}
            solution_data[house]["nationality"] = nationality
            
        elif atom.name == "has_drink":
            house = atom.arguments[0].number
            drink = str(atom.arguments[1])
            if house not in solution_data:
                solution_data[house] = {}
            solution_data[house]["drink"] = drink
            
        elif atom.name == "has_cigarette":
            house = atom.arguments[0].number
            cigarette = str(atom.arguments[1])
            if house not in solution_data:
                solution_data[house] = {}
            solution_data[house]["cigarette"] = cigarette
            
        elif atom.name == "has_pet":
            house = atom.arguments[0].number
            pet = str(atom.arguments[1])
            if house not in solution_data:
                solution_data[house] = {}
            solution_data[house]["pet"] = pet

result = ctl.solve(on_model=on_model)

if result.satisfiable:
    zebra_owner = None
    for house_num, attrs in solution_data.items():
        if attrs.get("pet") == "zebra":
            zebra_owner = capitalize_value(attrs["nationality"])
            break
    
    solution_array = []
    for house_num in sorted(solution_data.keys()):
        attrs = solution_data[house_num]
        solution_array.append({
            "house": house_num,
            "color": capitalize_value(attrs["color"]),
            "nationality": capitalize_value(attrs["nationality"]),
            "drink": capitalize_value(attrs["drink"]),
            "cigarette": capitalize_value(attrs["cigarette"]),
            "pet": capitalize_value(attrs["pet"])
        })
    
    output = {
        "solution": solution_array,
        "zebra_owner": zebra_owner
    }
    
    print(json.dumps(output, indent=2))
else:
    print(json.dumps({"error": "No solution exists", "reason": "Constraints are unsatisfiable"}))
