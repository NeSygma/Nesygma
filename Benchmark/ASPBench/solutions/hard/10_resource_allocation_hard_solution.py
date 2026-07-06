import clingo
import json

def solve_assembly_scheduling():
    ctl = clingo.Control(["1"])
    
    program = """
    task("T1", 2, "Welding", "A", 6).
    task("T2", 3, "Assembly", "B", 8).
    task("T3", 1, "Inspection", "A", 7).
    task("T4", 2, "Welding", "A", 9).
    task("T5", 3, "Assembly", "C", 10).
    task("T6", 2, "Programming", "B", 9).
    task("T7", 1, "Inspection", "A", 8).
    task("T8", 2, "Assembly", "C", 11).
    task("T9", 3, "Welding", "A", 12).
    task("T10", 2, "Programming", "B", 11).
    task("T11", 1, "Assembly", "C", 10).
    task("T12", 2, "Inspection", "A", 13).
    
    worker("W1", 15).
    worker("W2", 12).
    worker("W3", 20).
    worker("W4", 18).
    worker("W5", 16).
    
    has_skill("W1", "Welding").
    has_skill("W1", "Inspection").
    has_skill("W2", "Assembly").
    has_skill("W2", "Inspection").
    has_skill("W3", "Programming").
    has_skill("W3", "Assembly").
    has_skill("W4", "Welding").
    has_skill("W4", "Programming").
    has_skill("W5", "Assembly").
    has_skill("W5", "Inspection").
    has_skill("W5", "Welding").
    
    machine("M1", "A", 3).
    machine("M2", "B", 2).
    machine("M3", "C", 4).
    
    precedence("T1", "T3").
    precedence("T1", "T4").
    precedence("T2", "T5").
    precedence("T2", "T6").
    precedence("T3", "T7").
    precedence("T4", "T9").
    precedence("T5", "T8").
    precedence("T6", "T10").
    precedence("T7", "T12").
    precedence("T8", "T11").
    
    time(0..13).
    
    1 { assigned(T, W, M, Start) : 
        worker(W, _), has_skill(W, Skill),
        machine(M, MType, _),
        time(Start) } 1 :- task(T, _, Skill, MType, _).
    
    finish_time(T, Start + Duration) :- assigned(T, _, _, Start), 
                                         task(T, Duration, _, _, _).
    
    :- finish_time(T, FinishTime), task(T, _, _, _, Deadline), 
       FinishTime > Deadline.
    
    :- precedence(T1, T2), finish_time(T1, F1), assigned(T2, _, _, S2), 
       F1 > S2.
    
    :- worker(W, _), time(T), 
       #count { Task : assigned(Task, W, _, Start), 
                task(Task, Duration, _, _, _), 
                Start <= T, T < Start + Duration } > 3.
    
    :- machine(M, _, _), time(T),
       #count { Task : assigned(Task, _, M, Start), 
                task(Task, Duration, _, _, _),
                Start <= T, T < Start + Duration } > 2.
    
    task_cost(T, (WCost + MCost) * Duration) :- 
        assigned(T, W, M, _),
        task(T, Duration, _, _, _),
        worker(W, WCost),
        machine(M, _, MCost).
    
    total_cost(TotalCost) :- TotalCost = #sum { Cost, T : task_cost(T, Cost) }.
    
    :- total_cost(Cost), Cost > 470.
    
    makespan(MaxFinish) :- MaxFinish = #max { F : finish_time(_, F) }.
    
    :- makespan(M), M > 9.
    
    #show assigned/4.
    #show makespan/1.
    #show total_cost/1.
    """
    
    ctl.add("base", [], program)
    ctl.ground([("base", [])])
    
    solution_data = None
    
    def on_model(model):
        nonlocal solution_data
        atoms = model.symbols(atoms=True)
        
        schedule = []
        makespan_val = None
        total_cost_val = None
        
        for atom in atoms:
            if atom.name == "assigned" and len(atom.arguments) == 4:
                task = str(atom.arguments[0]).strip('"')
                worker = str(atom.arguments[1]).strip('"')
                machine = str(atom.arguments[2]).strip('"')
                start = atom.arguments[3].number
                schedule.append({
                    "task": task,
                    "worker": worker,
                    "machine": machine,
                    "start": start
                })
            elif atom.name == "makespan" and len(atom.arguments) == 1:
                makespan_val = atom.arguments[0].number
            elif atom.name == "total_cost" and len(atom.arguments) == 1:
                total_cost_val = atom.arguments[0].number
        
        schedule.sort(key=lambda x: x["task"])
        
        solution_data = {
            "schedule": schedule,
            "makespan": makespan_val,
            "total_cost": total_cost_val,
            "feasible": True
        }
    
    result = ctl.solve(on_model=on_model)
    
    if result.satisfiable:
        return solution_data
    else:
        return {
            "error": "No solution exists",
            "reason": "Could not find a schedule satisfying all constraints",
            "feasible": False
        }

solution = solve_assembly_scheduling()
print(json.dumps(solution, indent=2))
