import clingo
import json

def solve_scheduling_problem():
    """Solve task scheduling problem with precedence constraints using ASP"""
    
    tasks_data = [
        {"id": 0, "duration": 4, "machines": [1], "prereqs": []},
        {"id": 1, "duration": 3, "machines": [2], "prereqs": []},
        {"id": 2, "duration": 5, "machines": [3], "prereqs": []},
        {"id": 3, "duration": 2, "machines": [1], "prereqs": [0]},
        {"id": 4, "duration": 6, "machines": [2], "prereqs": [1]},
        {"id": 5, "duration": 3, "machines": [1], "prereqs": [3]},
        {"id": 6, "duration": 4, "machines": [3], "prereqs": [2, 4]},
        {"id": 7, "duration": 5, "machines": [2], "prereqs": [4]},
        {"id": 8, "duration": 2, "machines": [1], "prereqs": [5]},
        {"id": 9, "duration": 3, "machines": [2, 3], "prereqs": [7, 8]},
    ]
    
    machines = [1, 2, 3]
    
    facts = []
    for task in tasks_data:
        tid = task["id"]
        duration = task["duration"]
        facts.append(f'task({tid}, {duration}).')
        
        for m in task["machines"]:
            facts.append(f'eligible({tid}, {m}).')
        
        for prereq in task["prereqs"]:
            facts.append(f'prereq({prereq}, {tid}).')
    
    for m in machines:
        facts.append(f'machine({m}).')
    
    asp_program = """
time(0..20).

1 { assigned(T, M) : eligible(T, M) } 1 :- task(T, _).
1 { start_time(T, S) : time(S) } 1 :- task(T, _).

end_time(T, E) :- start_time(T, S), task(T, D), E = S + D.
makespan(M) :- M = #max { E : end_time(_, E) }.

:- prereq(T1, T2), end_time(T1, E1), start_time(T2, S2), S2 < E1.

:- assigned(T1, M), assigned(T2, M), T1 < T2,
   start_time(T1, S1), end_time(T1, E1),
   start_time(T2, S2), end_time(T2, E2),
   S1 < E2, S2 < E1.

:- end_time(T, E), E > 20.
:- makespan(M), M > 17.

#minimize { E : makespan(E) }.
"""
    
    ctl = clingo.Control(["1"])
    full_program = "\n".join(facts) + "\n" + asp_program
    ctl.add("base", [], full_program)
    ctl.ground([("base", [])])
    
    solution = None
    
    def on_model(m):
        nonlocal solution
        atoms = m.symbols(atoms=True)
        
        schedule = {}
        for atom in atoms:
            if atom.name == "assigned" and len(atom.arguments) == 2:
                task_id = atom.arguments[0].number
                machine_id = atom.arguments[1].number
                if task_id not in schedule:
                    schedule[task_id] = {}
                schedule[task_id]["machine"] = machine_id
            
            elif atom.name == "start_time" and len(atom.arguments) == 2:
                task_id = atom.arguments[0].number
                start = atom.arguments[1].number
                if task_id not in schedule:
                    schedule[task_id] = {}
                schedule[task_id]["start_time"] = start
        
        schedule_array = []
        max_end = 0
        for task in tasks_data:
            tid = task["id"]
            if tid in schedule:
                start = schedule[tid]["start_time"]
                end = start + task["duration"]
                max_end = max(max_end, end)
                schedule_array.append({
                    "task": tid,
                    "machine": schedule[tid]["machine"],
                    "start_time": start,
                    "end_time": end
                })
        
        schedule_array.sort(key=lambda x: x["task"])
        
        solution = {
            "schedule": schedule_array,
            "makespan": max_end
        }
    
    result = ctl.solve(on_model=on_model)
    
    if not result.satisfiable:
        return {"error": "No solution exists", "reason": "Problem is unsatisfiable"}
    
    task_map = {t["id"]: t for t in tasks_data}
    
    def longest_path_to(task_id, memo={}):
        if task_id in memo:
            return memo[task_id]
        
        task = task_map[task_id]
        if not task["prereqs"]:
            path = [task_id]
            length = task["duration"]
        else:
            best_path = []
            best_length = 0
            for prereq in task["prereqs"]:
                prereq_path, prereq_length = longest_path_to(prereq, memo)
                if prereq_length > best_length:
                    best_length = prereq_length
                    best_path = prereq_path
            
            path = best_path + [task_id]
            length = best_length + task["duration"]
        
        memo[task_id] = (path, length)
        return path, length
    
    last_task = max(solution["schedule"], key=lambda x: x["end_time"])["task"]
    critical_path, _ = longest_path_to(last_task)
    solution["critical_path"] = critical_path
    
    return solution

if __name__ == "__main__":
    solution = solve_scheduling_problem()
    print(json.dumps(solution, indent=2))
