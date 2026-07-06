import clingo
import json

recipes_data = {
    "pasta": [
        {"step": "prep", "duration": 10, "resource": "prep_area", "order": 1},
        {"step": "boil", "duration": 15, "resource": "stove", "order": 2},
        {"step": "serve", "duration": 5, "resource": "prep_area", "order": 3}
    ],
    "salad": [
        {"step": "chop", "duration": 15, "resource": "prep_area", "order": 1},
        {"step": "mix", "duration": 5, "resource": "prep_area", "order": 2}
    ],
    "bread": [
        {"step": "bake", "duration": 30, "resource": "oven", "order": 1}
    ]
}

resources = ["oven", "stove", "prep_area"]

def generate_asp_facts():
    facts = []
    
    for recipe, steps in recipes_data.items():
        facts.append(f'recipe("{recipe}").')
        for step_data in steps:
            step = step_data["step"]
            duration = step_data["duration"]
            resource = step_data["resource"]
            order = step_data["order"]
            facts.append(f'step("{recipe}", "{step}", {duration}, "{resource}", {order}).')
    
    for resource in resources:
        facts.append(f'resource("{resource}").')
    
    facts.append('precedes("pasta", "prep", "boil").')
    facts.append('precedes("pasta", "boil", "serve").')
    facts.append('precedes("salad", "chop", "mix").')
    facts.append('#const max_time = 35.')
    
    return "\n".join(facts)

asp_facts = generate_asp_facts()

asp_program = """
% Facts (generated from problem data)
""" + asp_facts + """

% Define time domain (0 to max_time)
time(0..max_time).

% Choice rule: Each step starts at exactly one time
1 { start_time(Recipe, Step, T) : time(T) } 1 :- step(Recipe, Step, _, _, _).

% Define end time based on start time and duration
end_time(Recipe, Step, T + Duration) :- 
    start_time(Recipe, Step, T), 
    step(Recipe, Step, Duration, _, _).

% Constraint: End time must not exceed max_time
:- end_time(Recipe, Step, EndTime), EndTime > max_time.

% Constraint: Precedence - if step S1 must precede S2, S1 must end before S2 starts
:- precedes(Recipe, Step1, Step2),
   end_time(Recipe, Step1, End1),
   start_time(Recipe, Step2, Start2),
   End1 > Start2.

% Constraint: No resource conflicts - two steps using the same resource cannot overlap
:- step(R1, S1, _, Res, _),
   step(R2, S2, _, Res, _),
   (R1, S1) != (R2, S2),
   start_time(R1, S1, Start1),
   end_time(R1, S1, End1),
   start_time(R2, S2, Start2),
   end_time(R2, S2, End2),
   Start1 < End2,
   Start2 < End1.

% Calculate total completion time (maximum end time)
total_time(MaxEnd) :- MaxEnd = #max { End : end_time(_, _, End) }.

% Constraint: Total time must not exceed max_time
:- total_time(T), T > max_time.

% Show predicates for output
#show start_time/3.
#show end_time/3.
#show total_time/1.
"""

def solve_scheduling():
    ctl = clingo.Control(["1"])
    ctl.add("base", [], asp_program)
    ctl.ground([("base", [])])
    
    solution_data = None
    
    def on_model(model):
        nonlocal solution_data
        solution_data = {
            "start_times": {},
            "end_times": {},
            "total_time": None
        }
        
        for atom in model.symbols(atoms=True):
            if atom.name == "start_time" and len(atom.arguments) == 3:
                recipe = str(atom.arguments[0])[1:-1]
                step = str(atom.arguments[1])[1:-1]
                time = atom.arguments[2].number
                solution_data["start_times"][(recipe, step)] = time
                
            elif atom.name == "end_time" and len(atom.arguments) == 3:
                recipe = str(atom.arguments[0])[1:-1]
                step = str(atom.arguments[1])[1:-1]
                time = atom.arguments[2].number
                solution_data["end_times"][(recipe, step)] = time
                
            elif atom.name == "total_time" and len(atom.arguments) == 1:
                solution_data["total_time"] = atom.arguments[0].number
    
    result = ctl.solve(on_model=on_model)
    
    if result.satisfiable:
        return solution_data
    else:
        return None

def format_output(solution_data):
    if not solution_data:
        return {"error": "No solution exists", "reason": "Problem is unsatisfiable"}
    
    schedule = []
    for recipe, steps in recipes_data.items():
        for step_data in steps:
            step = step_data["step"]
            resource = step_data["resource"]
            
            start = solution_data["start_times"][(recipe, step)]
            end = solution_data["end_times"][(recipe, step)]
            
            schedule.append({
                "recipe": recipe,
                "step": step,
                "start_time": start,
                "end_time": end,
                "resources": [resource]
            })
    
    schedule.sort(key=lambda x: (x["start_time"], x["recipe"], x["step"]))
    
    resource_usage = {res: [] for res in resources}
    
    for item in schedule:
        resource = item["resources"][0]
        resource_usage[resource].append({
            "start": item["start_time"],
            "end": item["end_time"],
            "recipe": item["recipe"]
        })
    
    for res in resource_usage:
        resource_usage[res].sort(key=lambda x: x["start"])
    
    output = {
        "total_time": solution_data["total_time"],
        "schedule": schedule,
        "resource_usage": resource_usage
    }
    
    return output

solution = solve_scheduling()
output = format_output(solution)
print(json.dumps(output, indent=2))
