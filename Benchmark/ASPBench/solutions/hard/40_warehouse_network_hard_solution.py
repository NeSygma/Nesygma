import clingo
import json

asp_program = """
% Facts - Entities
hub("H1"). hub("H2").
regional("R1"). regional("R2"). regional("R3"). regional("R4").
customer("C1"). customer("C2"). customer("C3"). customer("C4"). customer("C5"). customer("C6").
time_slot(1..4).

% Opening costs
hub_cost("H1", 1000). hub_cost("H2", 1200).
regional_cost("R1", 200). regional_cost("R2", 250). regional_cost("R3", 220). regional_cost("R4", 180).

% Capacities
hub_capacity("H1", 400). hub_capacity("H2", 350).
regional_capacity("R1", 70). regional_capacity("R2", 80). regional_capacity("R3", 60). regional_capacity("R4", 90).

% Truck resources per hub per time slot
trucks_available("H1", 2). trucks_available("H2", 1).

% Customer demands and time windows
customer_demand("C1", 20). customer_time_window("C1", 2, 3).
customer_demand("C2", 30). customer_time_window("C2", 1, 2).
customer_demand("C3", 15). customer_time_window("C3", 3, 4).
customer_demand("C4", 25). customer_time_window("C4", 1, 4).
customer_demand("C5", 35). customer_time_window("C5", 2, 4).
customer_demand("C6", 10). customer_time_window("C6", 1, 1).

% Transportation costs - Hub to Regional
hub_to_regional_cost("H1", "R1", 5). hub_to_regional_cost("H1", "R2", 6).
hub_to_regional_cost("H2", "R3", 5). hub_to_regional_cost("H2", "R4", 6).

% Transportation costs - Regional to Customer
regional_to_customer_cost("R1", "C1", 10). regional_to_customer_cost("R1", "C2", 12).
regional_to_customer_cost("R2", "C2", 13). regional_to_customer_cost("R2", "C3", 15).
regional_to_customer_cost("R3", "C4", 9). regional_to_customer_cost("R3", "C5", 11).
regional_to_customer_cost("R4", "C5", 14). regional_to_customer_cost("R4", "C6", 7).

% Connectivity constraints
can_supply("H1", "R1"). can_supply("H1", "R2").
can_supply("H2", "R3"). can_supply("H2", "R4").

can_serve("R1", "C1"). can_serve("R1", "C2").
can_serve("R2", "C2"). can_serve("R2", "C3").
can_serve("R3", "C4"). can_serve("R3", "C5").
can_serve("R4", "C5"). can_serve("R4", "C6").

% Maintenance schedules
maintenance("R2", 2). maintenance("H1", 4).

% Choice rules
{ open_hub(H) } :- hub(H).
{ open_regional(R) } :- regional(R).

% Each open regional warehouse is supplied by exactly one hub
1 { supply(R, H) : hub(H), can_supply(H, R) } 1 :- open_regional(R).

% Each customer is delivered by exactly one regional warehouse at exactly one time slot
1 { deliver(C, R, T) : regional(R), can_serve(R, C), time_slot(T) } 1 :- customer(C).

% Constraints
:- deliver(C, R, T), not open_regional(R).
:- supply(R, H), not open_hub(H).
:- deliver(C, R, T), customer_time_window(C, Start, End), T < Start.
:- deliver(C, R, T), customer_time_window(C, Start, End), T > End.
:- deliver(C, R, T), maintenance(R, T).
:- deliver(C, R, T), supply(R, H), maintenance(H, T).

% Regional capacity
:- regional(R), regional_capacity(R, Cap),
   #sum { Demand, C : deliver(C, R, _), customer_demand(C, Demand) } > Cap.

% Hub capacity
:- hub(H), hub_capacity(H, Cap),
   #sum { Demand, C : deliver(C, R, _), supply(R, H), customer_demand(C, Demand) } > Cap.

% Truck limits
:- hub(H), time_slot(T), trucks_available(H, Trucks),
   #count { C : deliver(C, R, T), supply(R, H) } > Trucks.

% Auxiliary predicates for cost calculation
regional_total_demand(R, D) :- regional(R), 
    D = #sum { Demand, C : deliver(C, R, _), customer_demand(C, Demand) }.

hub_regional_link_cost(R, H, TotalCost) :- 
    supply(R, H),
    hub_to_regional_cost(H, R, UnitCost),
    regional_total_demand(R, Demand),
    TotalCost = UnitCost * Demand.

delivery_cost(C, R, Cost) :-
    deliver(C, R, _),
    regional_to_customer_cost(R, C, UnitCost),
    customer_demand(C, Demand),
    Cost = UnitCost * Demand.

% Optimization - minimize total cost
#minimize { Cost, H : open_hub(H), hub_cost(H, Cost) }.
#minimize { Cost, R : open_regional(R), regional_cost(R, Cost) }.
#minimize { TotalCost, R, H : hub_regional_link_cost(R, H, TotalCost) }.
#minimize { Cost, C, R : delivery_cost(C, R, Cost) }.

#show open_hub/1.
#show open_regional/1.
#show supply/2.
#show deliver/3.
"""

