import clingo
import json

program = """
person("Evelyn"; "Frank"; "Grace"; "Henry"; "Iris").
location("Library"; "Park"; "Cafe"; "Museum"; "Studio").
hobby("Painting"; "Coding"; "Gardening"; "Baking"; "Sculpting").
snack("Apple"; "Muffin"; "Nuts"; "Yogurt"; "Tea").
project("A"; "B"; "C"; "D"; "E").

compatibility("Painting", "Apple", 3).
compatibility("Coding", "Muffin", 5).
compatibility("Gardening", "Nuts", 2).
compatibility("Baking", "Yogurt", 4).
compatibility("Sculpting", "Tea", 1).

1 { has_location(P, L) : location(L) } 1 :- person(P).
1 { has_hobby(P, H) : hobby(H) } 1 :- person(P).
1 { has_snack(P, S) : snack(S) } 1 :- person(P).
1 { has_project(P, Pr) : project(Pr) } 1 :- person(P).

1 { has_location(P, L) : person(P) } 1 :- location(L).
1 { has_hobby(P, H) : person(P) } 1 :- hobby(H).
1 { has_snack(P, S) : person(P) } 1 :- snack(S).
1 { has_project(P, Pr) : person(P) } 1 :- project(Pr).

:- has_hobby(P1, "Coding"), has_location(P1, L1),
   has_hobby(P2, "Gardening"), has_location(P2, L2),
   L1 >= L2.

:- has_hobby(P, H), H != "Painting", has_snack(P, "Apple").

hobby_sc("Sculpting"). hobby_sc("Coding").
:- #count { P : has_hobby(P, H), hobby_sc(H) } != 2.

:- has_project("Henry", Pr), Pr != "D".

:- has_location(P, "Museum"), has_snack(P, "Nuts").

:- has_project(P1, "E"), has_location(P1, L1),
   has_project(P2, "A"), has_location(P2, L2),
   L1 <= L2.

:- has_hobby(P1, "Baking"), has_project(P1, Pr1),
   has_location(P2, "Park"), has_project(P2, Pr2),
   Pr1 <= Pr2.

:- has_location("Frank", L), L != "Cafe".

:- has_hobby("Evelyn", "Gardening").

project_dist_2("A", "C"). project_dist_2("C", "A").
project_dist_2("B", "D"). project_dist_2("D", "B").
project_dist_2("C", "E"). project_dist_2("E", "C").

:- has_snack(P1, "Muffin"), has_project(P1, Pr1),
   has_hobby(P2, "Sculpting"), has_project(P2, Pr2),
   not project_dist_2(Pr1, Pr2).

total_score(Total) :- Total = #sum { Score, P : has_hobby(P, H), has_snack(P, S), compatibility(H, S, Score) }.
:- total_score(Total), Total != 15.

#show has_location/2.
#show has_hobby/2.
#show has_snack/2.
#show has_project/2.
"""

ctl = clingo.Control(["1"])
ctl.add("base", [], program)
ctl.ground([("base", [])])

solution_data = None

def on_model(model):
    global solution_data
    solution_data = {}
    
    for atom in model.symbols(atoms=True):
        if atom.name == "has_location" and len(atom.arguments) == 2:
            person = str(atom.arguments[0]).strip('"')
            location = str(atom.arguments[1]).strip('"')
            if person not in solution_data:
                solution_data[person] = {}
            solution_data[person]["location"] = location
            
        elif atom.name == "has_hobby" and len(atom.arguments) == 2:
            person = str(atom.arguments[0]).strip('"')
            hobby = str(atom.arguments[1]).strip('"')
            if person not in solution_data:
                solution_data[person] = {}
            solution_data[person]["hobby"] = hobby
            
        elif atom.name == "has_snack" and len(atom.arguments) == 2:
            person = str(atom.arguments[0]).strip('"')
            snack = str(atom.arguments[1]).strip('"')
            if person not in solution_data:
                solution_data[person] = {}
            solution_data[person]["snack"] = snack
            
        elif atom.name == "has_project" and len(atom.arguments) == 2:
            person = str(atom.arguments[0]).strip('"')
            project = str(atom.arguments[1]).strip('"')
            if person not in solution_data:
                solution_data[person] = {}
            solution_data[person]["project"] = project

result = ctl.solve(on_model=on_model)

if result.satisfiable and solution_data:
    output = {"assignments": []}
    for person in ["Evelyn", "Frank", "Grace", "Henry", "Iris"]:
        assignment = {
            "person": person,
            "location": solution_data[person]["location"],
            "hobby": solution_data[person]["hobby"],
            "snack": solution_data[person]["snack"],
            "project": solution_data[person]["project"]
        }
        output["assignments"].append(assignment)
    print(json.dumps(output, indent=2))
else:
    print(json.dumps({"error": "No solution exists"}))
