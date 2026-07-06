import clingo
import json

asp_program = """
step("roast_chicken", "prep_chicken", 15, "prep_area").
step("roast_chicken", "bake_chicken", 50, "oven").
step("roast_chicken", "rest_chicken", 10, "prep_area").

step("vegetable_soup", "chop_veg_soup", 20, "prep_area").
step("vegetable_soup", "simmer_stock", 30, "stove").

step("risotto", "chop_onion", 5, "prep_area").
step("risotto", "cook_risotto", 25, "stove").

step("side_salad", "wash_greens", 5, "prep_area").
step("side_salad", "mix_dressing", 10, "prep_area").

special_task("preheat_oven", 10, "oven").

precedes("roast_chicken", "prep_chicken", "bake_chicken").
precedes("roast_chicken", "bake_chicken", "rest_chicken").
precedes("vegetable_soup", "chop_veg_soup", "simmer_stock").
precedes("risotto", "chop_onion", "cook_risotto").
precedes("side_salad", "wash_greens", "mix_dressing").

inter_recipe_dep("vegetable_soup", "simmer_stock", "risotto", 
                 "cook_risotto").

requires_preheat("roast_chicken", "bake_chicken").

resource_capacity("prep_area", 2).
resource_capacity("oven", 1).
resource_capacity("stove", 1).

time(0..100).

1 { start_step(Recipe, Step, T) : time(T) } 1 :- 
    step(Recipe, Step, _, _).

1 { start_special(Task, T) : time(T) } 1 :- 
    special_task(Task, _, _).

end_step(Recipe, Step, T + Duration) :- 
    start_step(Recipe, Step, T), 
    step(Recipe, Step, Duration, _).

end_special(Task, T + Duration) :- 
    start_special(Task, T), 
    special_task(Task, Duration, _).

:- precedes(Recipe, Step1, Step2),
   end_step(Recipe, Step1, End1),
   start_step(Recipe, Step2, Start2),
   Start2 < End1.

:- inter_recipe_dep(Recipe1, Step1, Recipe2, Step2),
   end_step(Recipe1, Step1, End1),
   start_step(Recipe2, Step2, Start2),
   Start2 < End1.

:- requires_preheat(Recipe, Step),
   start_step(Recipe, Step, StepStart),
   end_special("preheat_oven", PreheatEnd),
   StepStart < PreheatEnd.

occupies_resource(Resource, T, Recipe, Step) :-
    start_step(Recipe, Step, Start),
    end_step(Recipe, Step, End),
    step(Recipe, Step, _, Resource),
    time(T), T >= Start, T < End.

occupies_resource(Resource, T, special, Task) :-
    start_special(Task, Start),
    end_special(Task, End),
    special_task(Task, _, Resource),
    time(T), T >= Start, T < End.

concurrent_usage(Resource, T, Count) :-
    resource_capacity(Resource, _),
    time(T),
    Count = #count { Recipe, Step : 
                     occupies_resource(Resource, T, Recipe, Step) }.

:- concurrent_usage(Resource, T, Count),
   resource_capacity(Resource, Capacity),
   Count > Capacity.

makespan(M) :- M = #max { End : end_step(_, _, End) ; 
                          End : end_special(_, End) }.

:- makespan(M), M > 75.

#show start_step/3.
#show start_special/2.
#show end_step/3.
#show end_special/2.
#show makespan/1.
"""

ctl = clingo.Control(["1"])
ctl.add("base", [], asp_program)
ctl.ground([("base", [])])

solution_data = None

def on_model(model):
    global solution_data
    
    atoms = model.symbols(atoms=True)
    schedule = []
    start_times = {}
    end_times = {}
    
    for atom in atoms:
        if atom.name == "start_step" and len(atom.arguments) == 3:
            recipe = str(atom.arguments[0]).strip('"')
            step = str(atom.arguments[1]).strip('"')
            start_time = atom.arguments[2].number
            start_times[(recipe, step)] = start_time
            
        elif atom.name == "end_step" and len(atom.arguments) == 3:
            recipe = str(atom.arguments[0]).strip('"')
            step = str(atom.arguments[1]).strip('"')
            end_time = atom.arguments[2].number
            end_times[(recipe, step)] = end_time
            
        elif atom.name == "start_special" and len(atom.arguments) == 2:
            task = str(atom.arguments[0]).strip('"')
            start_time = atom.arguments[1].number
            start_times[("special", task)] = start_time
            
        elif atom.name == "end_special" and len(atom.arguments) == 2:
            task = str(atom.arguments[0]).strip('"')
            end_time = atom.arguments[1].number
            end_times[("special", task)] = end_time
    
    steps_info = [
        ("roast_chicken", "prep_chicken", 15, "prep_area"),
        ("roast_chicken", "bake_chicken", 50, "oven"),
        ("roast_chicken", "rest_chicken", 10, "prep_area"),
        ("vegetable_soup", "chop_veg_soup", 20, "prep_area"),
        ("vegetable_soup", "simmer_stock", 30, "stove"),
        ("risotto", "chop_onion", 5, "prep_area"),
        ("risotto", "cook_risotto", 25, "stove"),
        ("side_salad", "wash_greens", 5, "prep_area"),
        ("side_salad", "mix_dressing", 10, "prep_area"),
    ]
    
    for recipe, step, duration, resource in steps_info:
        key = (recipe, step)
        if key in start_times and key in end_times:
            schedule.append({
                "recipe": recipe,
                "step": step,
                "start_time": start_times[key],
                "end_time": end_times[key],
                "resource": resource
            })
    
    special_key = ("special", "preheat_oven")
    if special_key in start_times and special_key in end_times:
        schedule.append({
            "task": "preheat_oven",
            "start_time": start_times[special_key],
            "end_time": end_times[special_key],
            "resource": "oven"
        })
    
    schedule.sort(key=lambda x: x["start_time"])
    
    if schedule:
        actual_makespan = max(item["end_time"] for item in schedule)
    else:
        actual_makespan = 0
    
    solution_data = {
        "total_time": actual_makespan,
        "schedule": schedule,
        "feasible": True
    }

result = ctl.solve(on_model=on_model)

if result.satisfiable and solution_data:
    print(json.dumps(solution_data, indent=2))
else:
    print(json.dumps({
        "error": "No solution exists",
        "reason": "Could not find a feasible schedule",
        "feasible": False
    }, indent=2))
