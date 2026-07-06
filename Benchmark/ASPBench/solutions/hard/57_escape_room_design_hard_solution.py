import clingo
import json

puzzle_data = [
    (1, "R1", 1, "search", [], [], []),
    (2, "R1", 1, "logic", [1], [], ["key_red"]),
    (3, "R2", 2, "physical", [2], [], []),
    (4, "R2", 2, "search", [3], ["key_red"], []),
    (5, "R2", 2, "logic", [4], [], ["uv_light"]),
    (6, "R1", 3, "search", [5], ["uv_light"], []),
    (7, "R1", 3, "logic", [6], [], ["key_blue"]),
    (8, "R2", 3, "physical", [7], [], ["crowbar"]),
    (9, "R3", 3, "search", [8], ["key_blue"], []),
    (10, "R4", 3, "physical", [9], ["crowbar"], []),
    (11, "R4", 4, "logic", [10], [], []),
    (12, "R3", 4, "search", [11], ["uv_light"], []),
    (13, "R3", 4, "logic", [12], [], ["gear_1"]),
    (14, "R4", 4, "search", [13], [], []),
    (15, "R5", 4, "physical", [14], ["crowbar"], ["gear_2"]),
    (16, "R5", 5, "logic", [15], [], []),
    (17, "R5", 5, "search", [16], ["uv_light"], ["gear_3"]),
    (18, "R5", 5, "logic", [17], ["key_red", "key_blue"], []),
]

def generate_asp_program(puzzle_data):
    facts = []
    
    for pid, room, diff, theme, prereqs, req_items, yield_items in puzzle_data:
        facts.append(f'puzzle({pid}, "{room}", {diff}, "{theme}").')
        
        for prereq in prereqs:
            facts.append(f'prerequisite({pid}, {prereq}).')
        
        for item in req_items:
            facts.append(f'requires_item({pid}, "{item}").')
        
        for item in yield_items:
            facts.append(f'yields_item({pid}, "{item}").')
    
    adjacencies = [
        ("R1", "R2"), ("R2", "R1"),
        ("R2", "R3"), ("R3", "R2"),
        ("R3", "R4"), ("R4", "R3"),
        ("R4", "R5"), ("R5", "R4")
    ]
    for r1, r2 in adjacencies:
        facts.append(f'adjacent_rooms("{r1}", "{r2}").')
    
    facts.append('position_num(1..18).')
    
    asp_program = "\n".join(facts) + "\n\n"
    
    asp_program += """
1 { position(P, Pos) : position_num(Pos) } 1 :- puzzle(P, _, _, _).

1 { position(P, Pos) : puzzle(P, _, _, _) } 1 :- position_num(Pos).

:- prerequisite(P1, P2), position(P1, Pos1), position(P2, Pos2), Pos2 >= Pos1.

has_item(Item, Pos) :- position_num(Pos), yields_item(P, Item), position(P, YieldPos), YieldPos < Pos.

:- requires_item(P, Item), position(P, Pos), not has_item(Item, Pos).

:- position(P1, Pos), position(P2, Pos+1), 
   puzzle(P1, Room1, _, _), puzzle(P2, Room2, _, _),
   Room1 != Room2, not adjacent_rooms(Room1, Room2).

:- position(P1, Pos), position(P2, Pos+1),
   puzzle(P1, _, _, Theme), puzzle(P2, _, _, Theme).

:- position(P1, Pos), position(P2, Pos+1),
   puzzle(P1, _, Diff1, _), puzzle(P2, _, Diff2, _),
   |Diff1 - Diff2| > 1.
"""
    
    return asp_program

asp_program = generate_asp_program(puzzle_data)

ctl = clingo.Control(["1"])
ctl.add("base", [], asp_program)
ctl.ground([("base", [])])

solution_data = None

def on_model(model):
    global solution_data
    atoms = model.symbols(atoms=True)
    
    positions = {}
    for atom in atoms:
        if atom.name == "position" and len(atom.arguments) == 2:
            puzzle_id = atom.arguments[0].number
            pos = atom.arguments[1].number
            positions[pos] = puzzle_id
    
    solution_data = positions

result = ctl.solve(on_model=on_model)

if result.satisfiable:
    puzzle_dict = {}
    for pid, room, diff, theme, prereqs, req_items, yield_items in puzzle_data:
        puzzle_dict[pid] = {
            "puzzle_id": pid,
            "room": room,
            "difficulty": diff,
            "theme": theme,
            "prerequisites": prereqs,
            "requires": req_items,
            "yields": yield_items
        }
    
    puzzle_order = [solution_data[i] for i in range(1, 19)]
    room_progression = [puzzle_dict[pid]["room"] for pid in puzzle_order]
    difficulty_progression = [puzzle_dict[pid]["difficulty"] for pid in puzzle_order]
    theme_progression = [puzzle_dict[pid]["theme"] for pid in puzzle_order]
    puzzle_details = [puzzle_dict[i] for i in range(1, 19)]
    
    output = {
        "puzzle_order": puzzle_order,
        "room_progression": room_progression,
        "difficulty_progression": difficulty_progression,
        "theme_progression": theme_progression,
        "all_constraints_satisfied": True,
        "puzzle_details": puzzle_details
    }
    
    print(json.dumps(output, indent=2))
else:
    print(json.dumps({"error": "No solution exists", "reason": "Constraints cannot be satisfied"}))
