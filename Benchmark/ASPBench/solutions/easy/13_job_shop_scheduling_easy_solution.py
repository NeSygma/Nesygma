import clingo
import json

def create_asp_program():
    program = """
job(1..3).
operation(J, 1..3) :- job(J).
machine(1..3).

duration(1, 1, 3).
duration(1, 2, 2).
duration(1, 3, 4).
requires(1, 1, 1).
requires(1, 2, 2).
requires(1, 3, 3).

duration(2, 1, 2).
duration(2, 2, 5).
duration(2, 3, 1).
requires(2, 1, 2).
requires(2, 2, 1).
requires(2, 3, 3).

duration(3, 1, 4).
duration(3, 2, 1).
duration(3, 3, 3).
requires(3, 1, 3).
requires(3, 2, 1).
requires(3, 3, 2).

time(0..11).

1 { start(J, O, T) : time(T) } 1 :- operation(J, O).

:- start(J, O, T1), start(J, O+1, T2), duration(J, O, D), 
   operation(J, O), operation(J, O+1), T2 < T1 + D.

:- start(J1, O1, T1), start(J2, O2, T2),
   requires(J1, O1, M), requires(J2, O2, M),
   duration(J1, O1, D1),
   (J1, O1) != (J2, O2),
   T1 <= T2, T2 < T1 + D1.

:- start(J, O, T), duration(J, O, D), T + D > 11.

completes(J, O, T + D) :- start(J, O, T), duration(J, O, D).

makespan(M) :- M = #max { T : completes(_, _, T) }.

#minimize { M : makespan(M) }.
"""
    return program

def solve_job_shop():
    ctl = clingo.Control(["1"])
    
    program = create_asp_program()
    ctl.add("base", [], program)
    ctl.ground([("base", [])])
    
    solution_data = None
    
    def on_model(model):
        nonlocal solution_data
        atoms = model.symbols(atoms=True)
        
        schedule = []
        makespan_value = 0
        
        duration_map = {}
        machine_map = {}
        
        for atom in atoms:
            if atom.name == "duration" and len(atom.arguments) == 3:
                job = atom.arguments[0].number
                op = atom.arguments[1].number
                duration_val = atom.arguments[2].number
                duration_map[(job, op)] = duration_val
            
            if atom.name == "requires" and len(atom.arguments) == 3:
                job = atom.arguments[0].number
                op = atom.arguments[1].number
                machine_val = atom.arguments[2].number
                machine_map[(job, op)] = machine_val
        
        for atom in atoms:
            if atom.name == "start" and len(atom.arguments) == 3:
                job = atom.arguments[0].number
                op = atom.arguments[1].number
                start_time = atom.arguments[2].number
                
                schedule.append({
                    "job": job,
                    "operation": op,
                    "machine": machine_map.get((job, op)),
                    "start": start_time,
                    "duration": duration_map.get((job, op))
                })
            
            elif atom.name == "makespan" and len(atom.arguments) == 1:
                makespan_value = atom.arguments[0].number
        
        schedule.sort(key=lambda x: (x["job"], x["operation"]))
        
        solution_data = {
            "schedule": schedule,
            "makespan": makespan_value,
            "feasible": True
        }
    
    result = ctl.solve(on_model=on_model)
    
    if result.satisfiable:
        return solution_data
    else:
        return {
            "schedule": [],
            "makespan": 0,
            "feasible": False,
            "error": "No solution exists within the given time horizon"
        }

solution = solve_job_shop()
print(json.dumps(solution, indent=2))
