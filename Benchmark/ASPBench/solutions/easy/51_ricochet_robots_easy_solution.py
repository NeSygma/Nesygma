import clingo
import json

def solve_robot_puzzle():
    ctl = clingo.Control(["1"])
    
    program = """
    row(0..3).
    col(0..3).
    robot("A"; "B").
    
    at("A", 0, 1, 0).
    at("B", 1, 1, 0).
    
    target(2, 1).
    
    wall_vertical(2, 0).
    wall_vertical(2, 1).
    
    #const max_time = 10.
    time(0..max_time-1).
    timestep(0..max_time).
    
    valid_move(R, FromR, FromC, ToR, ToC, T) :- 
        at(R, FromR, FromC, T),
        ToR = FromR + 1, ToC = FromC,
        row(ToR), col(ToC), time(T).
    
    valid_move(R, FromR, FromC, ToR, ToC, T) :- 
        at(R, FromR, FromC, T),
        ToR = FromR - 1, ToC = FromC,
        row(ToR), col(ToC), time(T).
    
    valid_move(R, FromR, FromC, ToR, ToC, T) :- 
        at(R, FromR, FromC, T),
        ToR = FromR, ToC = FromC + 1,
        row(ToR), col(ToC), time(T).
    
    valid_move(R, FromR, FromC, ToR, ToC, T) :- 
        at(R, FromR, FromC, T),
        ToR = FromR, ToC = FromC - 1,
        row(ToR), col(ToC), time(T).
    
    0 { move(R, FromR, FromC, ToR, ToC, T) : 
        valid_move(R, FromR, FromC, ToR, ToC, T) } 1 :- time(T).
    
    :- move(R, FromR, FromC, ToR, ToC, T), 
       wall_vertical(FromC, FromR), 
       ToC == FromC + 1, ToR == FromR.
    
    :- move(R, FromR, FromC, ToR, ToC, T), 
       wall_vertical(ToC, ToR), 
       FromC == ToC + 1, FromR == ToR.
    
    at(R, ToR, ToC, T+1) :- move(R, FromR, FromC, ToR, ToC, T).
    
    at(R, Row, Col, T+1) :- at(R, Row, Col, T), timestep(T+1), 
        not move(R, Row, Col, _, _, T).
    
    :- at(R, Row1, Col1, T), at(R, Row2, Col2, T), 
       (Row1, Col1) != (Row2, Col2).
    
    :- at(R1, Row, Col, T), at(R2, Row, Col, T), R1 != R2.
    
    :- target(Row, Col), not at("A", Row, Col, max_time).
    
    total_moves(N) :- N = #count { R, FromR, FromC, ToR, ToC, T : 
        move(R, FromR, FromC, ToR, ToC, T) }.
    
    :- total_moves(N), N > 3.
    
    #show move/6.
    #show at/4.
    #show total_moves/1.
    """
    
    ctl.add("base", [], program)
    ctl.ground([("base", [])])
    
    solution_data = None
    
    def on_model(model):
        nonlocal solution_data
        atoms = model.symbols(atoms=True)
        
        moves = []
        all_positions = []
        total = 0
        
        for atom in atoms:
            if atom.name == "move" and len(atom.arguments) == 6:
                robot = str(atom.arguments[0]).strip('"')
                from_r = atom.arguments[1].number
                from_c = atom.arguments[2].number
                to_r = atom.arguments[3].number
                to_c = atom.arguments[4].number
                t = atom.arguments[5].number
                
                moves.append({
                    "robot": robot,
                    "from": [from_r, from_c],
                    "to": [to_r, to_c],
                    "time": t
                })
            
            elif atom.name == "total_moves" and len(atom.arguments) == 1:
                total = atom.arguments[0].number
            
            elif atom.name == "at" and len(atom.arguments) == 4:
                robot = str(atom.arguments[0]).strip('"')
                row = atom.arguments[1].number
                col = atom.arguments[2].number
                t = atom.arguments[3].number
                
                all_positions.append({
                    "robot": robot,
                    "row": row,
                    "col": col,
                    "time": t
                })
        
        final_positions = {}
        for pos in all_positions:
            if pos["time"] == 10:
                final_positions[pos["robot"]] = [pos["row"], pos["col"]]
        
        moves.sort(key=lambda x: x["time"])
        
        sequence = [{"robot": m["robot"], "from": m["from"], "to": m["to"]} 
                    for m in moves]
        
        solution_data = {
            "solution_found": True,
            "moves": total,
            "sequence": sequence,
            "final_positions": final_positions
        }
    
    result = ctl.solve(on_model=on_model)
    
    if result.satisfiable:
        return solution_data
    else:
        return {
            "solution_found": False,
            "error": "No solution exists"
        }

solution = solve_robot_puzzle()
print(json.dumps(solution, indent=2))
