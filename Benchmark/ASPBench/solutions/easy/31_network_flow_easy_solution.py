import clingo
import json

def solve_max_flow():
    ctl = clingo.Control(["0"])
    
    facts = """
node(1). node(2). node(3). node(4). node(5). node(6).
source(1). sink(6).
edge(1,2,10). edge(1,3,8). edge(2,3,5). edge(2,4,7).
edge(3,4,3). edge(3,5,9). edge(4,6,8). edge(5,6,6).
"""
    
    program = """
{ flow(U, V, F) : F = 0..Cap } 1 :- edge(U, V, Cap).

:- flow(U, V, F), edge(U, V, Cap), F > Cap.

intermediate(N) :- node(N), not source(N), not sink(N).

incoming(N, Sum) :- intermediate(N), 
                    Sum = #sum { F,U : flow(U, N, F) }.

outgoing(N, Sum) :- intermediate(N), 
                    Sum = #sum { F,V : flow(N, V, F) }.

:- intermediate(N), incoming(N, In), outgoing(N, Out), In != Out.

total_flow(Total) :- Total = #sum { F,V : flow(1, V, F) }.

#maximize { Total : total_flow(Total) }.
"""
    
    ctl.add("base", [], facts)
    ctl.add("base", [], program)
    ctl.ground([("base", [])])
    
    solution = None
    max_flow_value = 0
    
    def on_model(m):
        nonlocal solution, max_flow_value
        
        flows = []
        total = 0
        
        for atom in m.symbols(atoms=True):
            if atom.name == "flow" and len(atom.arguments) == 3:
                u = atom.arguments[0].number
                v = atom.arguments[1].number
                f = atom.arguments[2].number
                
                if f > 0:
                    flows.append({
                        "from": u,
                        "to": v,
                        "flow": f
                    })
                    if u == 1:
                        total += f
            
            if atom.name == "total_flow" and len(atom.arguments) == 1:
                max_flow_value = atom.arguments[0].number
        
        solution = {
            "max_flow": max_flow_value,
            "flows": sorted(flows, key=lambda x: (x["from"], x["to"]))
        }
    
    result = ctl.solve(on_model=on_model)
    
    if result.satisfiable:
        return solution
    else:
        return {"error": "No solution exists", "reason": "Problem is unsatisfiable"}

if __name__ == "__main__":
    result = solve_max_flow()
    print(json.dumps(result, indent=2))
