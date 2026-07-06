import clingo
import json

def generate_asp_program():
    program = """
vertex(1..36).
color(1..5).

weight(1, 10). weight(2, 10). weight(3, 10). weight(4, 10). weight(5, 10).
weight(6, 3). weight(7, 3). weight(8, 3). weight(9, 3). weight(10, 3).
weight(11, 3). weight(12, 3). weight(13, 3). weight(14, 3). weight(15, 3).
weight(16, 5). weight(17, 5). weight(18, 5). weight(19, 5). weight(20, 5).
weight(21, 5). weight(22, 5). weight(23, 5). weight(24, 5). weight(25, 5).
weight(26, 7). weight(27, 7). weight(28, 7). weight(29, 7). weight(30, 7).
weight(31, 7). weight(32, 7). weight(33, 7). weight(34, 7). weight(35, 7).
weight(36, 7).

edge(1,2). edge(1,3). edge(1,4). edge(1,5).
edge(2,3). edge(2,4). edge(2,5).
edge(3,4). edge(3,5).
edge(4,5).

edge(6,7). edge(7,8). edge(8,9). edge(9,10). edge(10,11).
edge(11,12). edge(12,13). edge(13,14). edge(14,15). edge(15,6).

edge(6,9). edge(7,10). edge(8,11). edge(9,12). edge(10,13).
edge(11,14). edge(12,15). edge(13,6). edge(14,7). edge(15,8).

edge(6,1). edge(6,2).
edge(9,2). edge(9,3).
edge(12,3). edge(12,4).
edge(15,4). edge(15,5).

edge(16,17). edge(17,18). edge(18,19). edge(19,20).
edge(21,22). edge(22,23). edge(23,24). edge(24,25).

edge(16,21). edge(17,22). edge(18,23). edge(19,24). edge(20,25).

edge(16,22). edge(17,23). edge(18,24). edge(19,25).

edge(16,1). edge(20,5).

edge(18,8). edge(23,13).

edge(26,27). edge(27,28). edge(28,29). edge(29,30). edge(30,31).
edge(31,32). edge(32,33). edge(33,34). edge(34,35). edge(35,36). edge(36,26).

edge(26,29). edge(27,30). edge(28,31). edge(29,32). edge(30,33).
edge(31,34). edge(32,35). edge(33,36). edge(34,26). edge(35,27). edge(36,28).

edge(26,1). edge(26,5). edge(31,3).

edge(28,19). edge(33,24).

edge(V2, V1) :- edge(V1, V2), V1 < V2.

1 { colored(V, C) : color(C) } 1 :- vertex(V).

:- edge(V1, V2), colored(V1, C), colored(V2, C).

vertex_cost(V, Cost) :- colored(V, C), weight(V, W), Cost = C * W.

total_cost(Total) :- Total = #sum { Cost, V : vertex_cost(V, Cost) }.

:- total_cost(Cost), Cost > 850.

:- color(C), not colored(_, C).
"""
    return program

def solve_graph_coloring():
    ctl = clingo.Control(["1"])
    
    program = generate_asp_program()
    ctl.add("base", [], program)
    
    ctl.ground([("base", [])])
    
    solution = None
    
    def on_model(m):
        nonlocal solution
        atoms = m.symbols(atoms=True)
        
        coloring = {}
        for atom in atoms:
            if atom.name == "colored" and len(atom.arguments) == 2:
                vertex = atom.arguments[0].number
                color = atom.arguments[1].number
                coloring[vertex] = color
        
        total_cost = None
        for atom in atoms:
            if atom.name == "total_cost" and len(atom.arguments) == 1:
                total_cost = atom.arguments[0].number
        
        solution = {
            "coloring": coloring,
            "total_cost": total_cost
        }
    
    result = ctl.solve(on_model=on_model)
    
    return result, solution

def format_solution(solution):
    if solution is None:
        return {
            "error": "No solution exists",
            "reason": "Graph coloring with given constraints is unsatisfiable"
        }
    
    coloring_dict = solution['coloring']
    total_cost = solution['total_cost']
    
    colors_used = set(coloring_dict.values())
    num_colors = len(colors_used)
    
    coloring_array = []
    for vertex in sorted(coloring_dict.keys()):
        coloring_array.append({
            "vertex": vertex,
            "color": coloring_dict[vertex]
        })
    
    output = {
        "num_colors": num_colors,
        "weighted_cost": total_cost,
        "coloring": coloring_array
    }
    
    return output

result, solution = solve_graph_coloring()

if result.satisfiable:
    output = format_solution(solution)
    print(json.dumps(output, indent=2))
else:
    print(json.dumps({
        "error": "No solution exists",
        "reason": "The graph coloring problem is unsatisfiable"
    }))
