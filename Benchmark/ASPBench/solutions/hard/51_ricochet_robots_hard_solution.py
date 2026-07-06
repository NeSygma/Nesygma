import clingo
import json

def solve_ricochet_robots():
    ctl = clingo.Control(["1"])
    
    program = """
    row(0..4).
    col(0..4).
    
    robot("A"). robot("B"). robot("C").
    
    at("A", 0, 1, 0).
    at("B", 1, 1, 0).
    at("C", 3, 1, 0).
    
    target(2, 3).
    
    wall(0, 0). wall(0, 1). wall(0, 2). wall(0, 3). wall(0, 4).
    wall(1, 0). wall(1, 1). wall(1, 3). wall(1, 4).
    wall(2, 0). wall(2, 1). wall(2, 3). wall(2, 4).
    
    #const max_time = 7.
    time(0..max_time-1).
    
    adjacent(R1, C1, R2, C2) :- row(R1), col(C1), row(R2), col(C2),
        R2 = R1 + 1, C2 = C1.
    adjacent(R1, C1, R2, C2) :- row(R1), col(C1), row(R2), col(C2),
        R2 = R1 - 1, C2 = C1.
    adjacent(R1, C1, R2, C2) :- row(R1), col(C1), row(R2), col(C2),
        R2 = R1, C2 = C1 + 1, not wall(C1, R1).
    adjacent(R1, C1, R2, C2) :- row(R1), col(C1), row(R2), col(C2),
        R2 = R1, C2 = C1 - 1, not wall(C2, R2).
    
    1 { move(Robot, R1, C1, R2, C2, T) : 
        robot(Robot), at(Robot, R1, C1, T), adjacent(R1, C1, R2, C2) } 1 
        :- time(T).
    
    at(Robot, R2, C2, T+1) :- move(Robot, R1, C1, R2, C2, T).
    
    at(Robot, R, C, T+1) :- at(Robot, R, C, T), time(T+1),
        not move(Robot, R, C, _, _, T).
    
    :- at(Robot1, R, C, T), at(Robot2, R, C, T), Robot1 != Robot2.
    
    :- at(Robot, R1, C1, T), at(Robot, R2, C2, T), (R1, C1) != (R2, C2).
    
    :- target(TR, TC), not at("A", TR, TC, max_time).
    
    :- #count { Robot, R1, C1, R2, C2, T : 
        move(Robot, R1, C1, R2, C2, T) } > 7.
    
    #show move/6.
    """
    
    ctl.add("base", [], program)
    ctl.ground([("base", [])])
    
    solution_data = None
    
    def on_model(model):
        nonlocal solution_data
        atoms = model.symbols(atoms=True)
        
        moves = []
        for atom in atoms:
            if atom.name == "move" and len(atom.arguments) == 6:
                robot = str(atom.arguments[0])[1:-1]
                r1 = atom.arguments[1].number
                c1 = atom.arguments[2].number
                r2 = atom.arguments[3].number
                c2 = atom.arguments[4].number
                t = atom.arguments[5].number
                moves.append({
                    "robot": robot,
                    "from": [r1, c1],
                    "to": [r2, c2],
                    "time": t
                })
        
        moves.sort(key=lambda x: x["time"])
        
        final_positions = {
            "A": [0, 1],
            "B": [1, 1],
            "C": [3, 1]
        }
        
        for move in moves:
            final_positions[move["robot"]] = move["to"]
        
        sequence = [{"robot": m["robot"], "from": m["from"], "to": m["to"]} 
                    for m in moves]
        
        solution_data = {
            "solution_found": True,
            "moves": len(moves),
            "sequence": sequence,
            "final_positions": final_positions
        }
    
    result = ctl.solve(on_model=on_model)
    
    if result.satisfiable and solution_data:
        return solution_data
    else:
        return {
            "solution_found": False,
            "error": "No solution found within 7 moves"
        }

solution = solve_ricochet_robots()
print(json.dumps(solution, indent=2))
