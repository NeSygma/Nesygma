import clingo
import json

asp_program = """
die(a;b;c;d).
face(1..4).
value(1..8).

1 { has_value(D, F, V) : value(V) } 1 :- die(D), face(F).

die_sum(D, S) :- die(D), S = #sum { V,F : has_value(D, F, V) }.
:- die_sum(D1, S1), die_sum(D2, S2), D1 != D2, S1 != S2.

uses_value(D, V) :- has_value(D, _, V).

same_value_set(D1, D2) :- die(D1), die(D2), D1 < D2,
    not different_value_set(D1, D2).

different_value_set(D1, D2) :- die(D1), die(D2), D1 < D2,
    value(V), uses_value(D1, V), not uses_value(D2, V).
    
different_value_set(D1, D2) :- die(D1), die(D2), D1 < D2,
    value(V), uses_value(D2, V), not uses_value(D1, V).

:- same_value_set(D1, D2).

wins(D1, D2, W) :- die(D1), die(D2), D1 != D2,
    W = #count { F1, F2 : has_value(D1, F1, V1), has_value(D2, F2, V2), V1 > V2 }.

:- wins(a, b, W), W <= 8.
:- wins(b, c, W), W <= 8.
:- wins(c, d, W), W <= 8.
:- wins(d, a, W), W <= 8.

#show has_value/3.
#show die_sum/2.
#show wins/3.
"""

def solve_nontransitive_dice():
    ctl = clingo.Control(["1"])
    ctl.add("base", [], asp_program)
    ctl.ground([("base", [])])
    
    solution = None
    
    def on_model(m):
        nonlocal solution
        atoms = m.symbols(atoms=True)
        
        dice_config = {'a': [], 'b': [], 'c': [], 'd': []}
        die_sums = {}
        win_counts = {}
        
        for atom in atoms:
            if atom.name == "has_value" and len(atom.arguments) == 3:
                die_name = str(atom.arguments[0])
                value = atom.arguments[2].number
                dice_config[die_name].append(value)
            
            elif atom.name == "die_sum" and len(atom.arguments) == 2:
                die_name = str(atom.arguments[0])
                sum_val = atom.arguments[1].number
                die_sums[die_name] = sum_val
            
            elif atom.name == "wins" and len(atom.arguments) == 3:
                die1 = str(atom.arguments[0])
                die2 = str(atom.arguments[1])
                count = atom.arguments[2].number
                win_counts[f"{die1}_beats_{die2}"] = count
        
        for die in dice_config:
            dice_config[die].sort()
        
        solution = {
            'dice_config': dice_config,
            'die_sums': die_sums,
            'win_counts': win_counts
        }
    
    result = ctl.solve(on_model=on_model)
    
    if result.satisfiable:
        return solution
    else:
        return None

def format_output(solution):
    dice_output = {
        'A': solution['dice_config']['a'],
        'B': solution['dice_config']['b'],
        'C': solution['dice_config']['c'],
        'D': solution['dice_config']['d']
    }
    
    common_sum = list(solution['die_sums'].values())[0]
    
    win_counts_output = {
        'A_beats_B': solution['win_counts']['a_beats_b'],
        'B_beats_C': solution['win_counts']['b_beats_c'],
        'C_beats_D': solution['win_counts']['c_beats_d'],
        'D_beats_A': solution['win_counts']['d_beats_a']
    }
    
    output = {
        'dice': dice_output,
        'analysis': {
            'common_sum': common_sum,
            'win_counts': win_counts_output
        }
    }
    
    return output

solution = solve_nontransitive_dice()

if solution:
    final_output = format_output(solution)
    print(json.dumps(final_output, indent=2))
else:
    print(json.dumps({"error": "No solution exists", 
                      "reason": "No valid nontransitive dice configuration found"}))
