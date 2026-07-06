import clingo
import json


def create_asp_program():
    program = """
    % Facts - Exams
    exam(e1). exam(e2). exam(e3). exam(e4). exam(e5). exam(e6).
    
    % Facts - Time slots (3 slots)
    time_slot(1). time_slot(2). time_slot(3).
    
    % Facts - Rooms with capacity
    room(r1, 3). room(r2, 3).
    
    % Facts - Student enrollments
    enrolled(s1, e1). enrolled(s1, e3). enrolled(s1, e5).
    enrolled(s2, e1). enrolled(s2, e4). enrolled(s2, e6).
    enrolled(s3, e2). enrolled(s3, e3). enrolled(s3, e6).
    enrolled(s4, e2). enrolled(s4, e4). enrolled(s4, e5).
    
    % Calculate exam sizes (number of students per exam)
    exam_size(E, N) :- exam(E), N = #count { S : enrolled(S, E) }.
    
    % Choice rule: Each exam assigned to exactly one time slot and room
    1 { scheduled(E, T, R) : time_slot(T), room(R, _) } 1 :- exam(E).
    
    % Constraint: Room capacity must not be exceeded
    :- scheduled(E, T, R), room(R, Cap), exam_size(E, Size), Size > Cap.
    
    % Constraint: No student conflicts
    :- enrolled(S, E1), enrolled(S, E2), E1 != E2,
       scheduled(E1, T, _), scheduled(E2, T, _).
    
    #show scheduled/3.
    """
    return program


def solve_exam_scheduling():
    ctl = clingo.Control(["1"])
    
    program = create_asp_program()
    ctl.add("base", [], program)
    ctl.ground([("base", [])])
    
    solution_data = None
    
    def on_model(model):
        nonlocal solution_data
        atoms = model.symbols(atoms=True)
        
        schedule = []
        room_usage = {}
        
        for atom in atoms:
            if atom.name == "scheduled" and len(atom.arguments) == 3:
                exam = str(atom.arguments[0]).upper()
                time_slot = atom.arguments[1].number
                room = str(atom.arguments[2]).upper()
                
                if room not in room_usage:
                    room_usage[room] = 0
                room_usage[room] += 1
                
                schedule.append({
                    "exam": exam,
                    "day": 1,
                    "time_slot": time_slot,
                    "room": room,
                    "duration": 2
                })
        
        schedule.sort(key=lambda x: x["exam"])
        
        solution_data = {
            "schedule": schedule,
            "conflicts_resolved": True,
            "room_utilization": room_usage
        }
    
    result = ctl.solve(on_model=on_model)
    
    if result.satisfiable:
        return solution_data
    else:
        return {
            "error": "No solution exists",
            "reason": "Unable to schedule all exams without conflicts",
            "conflicts_resolved": False
        }


solution = solve_exam_scheduling()
print(json.dumps(solution, indent=2))
