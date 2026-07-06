import clingo
import json

def solve_course_scheduling():
    """Solve course scheduling problem using ASP with clingo"""
    
    program = """
course(0, 0, 30, sci).
course(1, 0, 25, sci).
course(2, 1, 40, sci).
course(3, 2, 50, hum).
course(4, 3, 45, hum).
course(5, 4, 60, eng).
course(6, 4, 55, eng).
course(7, 4, 50, eng).

room(0, 60).
room(1, 50).
room(2, 40).
room(3, 30).

room_feature(0, projector).
room_feature(1, projector).
room_feature(2, lab).
room_feature(2, projector).

time_slot(0).
time_slot(1).
time_slot(2).
time_slot(3).
time_slot(4).
time_slot(5).

teacher_available(0, 0).
teacher_available(0, 1).
teacher_available(0, 2).
teacher_available(1, 2).
teacher_available(1, 3).
teacher_available(1, 4).
teacher_available(2, 0).
teacher_available(2, 1).
teacher_available(2, 4).
teacher_available(2, 5).
teacher_available(3, 0).
teacher_available(3, 2).
teacher_available(3, 3).
teacher_available(3, 5).
teacher_available(4, 1).
teacher_available(4, 2).
teacher_available(4, 3).
teacher_available(4, 4).
teacher_available(4, 5).

course_requires(2, lab).
course_requires(5, projector).
course_requires(6, projector).
course_requires(7, projector).

prerequisite(0, 1).
prerequisite(5, 6).
prerequisite(6, 7).

student_conflict(1, 4).
student_conflict(2, 5).

1 { scheduled(C, R, T) : room(R, _), time_slot(T) } 1 :- course(C, _, _, _).

:- scheduled(C1, R, T), scheduled(C2, R, T), C1 != C2.

:- scheduled(C1, _, T), scheduled(C2, _, T), 
   course(C1, Tchr, _, _), course(C2, Tchr, _, _), C1 != C2.

:- scheduled(C, R, _), course(C, _, Students, _), room(R, Capacity), Students > Capacity.

:- scheduled(C, _, T), course(C, Tchr, _, _), not teacher_available(Tchr, T).

:- scheduled(C, R, _), course_requires(C, Feature), not room_feature(R, Feature).

:- scheduled(C1, _, T1), scheduled(C2, _, T2), prerequisite(C1, C2), T1 >= T2.

:- scheduled(C1, _, T), scheduled(C2, _, T), student_conflict(C1, C2).

:- #count { C : scheduled(C, _, 5) } > 2.

#minimize { 1,C1,C2 : scheduled(C1, _, T), scheduled(C2, _, T+1),
            course(C1, _, _, Dept), course(C2, _, _, Dept) }.

#show scheduled/3.
"""
    
    ctl = clingo.Control(["0"])
    ctl.add("base", [], program)
    ctl.ground([("base", [])])
    
    best_solution = None
    best_cost = float('inf')
    
    def on_model(m):
        nonlocal best_solution, best_cost
        atoms = m.symbols(atoms=True)
        assignments = []
        for atom in atoms:
            if atom.name == "scheduled" and len(atom.arguments) == 3:
                course = atom.arguments[0].number
                room = atom.arguments[1].number
                time_slot = atom.arguments[2].number
                assignments.append({
                    "course": course,
                    "room": room,
                    "time_slot": time_slot
                })
        
        cost = m.cost[0] if m.cost else 0
        assignments.sort(key=lambda x: x["course"])
        
        if cost < best_cost:
            best_cost = cost
            best_solution = {
                "cost": cost,
                "assignments": assignments
            }
    
    result = ctl.solve(on_model=on_model)
    
    if result.satisfiable:
        return best_solution
    else:
        return {"error": "No solution exists", "reason": "Constraints cannot be satisfied"}

if __name__ == "__main__":
    solution = solve_course_scheduling()
    print(json.dumps(solution, indent=2))
