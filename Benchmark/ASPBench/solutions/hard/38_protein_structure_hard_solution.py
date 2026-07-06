import clingo
import json

def solve_protein_folding():
    ctl = clingo.Control(["1"])
    
    program = """
    residue(1, "H").
    residue(2, "P").
    residue(3, "H").
    residue(4, "P").
    residue(5, "H").
    residue(6, "H").
    residue(7, "P").
    residue(8, "H").
    residue(9, "P").
    residue(10, "H").
    
    position(1..10).
    coord(-5..5).
    
    1 { at(Pos, X, Y) : coord(X), coord(Y) } 1 :- position(Pos).
    
    :- at(Pos1, X, Y), at(Pos2, X, Y), Pos1 != Pos2.
    
    :- at(Pos, X1, Y1), at(Pos+1, X2, Y2), position(Pos), Pos < 10,
       |X1 - X2| + |Y1 - Y2| != 1.
    
    hh_contact(Pos1, Pos2) :- 
        residue(Pos1, "H"), residue(Pos2, "H"),
        at(Pos1, X1, Y1), at(Pos2, X2, Y2),
        Pos1 < Pos2,
        Pos2 - Pos1 > 1,
        |X1 - X2| + |Y1 - Y2| = 1.
    
    :- #count { Pos1, Pos2 : hh_contact(Pos1, Pos2) } != 4.
    
    #show at/3.
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
                pos = atom.arguments[0].number
                x = atom.arguments[1].number
                y = atom.arguments[2].number
                coordinates[pos] = [x, y]
        
        solution = coordinates
    
    result = ctl.solve(on_model=on_model)
    
    return result, solution

result, solution = solve_protein_folding()

if result.satisfiable:
    output = {
        "sequence": "HPHPHHPHPH",
        "coordinates": [solution[i] for i in range(1, 11)]
    }
    print(json.dumps(output))
else:
    print(json.dumps({"error": "No solution exists", "reason": "UNSAT"}))
