import clingo
import json

def generate_asp_program():
    customers = [
        (1, 1, 1), (2, 2, 4), (3, 4, 2), (4, 5, 5),
        (5, 7, 1), (6, 8, 3), (7, 3, 6), (8, 6, 4)
    ]
    
    facilities = [
        ("A", 2, 2, 100), ("B", 4, 4, 120), ("C", 6, 2, 110),
        ("D", 3, 5, 90), ("E", 7, 3, 130)
    ]
    
    coverage_radius = 3
    service_cost_per_unit = 5
    
    program = []
    
    for c_id, x, y in customers:
        program.append(f'customer({c_id}, {x}, {y}).')
    
    for f_id, x, y, cost in facilities:
        program.append(f'facility("{f_id}", {x}, {y}, {cost}).')
    
    for c_id, cx, cy in customers:
        for f_id, fx, fy, _ in facilities:
            dist = abs(cx - fx) + abs(cy - fy)
            service_cost = dist * service_cost_per_unit
            program.append(f'manhattan({c_id}, "{f_id}", {dist}).')
            program.append(f'service_cost({c_id}, "{f_id}", {service_cost}).')
            
            if dist <= coverage_radius:
                program.append(f'can_serve({c_id}, "{f_id}").')
    
    return "\n".join(program)

def create_full_asp_program():
    program = generate_asp_program()
    
    rules = """
{ opened(F) } :- facility(F, _, _, _).

1 { serves(C, F) : can_serve(C, F) } 1 :- customer(C, _, _).

:- serves(C, F), not opened(F).

opening_cost_total(Total) :- Total = #sum { Cost, F : opened(F), facility(F, _, _, Cost) }.

service_cost_total(Total) :- Total = #sum { SC, C, F : serves(C, F), service_cost(C, F, SC) }.

total_cost(Total) :- opening_cost_total(OC), service_cost_total(SC), Total = OC + SC.

:- total_cost(Cost), Cost > 380.

#minimize { Cost : total_cost(Cost) }.

#show opened/1.
#show serves/2.
#show total_cost/1.
"""
    
    return program + "\n" + rules

def solve_facility_location():
    ctl = clingo.Control(["1"])
    
    program = create_full_asp_program()
    ctl.add("base", [], program)
    
    ctl.ground([("base", [])])
    
    solution_data = None
    
    def on_model(model):
        nonlocal solution_data
        
        opened_facilities = []
        assignments = {}
        total_cost_value = None
        
        for atom in model.symbols(atoms=True):
            if atom.name == "opened" and len(atom.arguments) == 1:
                facility_id = str(atom.arguments[0]).strip('"')
                opened_facilities.append(facility_id)
            
            elif atom.name == "serves" and len(atom.arguments) == 2:
                customer_id = str(atom.arguments[0])
                facility_id = str(atom.arguments[1]).strip('"')
                assignments[customer_id] = facility_id
            
            elif atom.name == "total_cost" and len(atom.arguments) == 1:
                total_cost_value = int(str(atom.arguments[0]))
        
        solution_data = {
            "facilities": sorted(opened_facilities),
            "assignments": assignments,
            "total_cost": total_cost_value,
            "feasible": True
        }
    
    result = ctl.solve(on_model=on_model)
    
    if result.satisfiable:
        return solution_data
    else:
        return {
            "error": "No solution exists",
            "reason": "Problem is unsatisfiable with given constraints",
            "feasible": False
        }

solution = solve_facility_location()
print(json.dumps(solution, indent=2))