ctl = clingo.Control(["0", "--opt-mode=optN"])
ctl.add("base", [], asp_program)
ctl.ground([("base", [])])

solution_data = None

def on_model(model):
    global solution_data
    solution_data = {
        'open_hubs': [],
        'open_regionals': [],
        'hub_assignments': {},
        'customer_deliveries': [],
        'total_cost': 0
    }
    
    for atom in model.symbols(atoms=True):
        if atom.name == "open_hub" and len(atom.arguments) == 1:
            hub = str(atom.arguments[0]).strip('"')
            solution_data['open_hubs'].append(hub)
        
        elif atom.name == "open_regional" and len(atom.arguments) == 1:
            regional = str(atom.arguments[0]).strip('"')
            solution_data['open_regionals'].append(regional)
        
        elif atom.name == "supply" and len(atom.arguments) == 2:
            regional = str(atom.arguments[0]).strip('"')
            hub = str(atom.arguments[1]).strip('"')
            solution_data['hub_assignments'][regional] = hub
        
        elif atom.name == "deliver" and len(atom.arguments) == 3:
            customer = str(atom.arguments[0]).strip('"')
            regional = str(atom.arguments[1]).strip('"')
            time_slot = int(str(atom.arguments[2]))
            solution_data['customer_deliveries'].append({
                'customer': customer,
                'regional_warehouse': regional,
                'time_slot': time_slot
            })

result = ctl.solve(on_model=on_model)

if result.satisfiable and solution_data:
    hub_costs = {"H1": 1000, "H2": 1200}
    regional_costs = {"R1": 200, "R2": 250, "R3": 220, "R4": 180}
    hub_to_regional_costs = {
        ("H1", "R1"): 5, ("H1", "R2"): 6,
        ("H2", "R3"): 5, ("H2", "R4"): 6
    }
    regional_to_customer_costs = {
        ("R1", "C1"): 10, ("R1", "C2"): 12,
        ("R2", "C2"): 13, ("R2", "C3"): 15,
        ("R3", "C4"): 9, ("R3", "C5"): 11,
        ("R4", "C5"): 14, ("R4", "C6"): 7
    }
    customer_demands = {"C1": 20, "C2": 30, "C3": 15, "C4": 25, "C5": 35, "C6": 10}
    
    fixed_cost = sum(hub_costs[h] for h in solution_data['open_hubs'])
    fixed_cost += sum(regional_costs[r] for r in solution_data['open_regionals'])
    
    regional_demands = {}
    for delivery in solution_data['customer_deliveries']:
        r = delivery['regional_warehouse']
        c = delivery['customer']
        regional_demands[r] = regional_demands.get(r, 0) + customer_demands[c]
    
    hub_transport_cost = 0
    for r, h in solution_data['hub_assignments'].items():
        if r in regional_demands:
            unit_cost = hub_to_regional_costs.get((h, r), 0)
            hub_transport_cost += unit_cost * regional_demands[r]
    
    regional_transport_cost = 0
    for delivery in solution_data['customer_deliveries']:
        r = delivery['regional_warehouse']
        c = delivery['customer']
        unit_cost = regional_to_customer_costs.get((r, c), 0)
        regional_transport_cost += unit_cost * customer_demands[c]
    
    solution_data['total_cost'] = fixed_cost + hub_transport_cost + regional_transport_cost
    
    solution_data['open_hubs'].sort()
    solution_data['open_regionals'].sort()
    solution_data['customer_deliveries'].sort(key=lambda x: x['customer'])
    
    print(json.dumps(solution_data, indent=2))
else:
    print(json.dumps({"error": "No solution exists"}))
