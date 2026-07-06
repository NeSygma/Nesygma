import clingo
import json


def create_asp_program():
    program = """
    vertex(0..15).
    partition(1..4).
    
    edge(0, 1, 10). edge(0, 2, 10). edge(0, 3, 10).
    edge(1, 2, 10). edge(1, 3, 10).
    edge(2, 3, 10).
    
    edge(4, 5, 10). edge(4, 6, 10). edge(4, 7, 10).
    edge(5, 6, 10). edge(5, 7, 10).
    edge(6, 7, 10).
    
    edge(8, 9, 10). edge(8, 10, 10). edge(8, 11, 10).
    edge(9, 10, 10). edge(9, 11, 10).
    edge(10, 11, 10).
    
    edge(12, 13, 10). edge(12, 14, 10). edge(12, 15, 10).
    edge(13, 14, 10). edge(13, 15, 10).
    edge(14, 15, 10).
    
    edge(0, 15, 1).
    edge(1, 6, 2).
    edge(3, 4, 1).
    edge(5, 10, 3).
    edge(7, 8, 2).
    edge(9, 14, 1).
    edge(11, 12, 3).
    
    1 { in_partition(V, P) : partition(P) } 1 :- vertex(V).
    
    :- partition(P), #count { V : in_partition(V, P) } != 4.
    
    cut_edge(U, V, W) :- edge(U, V, W), in_partition(U, P1), 
                         in_partition(V, P2), P1 != P2.
    
    total_cut(Total) :- Total = #sum { W, U, V : cut_edge(U, V, W) }.
    
    #minimize { W, U, V : cut_edge(U, V, W) }.
    
    #show in_partition/2.
    #show total_cut/1.
    #show cut_edge/3.
    """
    return program


def solve_graph_partition():
    ctl = clingo.Control(["1", "--opt-mode=optN"])
    
    program = create_asp_program()
    ctl.add("base", [], program)
    ctl.ground([("base", [])])
    
    solution_data = None
    
    def on_model(model):
        nonlocal solution_data
        atoms = model.symbols(atoms=True)
        
        partitions = {1: [], 2: [], 3: [], 4: []}
        cut_edges = []
        total_cut = 0
        
        for atom in atoms:
            if atom.name == "in_partition" and len(atom.arguments) == 2:
                vertex = atom.arguments[0].number
                partition = atom.arguments[1].number
                partitions[partition].append(vertex)
            elif atom.name == "cut_edge" and len(atom.arguments) == 3:
                u = atom.arguments[0].number
                v = atom.arguments[1].number
                w = atom.arguments[2].number
                cut_edges.append({"from": u, "to": v, "weight": w})
            elif atom.name == "total_cut" and len(atom.arguments) == 1:
                total_cut = atom.arguments[0].number
        
        for p in partitions:
            partitions[p].sort()
        
        cut_edges.sort(key=lambda x: (x["from"], x["to"]))
        
        solution_data = {
            "partition_1": partitions[1],
            "partition_2": partitions[2],
            "partition_3": partitions[3],
            "partition_4": partitions[4],
            "cut_weight": total_cut,
            "cut_edges": cut_edges,
            "balance": {
                "is_balanced": all(len(partitions[p]) == 4 for p in partitions),
                "partition_1_size": len(partitions[1]),
                "partition_2_size": len(partitions[2]),
                "partition_3_size": len(partitions[3]),
                "partition_4_size": len(partitions[4])
            }
        }
    
    result = ctl.solve(on_model=on_model)
    
    if result.satisfiable:
        return solution_data
    else:
        return {"error": "No solution exists", 
                "reason": "Problem is unsatisfiable"}


solution = solve_graph_partition()
print(json.dumps(solution, indent=2))
