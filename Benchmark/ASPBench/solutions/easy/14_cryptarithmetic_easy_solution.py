import clingo
import json

program = """
letter(s; e; n; d; m; o; r; y).
digit(0..9).

1 { assign(L, D) : digit(D) } 1 :- letter(L).

:- assign(L1, D), assign(L2, D), L1 != L2.

:- assign(s, 0).
:- assign(m, 0).

carry(0..1).

1 { carry_col(0, C) : carry(C) } 1.
1 { carry_col(1, C) : carry(C) } 1.
1 { carry_col(2, C) : carry(C) } 1.
1 { carry_col(3, C) : carry(C) } 1.

:- assign(d, D), assign(e, E), assign(y, Y), carry_col(0, C0),
   D + E != Y + 10*C0.

:- assign(n, N), assign(r, R), assign(e, E), 
   carry_col(0, C0), carry_col(1, C1),
   N + R + C0 != E + 10*C1.

:- assign(e, E), assign(o, O), assign(n, N),
   carry_col(1, C1), carry_col(2, C2),
   E + O + C1 != N + 10*C2.

:- assign(s, S), assign(m, M), assign(o, O),
   carry_col(2, C2), carry_col(3, C3),
   S + M + C2 != O + 10*C3.

:- assign(m, M), carry_col(3, C3), C3 != M.
"""

ctl = clingo.Control(["1"])
ctl.add("base", [], program)
ctl.ground([("base", [])])

solution_found = False
solution_data = None

def on_model(model):
    global solution_found, solution_data
    solution_found = True
    assignment = {}
    for atom in model.symbols(atoms=True):
        if atom.name == "assign" and len(atom.arguments) == 2:
            letter = str(atom.arguments[0])
            digit = atom.arguments[1].number
            assignment[letter.upper()] = digit
    solution_data = assignment

result = ctl.solve(on_model=on_model)

if result.satisfiable and solution_found:
    send = (solution_data['S'] * 1000 + solution_data['E'] * 100 + 
            solution_data['N'] * 10 + solution_data['D'])
    more = (solution_data['M'] * 1000 + solution_data['O'] * 100 + 
            solution_data['R'] * 10 + solution_data['E'])
    money = (solution_data['M'] * 10000 + solution_data['O'] * 1000 + 
             solution_data['N'] * 100 + solution_data['E'] * 10 + 
             solution_data['Y'])
    
    is_valid = (send + more == money)
    equation_str = f"{send} + {more} = {money}"
    
    output = {
        "assignment": solution_data,
        "equation": f"SEND + MORE = MONEY becomes {equation_str}",
        "valid": is_valid
    }
    
    print(json.dumps(output, indent=2))
else:
    print(json.dumps({"error": "No solution exists", 
                      "reason": "Constraints cannot be satisfied"}))
