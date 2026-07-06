import clingo
import json

def create_asp_program():
    program = """
    nurse(1..5).
    day(1..10).
    shift(1..3).
    
    coverage(1, 2).
    coverage(2, 1).
    coverage(3, 1).
    
    { assigned(N, D, S) : shift(S) } :- nurse(N), day(D).
    
    :- day(D), shift(S), coverage(S, Required),
       #count { N : assigned(N, D, S) } != Required.
    
    :- nurse(N), day(D), #count { S : assigned(N, D, S) } > 1.
    
    :- assigned(N, D, 3), day(D), D < 10, assigned(N, D+1, 1).
    """
    return program

def solve_nurse_scheduling():
    ctl = clingo.Control(["1"])
    
    program = create_asp_program()
    ctl.add("base", [], program)
    
    ctl.ground([("base", [])])
    
    solution = None
    
    def on_model(m):
        nonlocal solution
        assignments = []
        for atom in m.symbols(atoms=True):
            if atom.name == "assigned" and len(atom.arguments) == 3:
                nurse = atom.arguments[0].number
                day = atom.arguments[1].number
                shift = atom.arguments[2].number
                assignments.append((nurse, day, shift))
        solution = assignments
    
    result = ctl.solve(on_model=on_model)
    
    if result.satisfiable:
        return solution
    else:
        return None

def format_solution(assignments):
    if assignments is None:
        return {"roster": None}
    
    roster = [[[], [], []] for _ in range(10)]
    
    for nurse, day, shift in assignments:
        roster[day - 1][shift - 1].append(nurse)
    
    for day_schedule in roster:
        for shift_nurses in day_schedule:
            shift_nurses.sort()
    
    return {"roster": roster}

assignments = solve_nurse_scheduling()
solution_json = format_solution(assignments)
print(json.dumps(solution_json))
