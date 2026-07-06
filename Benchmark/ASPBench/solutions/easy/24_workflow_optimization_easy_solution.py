import clingo
import json

task_data = [
    (0, 3, []),
    (1, 2, []),
    (2, 4, [0]),
    (3, 1, [1]),
    (4, 5, [2, 3]),
    (5, 2, [0]),
    (6, 3, [4]),
    (7, 2, [5, 6])
]

def generate_asp_program(tasks):
    facts = []
    
    for task_id, duration, prereqs in tasks:
        facts.append(f"task({task_id}, {duration}).")
        for prereq in prereqs:
            facts.append(f"prerequisite({task_id}, {prereq}).")
    
    max_time = sum(d for _, d, _ in tasks)
    facts.append(f"time(0..{max_time}).")
    
    asp_program = " ".join(facts) + """
    
    1 { start(T, Time) : time(Time) } 1 :- task(T, _).
    
    end(T, EndTime) :- start(T, StartTime), task(T, Duration), EndTime = StartTime + Duration.
    
    :- start(T, StartTime), prerequisite(T, PrereqTask), end(PrereqTask, PrereqEnd), StartTime < PrereqEnd.
    
    makespan(M) :- M = #max { EndTime : end(_, EndTime) }.
    
    :- makespan(M), M > 17.
    
    #minimize { M : makespan(M) }.
    """
    
    return asp_program

def compute_critical_path(schedule, task_data):
    task_dict = {t[0]: {"duration": t[1], "prereqs": t[2]} for t in task_data}
    
    max_end_time = max(schedule[t]["end"] for t in schedule)
    last_tasks = [t for t in schedule if schedule[t]["end"] == max_end_time]
    
    def find_critical_path(task_id):
        task_info = task_dict[task_id]
        task_schedule = schedule[task_id]
        
        if not task_info["prereqs"]:
            return [task_id]
        
        critical_prereq = None
        for prereq in task_info["prereqs"]:
            if schedule[prereq]["end"] == task_schedule["start"]:
                critical_prereq = prereq
                break
        
        if critical_prereq is None:
            critical_prereq = max(task_info["prereqs"], 
                                 key=lambda p: schedule[p]["end"])
        
        path = find_critical_path(critical_prereq)
        path.append(task_id)
        return path
    
    return find_critical_path(last_tasks[0])

program = generate_asp_program(task_data)

ctl = clingo.Control(["1"])
ctl.add("base", [], program)
ctl.ground([("base", [])])

solution_data = None

def on_model(model):
    global solution_data
    atoms = model.symbols(atoms=True)
    
    schedule = {}
    makespan_value = 0
    
    for atom in atoms:
        if atom.name == "start" and len(atom.arguments) == 2:
            task_id = atom.arguments[0].number
            start_time = atom.arguments[1].number
            schedule[task_id] = {"start": start_time}
        elif atom.name == "end" and len(atom.arguments) == 2:
            task_id = atom.arguments[0].number
            end_time = atom.arguments[1].number
            if task_id in schedule:
                schedule[task_id]["end"] = end_time
            else:
                schedule[task_id] = {"end": end_time}
        elif atom.name == "makespan" and len(atom.arguments) == 1:
            makespan_value = atom.arguments[0].number
    
    solution_data = {
        "schedule": schedule,
        "makespan": makespan_value
    }

result = ctl.solve(on_model=on_model)

if result.satisfiable:
    critical_path = compute_critical_path(solution_data["schedule"], task_data)
    
    schedule_array = []
    for task_id in sorted(solution_data["schedule"].keys()):
        task_info = solution_data["schedule"][task_id]
        schedule_array.append({
            "task": task_id,
            "start_time": task_info["start"],
            "end_time": task_info["end"]
        })
    
    output = {
        "schedule": schedule_array,
        "makespan": solution_data["makespan"],
        "critical_path": critical_path
    }
    
    print(json.dumps(output, indent=2))
else:
    print(json.dumps({"error": "No solution exists", "reason": "UNSAT"}))
