import clingo
import json

program = """
puzzle(1, 1).
puzzle(2, 1).
puzzle(3, 2).
puzzle(4, 2).
puzzle(5, 3).
puzzle(6, 3).

depends(2, 1).
depends(3, 2).
depends(3, 4).
depends(4, 1).
depends(5, 3).
depends(6, 5).

pos(1..6).

1 { position(P, Pos) : pos(Pos) } 1 :- puzzle(P, _).
1 { position(P, Pos) : puzzle(P, _) } 1 :- pos(Pos).

:- depends(A, B), position(A, PosA), position(B, PosB), PosB >= PosA.
"""

ctl = clingo.Control(["1"])
ctl.add("base", [], program)
ctl.ground([("base", [])])

solution = None

def on_model(model):
    global solution
    atoms = model.symbols(atoms=True)
    positions = {}
    for atom in atoms:
        if atom.name == "position" and len(atom.arguments) == 2:
            puzzle_id = atom.arguments[0].number
            pos = atom.arguments[1].number
            positions[pos] = puzzle_id
    solution = positions

result = ctl.solve(on_model=on_model)

if result.satisfiable and solution:
    puzzle_data = {
        1: {"difficulty": 1, "prerequisites": []},
        2: {"difficulty": 1, "prerequisites": [1]},
        3: {"difficulty": 2, "prerequisites": [2, 4]},
        4: {"difficulty": 2, "prerequisites": [1]},
        5: {"difficulty": 3, "prerequisites": [3]},
        6: {"difficulty": 3, "prerequisites": [5]}
    }
    
    puzzle_order = [solution[pos] for pos in sorted(solution.keys())]
    difficulty_progression = [puzzle_data[pid]["difficulty"] 
                             for pid in puzzle_order]
    
    puzzle_details = []
    for pid in range(1, 7):
        puzzle_details.append({
            "puzzle_id": pid,
            "difficulty": puzzle_data[pid]["difficulty"],
            "prerequisites": puzzle_data[pid]["prerequisites"]
        })
    
    dependencies_satisfied = True
    for i, pid in enumerate(puzzle_order):
        prereqs = puzzle_data[pid]["prerequisites"]
        for prereq in prereqs:
            prereq_index = puzzle_order.index(prereq)
            if prereq_index >= i:
                dependencies_satisfied = False
                break
    
    output = {
        "puzzle_order": puzzle_order,
        "difficulty_progression": difficulty_progression,
        "dependencies_satisfied": dependencies_satisfied,
        "puzzle_details": puzzle_details
    }
    
    print(json.dumps(output, indent=2))
else:
    print(json.dumps({"error": "No solution exists", 
                     "reason": "Unable to find valid puzzle ordering"}))
