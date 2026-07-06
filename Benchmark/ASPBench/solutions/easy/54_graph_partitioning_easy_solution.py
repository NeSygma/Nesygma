import clingo
import json


def generate_asp_program():
    """Generate the ASP program for graph partitioning"""
    
    program = """
    vertex(0..7).
    
    edge(0,1). edge(0,4).
    edge(1,2). edge(1,5).
    edge(2,3). edge(2,6).
    edge(3,7).
    edge(4,5). edge(4,6).
    edge(5,7).
    edge(6,7).
    
    partition(1;2).
    
    1 { in_partition(V, P) : partition(P) } 1 :- vertex(V).
    
    :- #count { V : in_partition(V, 1) } != 4.
    
    :- #count { V : in_partition(V, 2) } != 4.
    
    crossing_edge(V1, V2) :- edge(V1, V2), 
                             in_partition(V1, P1), 
                             in_partition(V2, P2), 
                             P1 != P2.
    
    cut_size(N) :- N = #count { V1, V2 : crossing_edge(V1, V2) }.
    
    :- cut_size(N), N > 3.
    
    #show in_partition/2.
    #show cut_size/1.
    #show crossing_edge/2.
    """
    
    return program


def solve_graph_partitioning():
    """Solve the graph partitioning problem using clingo"""
    
    ctl = clingo.Control(["1"])
    
    program = generate_asp_program()
    ctl.add("base", [], program)
    
    ctl.ground([("base", [])])
    
    solution_data = None
    
    def on_model(model):
        nonlocal solution_data
        
        partition_1 = []
        partition_2 = []
        cut_edges = []
        cut_size_value = 0
        
        for atom in model.symbols(atoms=True):
            if atom.name == "in_partition" and len(atom.arguments) == 2:
                vertex = atom.arguments[0].number
                partition = atom.arguments[1].number
                
                if partition == 1:
                    partition_1.append(vertex)
                elif partition == 2:
                    partition_2.append(vertex)
            
            elif atom.name == "crossing_edge" and len(atom.arguments) == 2:
                v1 = atom.arguments[0].number
                v2 = atom.arguments[1].number
                cut_edges.append({"from": v1, "to": v2})
            
            elif atom.name == "cut_size" and len(atom.arguments) == 1:
                cut_size_value = atom.arguments[0].number
        
        partition_1.sort()
        partition_2.sort()
        
        cut_edges.sort(key=lambda e: (e["from"], e["to"]))
        
        solution_data = {
            "partition_1": partition_1,
            "partition_2": partition_2,
            "cut_size": cut_size_value,
            "cut_edges": cut_edges,
            "balance": {
                "partition_1_size": len(partition_1),
                "partition_2_size": len(partition_2),
                "is_balanced": len(partition_1) == 4 and len(partition_2) == 4
            }
        }
    
    result = ctl.solve(on_model=on_model)
    
    if result.satisfiable and solution_data is not None:
        return solution_data
    else:
        return {
            "error": "No solution exists",
            "reason": "Could not find a balanced partition with cut size <= 3"
        }


if __name__ == "__main__":
    solution = solve_graph_partitioning()
    print(json.dumps(solution, indent=2))
