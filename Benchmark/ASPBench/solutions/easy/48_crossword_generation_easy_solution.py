import clingo
import json

asp_program = """
row(0..4).
col(0..4).

direction(horizontal).
direction(vertical).

word(0, "CODE", 4, "Programming instructions").
word(1, "DATA", 4, "Information").
word(2, "TECH", 4, "Technology short").
word(3, "CHIP", 4, "Computer component").
word(4, "BYTE", 4, "Data unit").
word(5, "NET", 3, "Internet short").

letter("CODE", 0, "C"). letter("CODE", 1, "O"). letter("CODE", 2, "D"). 
letter("CODE", 3, "E").
letter("DATA", 0, "D"). letter("DATA", 1, "A"). letter("DATA", 2, "T"). 
letter("DATA", 3, "A").
letter("TECH", 0, "T"). letter("TECH", 1, "E"). letter("TECH", 2, "C"). 
letter("TECH", 3, "H").
letter("CHIP", 0, "C"). letter("CHIP", 1, "H"). letter("CHIP", 2, "I"). 
letter("CHIP", 3, "P").
letter("BYTE", 0, "B"). letter("BYTE", 1, "Y"). letter("BYTE", 2, "T"). 
letter("BYTE", 3, "E").
letter("NET", 0, "N"). letter("NET", 1, "E"). letter("NET", 2, "T").

1 { placed(W, R, C, D) : row(R), col(C), direction(D) } 1 :- 
    word(W, _, _, _).

:- placed(W, R, C, horizontal), word(W, _, Len, _), C + Len - 1 > 4.
:- placed(W, R, C, vertical), word(W, _, Len, _), R + Len - 1 > 4.

occupies(W, R, C, Letter) :- 
    placed(W, StartR, StartC, horizontal),
    word(W, Text, _, _),
    letter(Text, Pos, Letter),
    R = StartR,
    C = StartC + Pos.

occupies(W, R, C, Letter) :- 
    placed(W, StartR, StartC, vertical),
    word(W, Text, _, _),
    letter(Text, Pos, Letter),
    R = StartR + Pos,
    C = StartC.

:- occupies(W1, R, C, L1), occupies(W2, R, C, L2), W1 != W2, L1 != L2.

intersection(W1, W2, R, C) :- 
    occupies(W1, R, C, L),
    occupies(W2, R, C, L),
    W1 < W2.

:- #count { W1, W2, R, C : intersection(W1, W2, R, C) } < 3.

#show placed/4.
#show occupies/4.
#show intersection/4.
"""

words_info = [
    ("CODE", "Programming instructions"),
    ("DATA", "Information"),
    ("TECH", "Technology short"),
    ("CHIP", "Computer component"),
    ("BYTE", "Data unit"),
    ("NET", "Internet short")
]

ctl = clingo.Control(["1"])
ctl.add("base", [], asp_program)
ctl.ground([("base", [])])

solution_data = None

def on_model(model):
    global solution_data
    placements = []
    occupancies = []
    intersections = []
    
    for atom in model.symbols(atoms=True):
        if atom.name == "placed" and len(atom.arguments) == 4:
            word_id = atom.arguments[0].number
            row = atom.arguments[1].number
            col = atom.arguments[2].number
            direction = str(atom.arguments[3])
            placements.append((word_id, row, col, direction))
        elif atom.name == "occupies" and len(atom.arguments) == 4:
            word_id = atom.arguments[0].number
            row = atom.arguments[1].number
            col = atom.arguments[2].number
            letter = str(atom.arguments[3]).strip('"')
            occupancies.append((word_id, row, col, letter))
        elif atom.name == "intersection" and len(atom.arguments) == 4:
            w1 = atom.arguments[0].number
            w2 = atom.arguments[1].number
            row = atom.arguments[2].number
            col = atom.arguments[3].number
            intersections.append((w1, w2, row, col))
    
    solution_data = {
        'placements': placements,
        'occupancies': occupancies,
        'intersections': intersections
    }

result = ctl.solve(on_model=on_model)

if result.satisfiable:
    grid = [[" " for _ in range(5)] for _ in range(5)]
    
    for word_id, row, col, letter in solution_data['occupancies']:
        grid[row][col] = letter
    
    words_array = []
    for word_id, row, col, direction in sorted(solution_data['placements']):
        word_text = words_info[word_id][0]
        clue = words_info[word_id][1]
        words_array.append({
            "word": word_text,
            "position": [row, col],
            "direction": direction,
            "clue": clue
        })
    
    intersections_array = []
    for w1, w2, row, col in solution_data['intersections']:
        letter = grid[row][col]
        placement1 = next(p for p in solution_data['placements'] if p[0] == w1)
        placement2 = next(p for p in solution_data['placements'] if p[0] == w2)
        
        _, r1, c1, dir1 = placement1
        _, r2, c2, dir2 = placement2
        
        if dir1 == "horizontal":
            pos1 = col - c1
        else:
            pos1 = row - r1
        
        if dir2 == "horizontal":
            pos2 = col - c2
        else:
            pos2 = row - r2
        
        intersections_array.append({
            "word1": w1,
            "word2": w2,
            "position1": pos1,
            "position2": pos2,
            "letter": letter
        })
    
    output = {
        "grid": grid,
        "words": words_array,
        "theme": "Technology",
        "intersections": intersections_array
    }
    
    print(json.dumps(output, indent=2))
else:
    print(json.dumps({"error": "No solution exists", 
                      "reason": "Unable to place all words with required intersections"}))
