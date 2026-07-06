import clingo
import json

words_data = {
    "CAT": ["C", "A", "T"],
    "ACE": ["A", "C", "E"],
    "TEA": ["T", "E", "A"],
    "EAR": ["E", "A", "R"],
    "ATE": ["A", "T", "E"],
    "RAT": ["R", "A", "T"],
    "CAR": ["C", "A", "R"],
    "TAR": ["T", "A", "R"]
}

def generate_asp_program():
    program = """
row(0..5).
col(0..5).

black(0,0).
black(0,5).
black(5,0).
black(5,5).

direction("h").
direction("v").

"""
    
    for word, letters in words_data.items():
        program += f'word("{word}").\n'
        for pos, letter in enumerate(letters):
            program += f'word_letter("{word}", {pos}, "{letter}").\n'
    
    program += """
1 { placed(W, R, C, D) : row(R), col(C), direction(D) } 1 :- word(W).

:- placed(W, R, C, _), black(R, C).

:- placed(W, R, C, "h"), C + 2 > 5.

:- placed(W, R, C, "v"), R + 2 > 5.

:- placed(W, R, C, "h"), black(R, C+1).
:- placed(W, R, C, "h"), black(R, C+2).

:- placed(W, R, C, "v"), black(R+1, C).
:- placed(W, R, C, "v"), black(R+2, C).

cell(R, C+P, L) :- placed(W, R, C, "h"), word_letter(W, P, L), 
    P >= 0, P <= 2, col(C+P).

cell(R+P, C, L) :- placed(W, R, C, "v"), word_letter(W, P, L), 
    P >= 0, P <= 2, row(R+P).

:- cell(R, C, L1), cell(R, C, L2), L1 != L2.

has_h_word(R, C) :- placed(W, R, C, "h"), col(C).
has_h_word(R, C) :- placed(W, R, C-1, "h"), C > 0, col(C).
has_h_word(R, C) :- placed(W, R, C-2, "h"), C > 1, col(C).

has_v_word(R, C) :- placed(W, R, C, "v"), row(R).
has_v_word(R, C) :- placed(W, R-1, C, "v"), R > 0, row(R).
has_v_word(R, C) :- placed(W, R-2, C, "v"), R > 1, row(R).

intersection(R, C) :- has_h_word(R, C), has_v_word(R, C), cell(R, C, _).

:- #count { R, C : intersection(R, C) } < 3.

adjacent(R1, C1, R2, C2) :- cell(R1, C1, _), cell(R2, C2, _), 
    R1 = R2, C2 = C1 + 1, row(R1), col(C1), col(C2).
adjacent(R1, C1, R2, C2) :- cell(R1, C1, _), cell(R2, C2, _), 
    R1 = R2, C2 = C1 - 1, row(R1), col(C1), col(C2).
adjacent(R1, C1, R2, C2) :- cell(R1, C1, _), cell(R2, C2, _), 
    R2 = R1 + 1, C1 = C2, row(R1), row(R2), col(C1).
adjacent(R1, C1, R2, C2) :- cell(R1, C1, _), cell(R2, C2, _), 
    R2 = R1 - 1, C1 = C2, row(R1), row(R2), col(C1).

root_cell(R, C) :- cell(R, C, _), R = #min { R2 : cell(R2, _, _) }, 
    C = #min { C2 : cell(R, C2, _) }.

reachable(R, C) :- root_cell(R, C).
reachable(R2, C2) :- reachable(R1, C1), adjacent(R1, C1, R2, C2).
reachable(R2, C2) :- reachable(R1, C1), adjacent(R2, C2, R1, C1).

:- cell(R, C, _), not reachable(R, C).

#show placed/4.
"""
    
    return program

def build_grid(placements):
    grid = [[' ' for _ in range(6)] for _ in range(6)]
    
    grid[0][0] = '#'
    grid[0][5] = '#'
    grid[5][0] = '#'
    grid[5][5] = '#'
    
    for p in placements:
        word = p['word']
        row = p['row']
        col = p['col']
        direction = p['direction']
        
        if direction == 'horizontal':
            for i, letter in enumerate(word):
                if col + i < 6:
                    grid[row][col + i] = letter
        else:
            for i, letter in enumerate(word):
                if row + i < 6:
                    grid[row + i][col] = letter
    
    return grid

asp_program = generate_asp_program()
ctl = clingo.Control(["1"])
ctl.add("base", [], asp_program)
ctl.ground([("base", [])])

solution_found = False
placements = []

def on_model(model):
    global solution_found, placements
    solution_found = True
    placements = []
    
    for atom in model.symbols(atoms=True):
        if atom.name == "placed" and len(atom.arguments) == 4:
            word = str(atom.arguments[0]).strip('"')
            row = atom.arguments[1].number
            col = atom.arguments[2].number
            direction = str(atom.arguments[3]).strip('"')
            placements.append({
                "word": word,
                "row": row,
                "col": col,
                "direction": "horizontal" if direction == "h" else "vertical"
            })

result = ctl.solve(on_model=on_model)

if result.satisfiable:
    grid = build_grid(placements)
    output = {
        "grid": grid,
        "placements": placements,
        "theme": "Simple English Words"
    }
    print(json.dumps(output, indent=2))
else:
    print(json.dumps({"error": "No solution exists", 
                      "reason": "Unable to satisfy all constraints"}))
