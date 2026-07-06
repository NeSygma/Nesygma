import clingo
import json

def generate_asp_program(initial_grid, max_time=10):
    """Generate ASP program for Conway's Game of Life simulation"""
    
    program = """
cell(0..4, 0..4).
time(0..10).

"""
    
    for x in range(5):
        for y in range(5):
            if initial_grid[x][y] == 1:
                program += f"alive({x}, {y}, 0).\n"
    
    program += """
neighbor(X1, Y1, X2, Y2) :- 
    cell(X1, Y1), cell(X2, Y2),
    X2 >= X1-1, X2 <= X1+1,
    Y2 >= Y1-1, Y2 <= Y1+1,
    (X1, Y1) != (X2, Y2).

neighbor_count(X, Y, T, N) :- 
    cell(X, Y), time(T),
    N = #count { X2, Y2 : neighbor(X, Y, X2, Y2), alive(X2, Y2, T) }.

alive(X, Y, T+1) :- 
    alive(X, Y, T), 
    neighbor_count(X, Y, T, N),
    N >= 2, N <= 3,
    time(T), T < 10.

alive(X, Y, T+1) :- 
    cell(X, Y),
    not alive(X, Y, T),
    neighbor_count(X, Y, T, 3),
    time(T), T < 10.

#show alive/3.
"""
    
    return program

def solve_game_of_life(asp_program):
    """Solve the Game of Life simulation using clingo"""
    
    ctl = clingo.Control(["1"])
    ctl.add("base", [], asp_program)
    ctl.ground([("base", [])])
    
    solution = None
    
    def on_model(m):
        nonlocal solution
        atoms = m.symbols(atoms=True)
        
        alive_cells = {}
        for atom in atoms:
            if atom.name == "alive" and len(atom.arguments) == 3:
                x = atom.arguments[0].number
                y = atom.arguments[1].number
                t = atom.arguments[2].number
                
                if t not in alive_cells:
                    alive_cells[t] = []
                alive_cells[t].append((x, y))
        
        solution = alive_cells
    
    result = ctl.solve(on_model=on_model)
    
    if result.satisfiable:
        return solution
    else:
        return None

def cells_to_grid(alive_cells, size=5):
    """Convert list of alive cell coordinates to 5x5 grid"""
    grid = [[0 for _ in range(size)] for _ in range(size)]
    for x, y in alive_cells:
        grid[x][y] = 1
    return grid

def grid_to_tuple(grid):
    """Convert grid to hashable tuple for comparison"""
    return tuple(tuple(row) for row in grid)

def detect_cycle(grids_by_time):
    """Detect the first cycle in the grid evolution"""
    
    seen_states = {}
    
    for t in sorted(grids_by_time.keys()):
        grid_tuple = grid_to_tuple(grids_by_time[t])
        
        if grid_tuple in seen_states:
            cycle_start = seen_states[grid_tuple]
            cycle_end = t
            period = cycle_end - cycle_start
            
            cycle_states = []
            for cycle_t in range(cycle_start, cycle_end):
                cycle_states.append(grids_by_time[cycle_t])
            
            return {
                'cycle_start': cycle_start,
                'cycle_end': cycle_end,
                'period': period,
                'states': cycle_states
            }
        else:
            seen_states[grid_tuple] = t
    
    return None

def format_output(cycle_info):
    """Format the cycle information as required JSON output"""
    
    if not cycle_info:
        return {"error": "No stable pattern found", 
                "reason": "No cycle detected within simulation time"}
    
    output = {
        "stable_patterns": [
            {
                "pattern_id": 1,
                "period": cycle_info['period'],
                "states": cycle_info['states']
            }
        ]
    }
    
    return output

initial_grid = [
    [0, 1, 0, 1, 0],
    [1, 0, 1, 0, 1],
    [0, 1, 0, 1, 0],
    [1, 0, 1, 0, 1],
    [0, 1, 0, 1, 0]
]

asp_program = generate_asp_program(initial_grid)
alive_cells_by_time = solve_game_of_life(asp_program)

if alive_cells_by_time:
    grids_by_time = {}
    for t in sorted(alive_cells_by_time.keys()):
        grids_by_time[t] = cells_to_grid(alive_cells_by_time.get(t, []))
    
    cycle_info = detect_cycle(grids_by_time)
    output = format_output(cycle_info)
    print(json.dumps(output, indent=2))
else:
    print(json.dumps({"error": "No solution exists", 
                      "reason": "ASP solver returned UNSAT"}))
