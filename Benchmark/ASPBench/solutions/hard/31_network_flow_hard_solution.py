import clingo
import json

def solve_max_flow():
    ctl = clingo.Control(["0"])
    
    program = """
    node(1..8).
    source(1).
    sink(8).
    budget(100).
    
    edge(1, 2, 10, 2, standard).
    edge(1, 3, 12, 4, premium).
    edge(2, 4, 8, 1, standard).
    edge(2, 5, 4, 3, premium).
    edge(3, 4, 5, 3, standard).
    edge(3, 6, 10, 5, premium).
    edge(4, 7, 10, 2, standard).
    edge(5, 7, 7, 4, premium).
    edge(6, 8, 12, 2, premium).
    edge(7, 8, 15, 1, standard).
    
    flow_type(standard).
    flow_type(premium).
    
    priority_node(3).
    priority_node(5).
    
    { flow(From, To, Amount) : Amount = 0..Cap } = 1 :- edge(From, To, Cap, _, _).
    
    incoming(N, In) :- node(N), not source(N), not sink(N),
                       In = #sum { F,From : flow(From, N, F) }.
    outgoing(N, Out) :- node(N), not source(N), not sink(N),
                        Out = #sum { F,To : flow(N, To, F) }.
    
    :- incoming(N, In), outgoing(N, Out), In != Out.
    
    total_cost(Cost) :- Cost = #sum { F*C,From,To : flow(From, To, F), edge(From, To, _, C, _) }.
    :- total_cost(Cost), budget(B), Cost > B.
    
    outgoing_premium(N, Premium) :- priority_node(N),
                                     Premium = #sum { F,To : flow(N, To, F), edge(N, To, _, _, premium) }.
    outgoing_total(N, Total) :- priority_node(N),
                                 Total = #sum { F,To : flow(N, To, F) }.
    
    :- priority_node(N), outgoing_total(N, Total), Total > 0,
       outgoing_premium(N, Premium), 4 * Premium < 3 * Total.
    
    total_standard(S) :- S = #sum { F,From,To : flow(From, To, F), edge(From, To, _, _, standard) }.
    total_premium(P) :- P = #sum { F,From,To : flow(From, To, F), edge(From, To, _, _, premium) }.
    
    :- total_standard(S), total_premium(P), 2 * S < P.
    
    source_outflow(F) :- source(S), F = #sum { Amount,To : flow(S, To, Amount) }.
    
    total_flow(F) :- source_outflow(F).
    
    #maximize { F : total_flow(F) }.
    
    #show flow/3.
    #show total_flow/1.
    """
    
    ctl.add("base", [], program)
    ctl.ground([("base", [])])
    
    solution = None
    best_flow = -1
    
    def on_model(model):
        nonlocal solution, best_flow
        atoms = model.symbols(atoms=True)
        
        flows = []
        max_flow = 0
        
        for atom in atoms:
            if atom.name == "flow" and len(atom.arguments) == 3:
                from_node = atom.arguments[0].number
                to_node = atom.arguments[1].number
                flow_amount = atom.arguments[2].number
                flows.append({
                    "from": from_node,
                    "to": to_node,
                    "flow": flow_amount
                })
            elif atom.name == "total_flow" and len(atom.arguments) == 1:
                max_flow = atom.arguments[0].number
        
        if max_flow > best_flow:
            best_flow = max_flow
            flows.sort(key=lambda x: (x["from"], x["to"]))
            solution = {
                "max_flow": max_flow,
                "flows": flows
            }
    
    result = ctl.solve(on_model=on_model)
    
    if result.satisfiable:
        return solution
    else:
        return {"error": "No solution exists", "reason": "Constraints cannot be satisfied"}

solution = solve_max_flow()
print(json.dumps(solution, indent=2))
