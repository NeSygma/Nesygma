import clingo
import json

def solve_graph_isomorphism():
    ctl = clingo.Control(["1"])
    
    program = """
    vertex1(0). vertex1(1). vertex1(2). vertex1(3). vertex1(4).
    
    edge1(0,1). edge1(1,0).
    edge1(0,2). edge1(2,0).
    edge1(1,3). edge1(3,1).
    edge1(2,4). edge1(4,2).
    edge1(3,4). edge1(4,3).
    
    vertex2("a"). vertex2("b"). vertex2("c"). vertex2("d"). vertex2("e").
    
    edge2("a","b"). edge2("b","a").
    edge2("a","c"). edge2("c","a").
    edge2("b","d"). edge2("d","b").
    edge2("c","e"). edge2("e","c").
    edge2("d","e"). edge2("e","d").
    
    1 { mapping(V1, V2) : vertex2(V2) } 1 :- vertex1(V1).
    
    :- vertex2(V2), #count { V1 : mapping(V1, V2) } > 1.
    
    :- vertex2(V2), #count { V1 : mapping(V1, V2) } = 0.
    
    :- edge1(U, V), mapping(U, U2), mapping(V, V2), not edge2(U2, V2).
    
    #show mapping/2.
    """
    
    ctl.add("base", [], program)
    ctl.ground([("base", [])])
    
    solution_found = False
    mapping_dict = {}
    
    def on_model(model):
        nonlocal solution_found, mapping_dict
        solution_found = True
        
        for atom in model.symbols(atoms=True):
            if atom.name == "mapping" and len(atom.arguments) == 2:
                v1 = str(atom.arguments[0])
                v2 = str(atom.arguments[1]).strip('"')
                mapping_dict[v1] = v2
    
    result = ctl.solve(on_model=on_model)
    
    return solution_found, mapping_dict

def format_output(is_isomorphic, mapping_dict):
    if not is_isomorphic:
        return {
            "is_isomorphic": False,
            "mapping": None,
            "preserved_edges": []
        }
    
    g1_edges = [(0, 1), (0, 2), (1, 3), (2, 4), (3, 4)]
    
    preserved_edges = []
    for u, v in g1_edges:
        u_str = str(u)
        v_str = str(v)
        mapped_u = mapping_dict[u_str]
        mapped_v = mapping_dict[v_str]
        
        edge_g1 = f"{u},{v}"
        edge_g2 = f"{mapped_u},{mapped_v}"
        preserved_edges.append([edge_g1, edge_g2])
    
    return {
        "is_isomorphic": True,
        "mapping": mapping_dict,
        "preserved_edges": preserved_edges
    }

is_sat, mapping = solve_graph_isomorphism()
output = format_output(is_sat, mapping)
print(json.dumps(output, indent=2))
