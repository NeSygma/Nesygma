import clingo
import json

program = """
person("Alice"). person("Bob"). person("Carol"). person("Dave").
person("Eve"). person("Frank"). person("Grace"). person("Henry").

has_skill("Alice", "Programming"). has_skill("Alice", "Design").
has_skill("Bob", "Programming"). has_skill("Bob", "Testing").
has_skill("Carol", "Design"). has_skill("Carol", "Management").
has_skill("Dave", "Testing"). has_skill("Dave", "Management").
has_skill("Eve", "Programming"). has_skill("Eve", "Documentation").
has_skill("Frank", "Design"). has_skill("Frank", "Documentation").
has_skill("Grace", "Testing"). has_skill("Grace", "Documentation").
has_skill("Henry", "Management"). has_skill("Henry", "Documentation").

required_skill("Programming"). required_skill("Design").
required_skill("Testing"). required_skill("Management").

team(1). team(2).

1 { assigned(P, T) : team(T) } 1 :- person(P).

:- team(T), #count { P : assigned(P, T) } != 4.

:- team(T), required_skill(S), 
   #count { P : assigned(P, T), has_skill(P, S) } = 0.

team_skill_count(T, S, C) :- team(T), required_skill(S), 
    C = #count { P : assigned(P, T), has_skill(P, S) }.

#minimize { C-1, T, S : team_skill_count(T, S, C), C > 1 }.
"""

ctl = clingo.Control(["1"])
ctl.add("base", [], program)
ctl.ground([("base", [])])

solution = None

def on_model(model):
    global solution
    solution = {"teams": [[], []]}
    
    for atom in model.symbols(atoms=True):
        if atom.name == "assigned" and len(atom.arguments) == 2:
            person = str(atom.arguments[0]).strip('"')
            team_num = atom.arguments[1].number
            solution["teams"][team_num - 1].append(person)

result = ctl.solve(on_model=on_model)

if result.satisfiable and solution:
    print(json.dumps(solution, indent=2))
else:
    print(json.dumps({"error": "No solution exists", 
                      "reason": "Could not find valid team assignment"}))
