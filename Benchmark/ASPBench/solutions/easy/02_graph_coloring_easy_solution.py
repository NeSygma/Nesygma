import clingo
import json

def solve_graph_coloring():
    ctl = clingo.Control(["0"])
    
    program = """
    vertex(1..6).
    
    edge(1, 2). edge(2, 1).
    edge(1, 3). edge(3, 1).
    edge(2, 3). edge(3, 2).
    edge(2, 4). edge(4, 2).
    edge(3, 4). edge(4, 3).
    edge(3, 5). edge(5, 3).
    edge(4, 5). edge(5, 4).
    edge(4, 6). edge(6, 4).
    edge(5, 6). edge(6, 5).
    
    color(1..6).
    
    1 { colored(V, C) : color(C) } 1 :- vertex(V).
    
    :- edge(V1, V2), colored(V1, C), colored(V2, C).
    
    used_color(C) :- colored(_, C).
    
    #minimize { 1,C : used_color(C) }.
    """
    
    ctl.add("base", [], program)
    ctl.ground([("base", [])])
    
    solution = None
    
    def on_model(model):
        nonlocal solution
        atoms = model.symbols(atoms=True)
        
        coloring = []
        used_colors = set()
        
        for atom in atoms:
            if atom.name == "colored" and len(atom.arguments) == 2:
                vertex = atom.arguments[0].number
                color = atom.arguments[1].number
                coloring.append({"vertex": vertex, "color": color})
                used_colors.add(color)
        
        color_mapping = {old_color: new_color 
                        for new_color, old_color 
                        in enumerate(sorted(used_colors), 1)}
        
        for item in coloring:
            item["color"] = color_mapping[item["color"]]
        
        coloring.sort(key=lambda x: x["vertex"])
        
        solution = {
            "num_colors": len(used_colors),
            "coloring": coloring
        }
    
    result = ctl.solve(on_model=on_model)
    
    if result.satisfiable and solution:
        return solution
    else:
        return {"error": "No solution exists", 
                "reason": "Graph coloring problem is unsatisfiable"}

solution = solve_graph_coloring()
print(json.dumps(solution, indent=2))
