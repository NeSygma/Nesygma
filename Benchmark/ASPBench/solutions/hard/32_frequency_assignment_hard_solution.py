import clingo
import json

def solve_frequency_assignment():
    ctl = clingo.Control(["1"])
    
    program = """
    transmitter(t1). transmitter(t2). transmitter(t3). transmitter(t4). transmitter(t5).
    transmitter(t6). transmitter(t7). transmitter(t8). transmitter(t9). transmitter(t10).
    
    frequency(101, low, 10).
    frequency(102, low, 12).
    frequency(103, low, 15).
    
    frequency(201, mid, 20).
    frequency(202, mid, 22).
    frequency(203, mid, 25).
    frequency(204, mid, 28).
    
    frequency(301, high, 40).
    frequency(302, high, 45).
    
    allowed(t1, low). allowed(t2, low).
    
    allowed(t3, mid). allowed(t4, mid). allowed(t5, mid).
    
    allowed(t6, high).
    
    allowed(t7, low). allowed(t7, mid).
    allowed(t8, low). allowed(t8, mid).
    
    allowed(t9, mid). allowed(t9, high).
    allowed(t10, mid). allowed(t10, high).
    
    interferes(t1, t2). interferes(t2, t1).
    interferes(t1, t7). interferes(t7, t1).
    interferes(t2, t8). interferes(t8, t2).
    interferes(t3, t4). interferes(t4, t3).
    interferes(t3, t9). interferes(t9, t3).
    interferes(t4, t5). interferes(t5, t4).
    interferes(t4, t7). interferes(t7, t4).
    interferes(t5, t8). interferes(t8, t5).
    interferes(t5, t10). interferes(t10, t5).
    interferes(t6, t9). interferes(t9, t6).
    interferes(t6, t10). interferes(t10, t6).
    
    band_of(F, Band) :- frequency(F, Band, _).
    
    1 { assigned(T, F) : frequency(F, Band, _), allowed(T, Band) } 1 :- transmitter(T).
    
    :- assigned(T1, F1), assigned(T2, F2), interferes(T1, T2),
       band_of(F1, Band), band_of(F2, Band),
       |F1 - F2| <= 1.
    
    :- assigned(T1, F), assigned(T2, F), interferes(T1, T2), T1 != T2.
    
    total_cost(C) :- C = #sum { Cost, T : assigned(T, F), frequency(F, _, Cost) }.
    
    :- total_cost(C), C > 200.
    """
    
    ctl.add("base", [], program)
    ctl.ground([("base", [])])
    
    solution = None
    
    def on_model(m):
        nonlocal solution
        atoms = m.symbols(atoms=True)
        
        assignments = []
        total_cost = 0
        
        for atom in atoms:
            if atom.name == "assigned" and len(atom.arguments) == 2:
                transmitter = str(atom.arguments[0])
                frequency = atom.arguments[1].number
                
                for atom2 in atoms:
                    if atom2.name == "frequency" and len(atom2.arguments) == 3:
                        if atom2.arguments[0].number == frequency:
                            cost = atom2.arguments[2].number
                            total_cost += cost
                            break
                
                assignments.append({
                    "transmitter": transmitter,
                    "frequency": frequency
                })
            
            if atom.name == "total_cost" and len(atom.arguments) == 1:
                total_cost = atom.arguments[0].number
        
        assignments.sort(key=lambda x: x["transmitter"])
        
        solution = {
            "assignments": assignments,
            "total_cost": total_cost
        }
    
    result = ctl.solve(on_model=on_model)
    
    if result.satisfiable:
        return solution
    else:
        return {"error": "No solution exists", 
                "reason": "Constraints cannot be satisfied"}

solution = solve_frequency_assignment()
print(json.dumps(solution, indent=2))
