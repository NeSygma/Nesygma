import clingo
import json

asp_program = """
element(1..20).

set_data(0, 1). set_data(1, 1). set_data(2, 1).
set_data(3, 1). set_data(4, 1). set_data(5, 1).
set_data(6, 1). set_data(7, 1). set_data(8, 1).
set_data(9, 4). set_data(10, 4). set_data(11, 4).
set_data(12, 4). set_data(13, 4).

contains(0, 1). contains(0, 2). contains(0, 3). contains(0, 4). contains(0, 5).
contains(1, 1). contains(1, 6). contains(1, 11). contains(1, 16).
contains(2, 2). contains(2, 7). contains(2, 12). contains(2, 17).
contains(3, 3). contains(3, 8). contains(3, 13). contains(3, 18).
contains(4, 4). contains(4, 9). contains(4, 14). contains(4, 19).
contains(5, 5). contains(5, 10). contains(5, 15). contains(5, 20).
contains(6, 6). contains(6, 7). contains(6, 8). contains(6, 9). contains(6, 10).
contains(7, 1). contains(7, 3). contains(7, 5). contains(7, 7). contains(7, 9).
contains(8, 2). contains(8, 4). contains(8, 6). contains(8, 8). contains(8, 10).
contains(9, 1). contains(9, 2). contains(9, 3). contains(9, 4). contains(9, 5).
contains(9, 6). contains(9, 7).
contains(10, 11). contains(10, 12). contains(10, 13). contains(10, 14).
contains(10, 15).
contains(11, 8). contains(11, 9). contains(11, 10).
contains(12, 1). contains(12, 5). contains(12, 10). contains(12, 15).
contains(13, 16). contains(13, 17). contains(13, 18). contains(13, 19).
contains(13, 20).

category(0, "A"). category(1, "A"). category(2, "A").
category(3, "B"). category(4, "B"). category(5, "B").
category(6, "C"). category(7, "C"). category(8, "C").

specialized(9). specialized(10). specialized(11). specialized(12).
specialized(13).

{ selected(S) : set_data(S, _) }.

covered(E) :- selected(S), contains(S, E).
:- element(E), not covered(E).

:- selected(9), not selected(0).
:- selected(11), not selected(6).

:- selected(12), selected(13).

has_specialized :- selected(S), specialized(S).
has_category(Cat) :- selected(S), category(S, Cat).

:- has_specialized, not has_category("A").
:- has_specialized, not has_category("B").
:- has_specialized, not has_category("C").

coverage_count(E, N) :- element(E), 
    N = #count { S : selected(S), contains(S, E) }.

over_covered(E) :- coverage_count(E, N), N > 3.
over_covered_count(C) :- C = #count { E : over_covered(E) }.

base_cost(C) :- C = #sum { Cost, S : selected(S), set_data(S, Cost) }.

total_cost(T) :- base_cost(B), over_covered_count(OC), T = B + 2 * OC.

:- total_cost(T), T > 5.

#minimize { T : total_cost(T) }.
"""

ctl = clingo.Control(["1"])
ctl.add("base", [], asp_program)
ctl.ground([("base", [])])

solution_data = None

def on_model(model):
    global solution_data
    
    selected_sets = []
    covered_elements = set()
    base_cost = 0
    over_covered_count = 0
    total_cost = 0
    
    for atom in model.symbols(atoms=True):
        if atom.name == "selected" and len(atom.arguments) == 1:
            selected_sets.append(atom.arguments[0].number)
        elif atom.name == "covered" and len(atom.arguments) == 1:
            covered_elements.add(atom.arguments[0].number)
        elif atom.name == "base_cost" and len(atom.arguments) == 1:
            base_cost = atom.arguments[0].number
        elif atom.name == "over_covered_count" and len(atom.arguments) == 1:
            over_covered_count = atom.arguments[0].number
        elif atom.name == "total_cost" and len(atom.arguments) == 1:
            total_cost = atom.arguments[0].number
    
    redundancy_penalty = 2 * over_covered_count
    selected_sets.sort()
    covered_elements = sorted(list(covered_elements))
    
    solution_data = {
        "selected_sets": selected_sets,
        "total_sets": len(selected_sets),
        "covered_elements": covered_elements,
        "base_cost": base_cost,
        "redundancy_penalty": redundancy_penalty,
        "total_cost": total_cost
    }

result = ctl.solve(on_model=on_model)

if result.satisfiable:
    print(json.dumps(solution_data))
else:
    print(json.dumps({
        "error": "No solution exists",
        "reason": "Problem constraints are unsatisfiable"
    }))
