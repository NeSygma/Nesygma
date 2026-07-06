import clingo
import json

asp_program = """
letter(d). letter(o). letter(n). letter(a). letter(l).
letter(g). letter(e). letter(r). letter(b). letter(t).

digit(0..9).

1 { assign(L, D) : digit(D) } 1 :- letter(L).
1 { assign(L, D) : letter(L) } 1 :- digit(D).

:- assign(d, 0).
:- assign(g, 0).
:- assign(r, 0).

carry(0, 0) :- assign(d, D), D + D < 10.
carry(0, 1) :- assign(d, D), D + D >= 10.
:- assign(d, D), assign(t, T), carry(0, C0), D + D != 10*C0 + T.

carry(1, 0) :- assign(l, L), carry(0, C0), L + L + C0 < 10.
carry(1, 1) :- assign(l, L), carry(0, C0), L + L + C0 >= 10.
:- assign(l, L), assign(r, R), carry(0, C0), carry(1, C1), 
   L + L + C0 != 10*C1 + R.

carry(2, 0) :- assign(a, A), carry(1, C1), A + A + C1 < 10.
carry(2, 1) :- assign(a, A), carry(1, C1), A + A + C1 >= 10.
:- assign(a, A), assign(e, E), carry(1, C1), carry(2, C2),
   A + A + C1 != 10*C2 + E.

carry(3, 0) :- assign(n, N), assign(r, R), carry(2, C2), N + R + C2 < 10.
carry(3, 1) :- assign(n, N), assign(r, R), carry(2, C2), N + R + C2 >= 10.
:- assign(n, N), assign(r, R), assign(b, B), carry(2, C2), carry(3, C3),
   N + R + C2 != 10*C3 + B.

carry(4, 0) :- assign(o, O), assign(e, E), carry(3, C3), O + E + C3 < 10.
carry(4, 1) :- assign(o, O), assign(e, E), carry(3, C3), O + E + C3 >= 10.
:- assign(o, O), assign(e, E), carry(3, C3), carry(4, C4),
   O + E + C3 != 10*C4 + O.

:- assign(d, D), assign(g, G), assign(r, R), carry(4, C4),
   D + G + C4 != R.
"""

ctl = clingo.Control(["1"])
ctl.add("base", [], asp_program)
ctl.ground([("base", [])])

solution_data = None

def on_model(model):
    global solution_data
    assignment = {}
    for atom in model.symbols(atoms=True):
        if atom.name == "assign" and len(atom.arguments) == 2:
            letter = str(atom.arguments[0])
            digit = atom.arguments[1].number
            assignment[letter.upper()] = digit
    solution_data = assignment

result = ctl.solve(on_model=on_model)

if result.satisfiable:
    donald = (solution_data['D'] * 100000 + solution_data['O'] * 10000 + 
              solution_data['N'] * 1000 + solution_data['A'] * 100 + 
              solution_data['L'] * 10 + solution_data['D'])
    
    gerald = (solution_data['G'] * 100000 + solution_data['E'] * 10000 + 
              solution_data['R'] * 1000 + solution_data['A'] * 100 + 
              solution_data['L'] * 10 + solution_data['D'])
    
    robert = (solution_data['R'] * 100000 + solution_data['O'] * 10000 + 
              solution_data['B'] * 1000 + solution_data['E'] * 100 + 
              solution_data['R'] * 10 + solution_data['T'])
    
    is_valid = (donald + gerald == robert)
    
    output = {
        "assignment": solution_data,
        "equation": f"DONALD + GERALD = ROBERT becomes {donald} + {gerald} = {robert}",
        "valid": is_valid
    }
    print(json.dumps(output, indent=2))
else:
    print(json.dumps({"error": "No solution exists", "reason": "UNSAT"}))
