import clingo
import json


def generate_asp_program():
    program = """
vertex(1..15).

protected(1). protected(15).

cost(1, 10). cost(2, 4). cost(3, 5). cost(4, 6).
cost(5, 7). cost(6, 9). cost(7, 8).
cost(8, 2). cost(9, 4). cost(10, 3).
cost(11, 5). cost(12, 7). cost(13, 6).
cost(14, 6). cost(15, 12).

group(a, 2). group(a, 3). group(a, 4).
group(b, 5). group(b, 6). group(b, 7).
group(c, 8). group(c, 9). group(c, 10).
group(d, 11). group(d, 12). group(d, 13).
group(e, 14).

core_edge(1, 2). core_edge(1, 5). core_edge(1, 8).
core_edge(2, 3). core_edge(3, 4). core_edge(4, 2).
core_edge(5, 6). core_edge(6, 7). core_edge(7, 5).
core_edge(8, 9). core_edge(9, 10). core_edge(10, 8).
core_edge(11, 12). core_edge(12, 13). core_edge(13, 11).
core_edge(2, 11). core_edge(4, 14). core_edge(7, 14). core_edge(10, 15).
core_edge(14, 1).

conditional_edge(3, 7). conditional_edge(3, 11).
conditional_edge(6, 10). conditional_edge(6, 13).
conditional_edge(9, 13). conditional_edge(9, 14).
conditional_edge(12, 4). conditional_edge(12, 7).

{ removed(V) } :- vertex(V), not protected(V).

:- removed(V), protected(V).

:- group(G, V1), group(G, V2), removed(V1), removed(V2), V1 != V2.

remaining(V) :- vertex(V), not removed(V).

active_edge(U, V) :- core_edge(U, V), remaining(U).
active_edge(U, V) :- conditional_edge(U, V), remaining(U).

reach(U, V) :- active_edge(U, V).
reach(U, W) :- reach(U, V), active_edge(V, W).

:- remaining(V), reach(V, V).

total_cost(C) :- C = #sum { Cost, V : removed(V), cost(V, Cost) }.

:- total_cost(C), C > 18.

#show removed/1.
#show total_cost/1.
"""
    return program


def solve_feedback_vertex_set():
    ctl = clingo.Control(["1"])
    
    program = generate_asp_program()
    ctl.add("base", [], program)
    
    ctl.ground([("base", [])])
    
    solution_data = None
    
    def on_model(model):
        nonlocal solution_data
        
        removed_vertices = []
        total_cost = 0
        
        for atom in model.symbols(atoms=True):
            if atom.name == "removed" and len(atom.arguments) == 1:
                vertex_id = atom.arguments[0].number
                removed_vertices.append(vertex_id)
            elif atom.name == "total_cost" and len(atom.arguments) == 1:
                total_cost = atom.arguments[0].number
        
        removed_vertices.sort()
        
        vertex_costs = {
            1: 10, 2: 4, 3: 5, 4: 6, 5: 7, 6: 9, 7: 8,
            8: 2, 9: 4, 10: 3, 11: 5, 12: 7, 13: 6, 14: 6, 15: 12
        }
        
        costs = [vertex_costs[v] for v in removed_vertices]
        
        all_vertices = list(range(1, 16))
        remaining_vertices = [v for v in all_vertices 
                            if v not in removed_vertices]
        
        solution_data = {
            "feedback_set": removed_vertices,
            "costs": costs,
            "total_cost": total_cost,
            "remaining_vertices": remaining_vertices
        }
    
    result = ctl.solve(on_model=on_model)
    
    if result.satisfiable:
        return solution_data
    else:
        return {"error": "No solution exists", 
                "reason": "Problem is unsatisfiable"}


solution = solve_feedback_vertex_set()
print(json.dumps(solution, indent=2))
