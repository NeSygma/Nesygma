import clingo
import json

program = """
person("Alice"; "Bob"; "Carol"; "Dave").
color("Red"; "Blue"; "Green"; "Yellow").
pet("Cat"; "Dog"; "Bird"; "Fish").
house(1..4).

1 { has_color(P, C) : color(C) } 1 :- person(P).
1 { has_pet(P, Pet) : pet(Pet) } 1 :- person(P).
1 { lives_in(P, H) : house(H) } 1 :- person(P).

1 { has_color(P, C) : person(P) } 1 :- color(C).
1 { has_pet(P, Pet) : person(P) } 1 :- pet(Pet).
1 { lives_in(P, H) : person(P) } 1 :- house(H).

:- not lives_in("Alice", 1).
:- has_color(P, "Red"), not lives_in(P, 2).
:- not has_pet("Bob", "Cat").
:- not has_color("Carol", "Blue").
:- has_color(P, "Yellow"), not has_pet(P, "Fish").
:- has_color(P, "Green"), not lives_in(P, 4).
:- not has_pet("Dave", "Dog").
:- has_pet("Alice", "Bird").
"""

ctl = clingo.Control(["1"])
ctl.add("base", [], program)
ctl.ground([("base", [])])

solution = None

def on_model(model):
    global solution
    solution = {"assignments": []}
    atoms = model.symbols(atoms=True)
    person_data = {}
    
    for atom in atoms:
        if atom.name == "has_color" and len(atom.arguments) == 2:
            person = str(atom.arguments[0]).strip('"')
            color = str(atom.arguments[1]).strip('"')
            if person not in person_data:
                person_data[person] = {}
            person_data[person]["color"] = color
            
        elif atom.name == "has_pet" and len(atom.arguments) == 2:
            person = str(atom.arguments[0]).strip('"')
            pet = str(atom.arguments[1]).strip('"')
            if person not in person_data:
                person_data[person] = {}
            person_data[person]["pet"] = pet
            
        elif atom.name == "lives_in" and len(atom.arguments) == 2:
            person = str(atom.arguments[0]).strip('"')
            house = int(str(atom.arguments[1]))
            if person not in person_data:
                person_data[person] = {}
            person_data[person]["house"] = house
    
    for person, attrs in person_data.items():
        solution["assignments"].append({
            "person": person,
            "color": attrs.get("color", ""),
            "pet": attrs.get("pet", ""),
            "house": attrs.get("house", 0)
        })
    
    solution["assignments"].sort(key=lambda x: x["house"])

result = ctl.solve(on_model=on_model)

if result.satisfiable and solution:
    print(json.dumps(solution, indent=2))
else:
    print(json.dumps({"error": "No solution exists", 
                      "reason": "Constraints are unsatisfiable"}))
