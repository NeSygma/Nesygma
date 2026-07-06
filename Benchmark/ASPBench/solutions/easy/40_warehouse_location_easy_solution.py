import clingo
import json

def solve_warehouse_problem():
    ctl = clingo.Control(["1"])
    
    program = """
    warehouse("W1"). warehouse("W2"). warehouse("W3").
    
    capacity("W1", 100).
    capacity("W2", 150).
    capacity("W3", 120).
    
    customer("C1"). customer("C2"). customer("C3").
    customer("C4"). customer("C5"). customer("C6").
    
    demand("C1", 25).
    demand("C2", 30).
    demand("C3", 20).
    demand("C4", 35).
    demand("C5", 15).
    demand("C6", 25).
    
    distance("W1", "C1", 10). distance("W1", "C2", 15).
    distance("W1", "C3", 25). distance("W1", "C4", 20).
    distance("W1", "C5", 30). distance("W1", "C6", 12).
    distance("W2", "C1", 18). distance("W2", "C2", 8).
    distance("W2", "C3", 12). distance("W2", "C4", 15).
    distance("W2", "C5", 10). distance("W2", "C6", 20).
    distance("W3", "C1", 22). distance("W3", "C2", 25).
    distance("W3", "C3", 8).  distance("W3", "C4", 18).
    distance("W3", "C5", 12). distance("W3", "C6", 15).
    
    { open(W) } :- warehouse(W).
    
    1 { assign(C, W) : warehouse(W) } 1 :- customer(C).
    
    :- assign(C, W), not open(W).
    
    :- warehouse(W), capacity(W, Cap),
       #sum { D,C : assign(C, W), demand(C, D) } > Cap.
    
    total_cost(TotalCost) :- 
        TotalCost = #sum { Dist*Dem, C, W : assign(C, W), 
                          distance(W, C, Dist), demand(C, Dem) }.
    
    :- total_cost(Cost), Cost > 1625.
    
    #show open/1.
    #show assign/2.
    #show total_cost/1.
    """
    
    ctl.add("base", [], program)
    ctl.ground([("base", [])])
    
    solution = None
    
    def on_model(model):
        nonlocal solution
        solution = {
            "selected_warehouses": [],
            "assignments": {},
            "total_cost": 0
        }
        
        for atom in model.symbols(atoms=True):
            if atom.name == "open" and len(atom.arguments) == 1:
                warehouse = str(atom.arguments[0]).strip('"')
                solution["selected_warehouses"].append(warehouse)
            elif atom.name == "assign" and len(atom.arguments) == 2:
                customer = str(atom.arguments[0]).strip('"')
                warehouse = str(atom.arguments[1]).strip('"')
                solution["assignments"][customer] = warehouse
            elif atom.name == "total_cost" and len(atom.arguments) == 1:
                solution["total_cost"] = atom.arguments[0].number
        
        solution["selected_warehouses"].sort()
    
    result = ctl.solve(on_model=on_model)
    
    if result.satisfiable and solution:
        return solution
    else:
        return {
            "error": "No solution exists",
            "reason": "Problem is unsatisfiable"
        }

solution = solve_warehouse_problem()
print(json.dumps(solution, indent=2))
