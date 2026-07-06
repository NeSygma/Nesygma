import clingo
import json

asp_program = """
row(1..4).
col(1..4).
value(1..16).

prime(2). prime(3). prime(5). prime(7).

corner(1,1). corner(1,4). corner(4,1). corner(4,4).

1 { cell(R, C, V) : value(V) } 1 :- row(R), col(C).

:- value(V), #count { R,C : cell(R,C,V) } != 1.

:- row(R), #sum { V,C : cell(R,C,V) } != 34.

:- col(C), #sum { V,R : cell(R,C,V) } != 34.

:- #sum { V,R : cell(R,R,V) } != 34.

:- #sum { V,R : cell(R,5-R,V) } != 34.

:- cell(R, C, V1), cell(5-R, 5-C, V2), V1 + V2 != 17.

:- #sum { V,R,C : cell(R,C,V), R >= 1, R <= 2, C >= 1, C <= 2 } != 34.

:- #sum { V,R,C : cell(R,C,V), R >= 1, R <= 2, C >= 3, C <= 4 } != 34.

:- #sum { V,R,C : cell(R,C,V), R >= 3, R <= 4, C >= 1, C <= 2 } != 34.

:- #sum { V,R,C : cell(R,C,V), R >= 3, R <= 4, C >= 3, C <= 4 } != 34.

:- corner(R, C), cell(R, C, V), prime(V).

#show cell/3.
"""

ctl = clingo.Control(["1"])
ctl.add("base", [], asp_program)
ctl.ground([("base", [])])

solution_found = False
grid = [[0 for _ in range(4)] for _ in range(4)]

def on_model(model):
    global solution_found, grid
    solution_found = True
    
    for atom in model.symbols(atoms=True):
        if atom.name == "cell" and len(atom.arguments) == 3:
            r = atom.arguments[0].number
            c = atom.arguments[1].number
            v = atom.arguments[2].number
            grid[r-1][c-1] = v

result = ctl.solve(on_model=on_model)

if solution_found:
    def verify_solution(grid):
        is_symmetrical = True
        for r in range(4):
            for c in range(4):
                opposite_r = 3 - r
                opposite_c = 3 - c
                if grid[r][c] + grid[opposite_r][opposite_c] != 17:
                    is_symmetrical = False
        
        quadrants = [
            [(0,0), (0,1), (1,0), (1,1)],
            [(0,2), (0,3), (1,2), (1,3)],
            [(2,0), (2,1), (3,0), (3,1)],
            [(2,2), (2,3), (3,2), (3,3)]
        ]
        
        is_quadrant_valid = True
        for quad in quadrants:
            quad_sum = sum(grid[r][c] for r, c in quad)
            if quad_sum != 34:
                is_quadrant_valid = False
        
        primes = {2, 3, 5, 7}
        corners = [(0,0), (0,3), (3,0), (3,3)]
        is_prime_valid = True
        for r, c in corners:
            if grid[r][c] in primes:
                is_prime_valid = False
        
        return is_symmetrical, is_quadrant_valid, is_prime_valid
    
    is_sym, is_quad, is_prime = verify_solution(grid)
    
    output = {
        "square": grid,
        "magic_sum": 34,
        "properties": {
            "is_symmetrical_pairs": is_sym,
            "is_quadrant_sum_valid": is_quad,
            "is_prime_placement_valid": is_prime
        },
        "valid": is_sym and is_quad and is_prime
    }
    
    print(json.dumps(output, indent=2))
else:
    print(json.dumps({"error": "No solution exists", "reason": "UNSAT"}))
