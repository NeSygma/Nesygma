import clingo
import json

def solve_protein_folding(sequence):
    ctl = clingo.Control(["1"])
    
    n = len(sequence)
    
    program = f"""
"""
    
    for i, residue_type in enumerate(sequence):
        res_type = residue_type.lower()
        program += f'residue({i}, {res_type}).\n'
    
    program += f"""
index(0..{n-1}).
coord(-4..4).

adjacent(X1, Y1, X2, Y2) :- coord(X1), coord(Y1), coord(X2), coord(Y2),
    |X1 - X2| + |Y1 - Y2| == 1.

1 {{ at(I, X, Y) : coord(X), coord(Y) }} 1 :- index(I).

:- at(I1, X, Y), at(I2, X, Y), I1 != I2.

:- index(I), I < {n-1}, at(I, X1, Y1), at(I+1, X2, Y2),
   not adjacent(X1, Y1, X2, Y2).

hh_contact(I1, I2) :- I1 < I2,
    residue(I1, h), residue(I2, h),
    at(I1, X1, Y1), at(I2, X2, Y2),
    adjacent(X1, Y1, X2, Y2),
    I2 - I1 > 1.

total_contacts(N) :- N = #count {{ I1, I2 : hh_contact(I1, I2) }}.

:- total_contacts(N), N < 3.

#show at/3.
#show hh_contact/2.
#show total_contacts/1.
"""
    
    ctl.add("base", [], program)
    ctl.ground([("base", [])])
    
    solution = None
    
    def on_model(model):
        nonlocal solution
        atoms = model.symbols(atoms=True)
        
        coordinates = {}
        
        for atom in atoms:
            if atom.name == "at" and len(atom.arguments) == 3:
                idx = atom.arguments[0].number
                x = atom.arguments[1].number
                y = atom.arguments[2].number
                coordinates[idx] = [x, y]
        
        coord_list = [coordinates[i] for i in range(n)]
        
        solution = {
            "coordinates": coord_list,
            "sequence": sequence
        }
    
    result = ctl.solve(on_model=on_model)
    
    if result.satisfiable:
        return solution
    else:
        return {"error": "No solution exists", "reason": "UNSAT"}

sequence = "HPPHPPHH"
solution = solve_protein_folding(sequence)
print(json.dumps(solution, indent=2))
