import clingo
import json

asp_program = """
job(1..4).

operation(1, 1, 4, 1, 0).
operation(1, 2, 5, 3, 1).
operation(1, 3, 3, 2, 0).

operation(2, 1, 6, 2, 0).
operation(2, 2, 4, 4, 0).
operation(2, 3, 2, 1, 0).
operation(2, 4, 3, 3, 0).

operation(3, 1, 7, 4, 1).
operation(3, 2, 6, 1, 0).
operation(3, 3, 2, 3, 0).

operation(4, 1, 2, 3, 0).
operation(4, 2, 5, 2, 0).
operation(4, 3, 3, 4, 0).
operation(4, 4, 4, 1, 1).

due_date(1, 20).
due_date(2, 25).
due_date(3, 22).
due_date(4, 30).

penalty_weight(1, 3).
penalty_weight(2, 1).
penalty_weight(3, 2).
penalty_weight(4, 1).

maintenance(2, 10, 11).
maintenance(4, 15, 16).

time(0..40).
machine(1..4).

1 { start(J, O, T) : time(T) } 1 :- operation(J, O, _, _, _).

:- start(J, O1, T1), start(J, O2, T2), operation(J, O1, D1, _, _), 
   operation(J, O2, _, _, _), O2 = O1 + 1, T2 < T1 + D1.

:- start(J1, O1, T1), start(J2, O2, T2), 
   operation(J1, O1, D1, M, _), operation(J2, O2, D2, M, _),
   (J1, O1) != (J2, O2),
   T1 <= T2, T2 < T1 + D1.

:- start(J1, O1, T1), start(J2, O2, T2), 
   operation(J1, O1, D1, M, _), operation(J2, O2, D2, M, _),
   (J1, O1) != (J2, O2),
   T2 <= T1, T1 < T2 + D2.

:- start(J1, O1, T1), start(J2, O2, T2),
   operation(J1, O1, D1, _, 1), operation(J2, O2, D2, _, 1),
   (J1, O1) != (J2, O2),
   T1 <= T2, T2 < T1 + D1.

:- start(J1, O1, T1), start(J2, O2, T2),
   operation(J1, O1, D1, _, 1), operation(J2, O2, D2, _, 1),
   (J1, O1) != (J2, O2),
   T2 <= T1, T1 < T2 + D2.

:- start(J, O, T), operation(J, O, D, M, _), maintenance(M, MStart, MEnd),
   T <= MEnd, MStart < T + D.

job_finish(J, T + D) :- start(J, O, T), operation(J, O, D, _, _),
   not operation(J, O + 1, _, _, _).

makespan(MS) :- MS = #max { T : job_finish(_, T) }.

:- makespan(MS), MS > 24.

tardiness(J, Tard) :- job_finish(J, F), due_date(J, Due), Tard = F - Due, F > Due.
tardiness(J, 0) :- job_finish(J, F), due_date(J, Due), F <= Due.

total_penalty(TP) :- TP = #sum { Tard * W, J : tardiness(J, Tard), penalty_weight(J, W) }.

#show start/3.
#show makespan/1.
#show total_penalty/1.
#show job_finish/2.
#show tardiness/2.
"""

operations_data = {
    (1, 1): {'duration': 4, 'machine': 1, 'needs_master': 0},
    (1, 2): {'duration': 5, 'machine': 3, 'needs_master': 1},
    (1, 3): {'duration': 3, 'machine': 2, 'needs_master': 0},
    (2, 1): {'duration': 6, 'machine': 2, 'needs_master': 0},
    (2, 2): {'duration': 4, 'machine': 4, 'needs_master': 0},
    (2, 3): {'duration': 2, 'machine': 1, 'needs_master': 0},
    (2, 4): {'duration': 3, 'machine': 3, 'needs_master': 0},
    (3, 1): {'duration': 7, 'machine': 4, 'needs_master': 1},
    (3, 2): {'duration': 6, 'machine': 1, 'needs_master': 0},
    (3, 3): {'duration': 2, 'machine': 3, 'needs_master': 0},
    (4, 1): {'duration': 2, 'machine': 3, 'needs_master': 0},
    (4, 2): {'duration': 5, 'machine': 2, 'needs_master': 0},
    (4, 3): {'duration': 3, 'machine': 4, 'needs_master': 0},
    (4, 4): {'duration': 4, 'machine': 1, 'needs_master': 1},
}

due_dates = {1: 20, 2: 25, 3: 22, 4: 30}

ctl = clingo.Control(["1"])
ctl.add("base", [], asp_program)
ctl.ground([("base", [])])

solution_data = None

def on_model(model):
    global solution_data
    solution_data = {
        'starts': [],
        'makespan': None,
        'total_penalty': None,
        'job_finishes': [],
        'tardiness': []
    }
    
    for atom in model.symbols(atoms=True):
        if atom.name == "start" and len(atom.arguments) == 3:
            j = atom.arguments[0].number
            o = atom.arguments[1].number
            t = atom.arguments[2].number
            solution_data['starts'].append((j, o, t))
        elif atom.name == "makespan" and len(atom.arguments) == 1:
            solution_data['makespan'] = atom.arguments[0].number
        elif atom.name == "total_penalty" and len(atom.arguments) == 1:
            solution_data['total_penalty'] = atom.arguments[0].number
        elif atom.name == "job_finish" and len(atom.arguments) == 2:
            j = atom.arguments[0].number
            t = atom.arguments[1].number
            solution_data['job_finishes'].append((j, t))
        elif atom.name == "tardiness" and len(atom.arguments) == 2:
            j = atom.arguments[0].number
            tard = atom.arguments[1].number
            solution_data['tardiness'].append((j, tard))

result = ctl.solve(on_model=on_model)

if result.satisfiable:
    schedule = []
    for j, o, t in sorted(solution_data['starts']):
        op_data = operations_data[(j, o)]
        schedule.append({
            'job': j,
            'operation': o,
            'machine': op_data['machine'],
            'start': t,
            'duration': op_data['duration']
        })
    
    job_completion = []
    job_finish_dict = {j: t for j, t in solution_data['job_finishes']}
    tardiness_dict = {j: t for j, t in solution_data['tardiness']}
    
    for j in sorted(job_finish_dict.keys()):
        finish_time = job_finish_dict[j]
        due_date = due_dates[j]
        tardiness = tardiness_dict.get(j, 0)
        
        job_completion.append({
            'job': j,
            'finish_time': finish_time,
            'due_date': due_date,
            'tardiness': tardiness
        })
    
    total_cost = solution_data['makespan'] + solution_data['total_penalty']
    
    output = {
        'schedule': schedule,
        'metrics': {
            'makespan': solution_data['makespan'],
            'total_penalty': solution_data['total_penalty'],
            'total_cost': total_cost
        },
        'job_completion': job_completion,
        'feasible': True
    }
    
    print(json.dumps(output, indent=2))
else:
    print(json.dumps({
        "error": "No solution exists",
        "reason": "Unable to find a feasible schedule satisfying all constraints",
        "feasible": False
    }))
