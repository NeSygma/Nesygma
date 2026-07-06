import clingo
import json

def create_asp_program():
    program = """
    exam(e1; e2; e3; e4; e5; e6; e7; e8).
    
    student(s1; s2; s3; s4; s5; s6).
    
    enrolled(s1, e1). enrolled(s1, e3). enrolled(s1, e7).
    enrolled(s2, e2). enrolled(s2, e4). enrolled(s2, e8).
    enrolled(s3, e1). enrolled(s3, e5).
    enrolled(s4, e2). enrolled(s4, e6).
    enrolled(s5, e3). enrolled(s5, e5). enrolled(s5, e8).
    enrolled(s6, e4). enrolled(s6, e6). enrolled(s6, e7).
    
    time_slot(1..4).
    
    room(r1). room_type(r1, classroom). room_capacity(r1, 2).
    room(r2). room_type(r2, classroom). room_capacity(r2, 2).
    room(r3). room_type(r3, lab). room_capacity(r3, 2).
    
    exam_requires(e1, classroom). exam_requires(e2, classroom).
    exam_requires(e3, classroom). exam_requires(e4, classroom).
    exam_requires(e5, classroom). exam_requires(e6, classroom).
    exam_requires(e7, lab). exam_requires(e8, lab).
    
    exam_enrollment_count(E, Count) :- exam(E), 
        Count = #count { S : enrolled(S, E) }.
    
    1 { scheduled(E, T, R) : time_slot(T), room(R), 
        room_type(R, Type), exam_requires(E, Type) } 1 :- exam(E).
    
    :- enrolled(S, E1), enrolled(S, E2), E1 != E2,
       scheduled(E1, T, _), scheduled(E2, T, _).
    
    :- scheduled(E1, T, R), scheduled(E2, T, R), E1 != E2.
    
    :- scheduled(E, _, R), exam_enrollment_count(E, Count), 
       room_capacity(R, Cap), Count > Cap.
    """
    return program

def solve_exam_scheduling():
    ctl = clingo.Control(["1"])
    
    program = create_asp_program()
    ctl.add("base", [], program)
    
    ctl.ground([("base", [])])
    
    solution = None
    
    def on_model(m):
        nonlocal solution
        atoms = m.symbols(atoms=True)
        schedule = []
        
        for atom in atoms:
            if atom.name == "scheduled" and len(atom.arguments) == 3:
                exam = str(atom.arguments[0]).upper()
                time_slot = atom.arguments[1].number
                room = str(atom.arguments[2]).upper()
                
                schedule.append({
                    "exam": exam,
                    "time_slot": time_slot,
                    "room": room
                })
        
        schedule.sort(key=lambda x: x["exam"])
        solution = schedule
    
    result = ctl.solve(on_model=on_model)
    
    if result.satisfiable:
        output = {
            "status": "SATISFIABLE",
            "schedule": solution
        }
    else:
        output = {
            "status": "UNSATISFIABLE",
            "reason": "No valid schedule exists that satisfies all constraints"
        }
    
    return output

result = solve_exam_scheduling()
print(json.dumps(result, indent=2))
