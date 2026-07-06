import clingo
import json

universe = [1, 2, 3, 4, 5, 6, 7, 8]
sets_data = {
    0: [1, 2, 3],
    1: [2, 4, 5],
    2: [3, 6, 7],
    3: [1, 4, 8],
    4: [5, 6, 7, 8],
    5: [1, 2, 6]
}

facts = []

for elem in universe:
    facts.append(f'element({elem}).')

for set_id in sets_data.keys():
    facts.append(f'set_id({set_id}).')

for set_id, elements in sets_data.items():
    for elem in elements:
        facts.append(f'contains({set_id}, {elem}).')

asp_program = "\n".join(facts) + """

{ selected(S) } :- set_id(S).

covered(E) :- selected(S), contains(S, E).

:- element(E), not covered(E).

#minimize { 1,S : selected(S) }.
"""

ctl = clingo.Control(["0"])
ctl.add("base", [], asp_program)
ctl.ground([("base", [])])

solution_data = None

def on_model(model):
    global solution_data
    
    selected_sets = []
    covered_elements = set()
    
    for atom in model.symbols(atoms=True):
        if atom.name == "selected" and len(atom.arguments) == 1:
            set_id = atom.arguments[0].number
            selected_sets.append(set_id)
            covered_elements.update(sets_data[set_id])
    
    selected_sets.sort()
    covered_elements = sorted(list(covered_elements))
    
    solution_data = {
        "selected_sets": selected_sets,
        "total_sets": len(selected_sets),
        "covered_elements": covered_elements
    }

result = ctl.solve(on_model=on_model)

if result.satisfiable and solution_data:
    print(json.dumps(solution_data))
else:
    print(json.dumps({"error": "No solution exists", "reason": "UNSAT"}))
