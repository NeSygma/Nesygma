import clingo
import json

def generate_asp_program():
    program = """
    % Graph G1 vertices
    vertex_g1("1"). vertex_g1("2"). vertex_g1("3"). vertex_g1("4").
    vertex_g1("5"). vertex_g1("6"). vertex_g1("7"). vertex_g1("8").
    
    % Graph G2 vertices
    vertex_g2("a"). vertex_g2("b"). vertex_g2("c"). vertex_g2("d").
    vertex_g2("e"). vertex_g2("f"). vertex_g2("g"). vertex_g2("h").
    
    % Colors in G1
    color_g1("1", "red"). color_g1("2", "red"). color_g1("5", "red"). color_g1("6", "red").
    color_g1("3", "blue"). color_g1("4", "blue"). color_g1("7", "blue"). color_g1("8", "blue").
    
    % Colors in G2
    color_g2("a", "red"). color_g2("b", "red"). color_g2("e", "red"). color_g2("f", "red").
    color_g2("c", "blue"). color_g2("d", "blue"). color_g2("g", "blue"). color_g2("h", "blue").
    
    % Special vertices
    special_g1("1").
    special_g2("a").
    
    % Edges in G1 (undirected)
    edge_g1("1", "3", 10). edge_g1("1", "4", 20). edge_g1("2", "3", 20). edge_g1("2", "4", 10).
    edge_g1("5", "7", 10). edge_g1("5", "8", 20). edge_g1("6", "7", 20). edge_g1("6", "8", 10).
    edge_g1("1", "5", 30). edge_g1("2", "6", 30). edge_g1("3", "7", 40). edge_g1("4", "8", 40).
    
    % Edges in G2 (undirected)
    edge_g2("a", "c", 10). edge_g2("a", "d", 20). edge_g2("b", "c", 20). edge_g2("b", "d", 10).
    edge_g2("e", "g", 10). edge_g2("e", "h", 20). edge_g2("f", "g", 20). edge_g2("f", "h", 10).
    edge_g2("a", "e", 30). edge_g2("b", "f", 30). edge_g2("c", "g", 40). edge_g2("d", "h", 40).
    
    % Each G1 vertex maps to exactly one G2 vertex
    1 { maps_to(V1, V2) : vertex_g2(V2) } 1 :- vertex_g1(V1).
    
    % Bijection constraint - each G2 vertex is mapped from exactly one G1 vertex
    1 { maps_to(V1, V2) : vertex_g1(V1) } 1 :- vertex_g2(V2).
    
    % Color preservation constraint
    :- maps_to(V1, V2), color_g1(V1, C1), color_g2(V2, C2), C1 != C2.
    
    % Special vertex preservation constraint
    :- maps_to(V1, V2), special_g1(V1), not special_g2(V2).
    :- maps_to(V1, V2), vertex_g1(V1), not special_g1(V1), special_g2(V2).
    
    % Helper predicate for edge existence (handles undirected edges)
    has_edge_g1(U, V, W) :- edge_g1(U, V, W).
    has_edge_g1(U, V, W) :- edge_g1(V, U, W).
    
    has_edge_g2(U, V, W) :- edge_g2(U, V, W).
    has_edge_g2(U, V, W) :- edge_g2(V, U, W).
    
    % Edge and weight preservation
    :- has_edge_g1(U1, V1, W), maps_to(U1, U2), maps_to(V1, V2), not has_edge_g2(U2, V2, W).
    :- has_edge_g2(U2, V2, W), maps_to(U1, U2), maps_to(V1, V2), not has_edge_g1(U1, V1, W).
    
    % Forbidden subgraph constraint
    has_triangle_weight_60(A2, B2, C2) :-
        maps_to(A1, A2), maps_to(B1, B2), maps_to(C1, C2),
        A1 != B1, B1 != C1, A1 != C1,
        has_edge_g1(A1, B1, W1), has_edge_g1(B1, C1, W2), has_edge_g1(C1, A1, W3),
        W1 + W2 + W3 == 60.
    
    :- has_triangle_weight_60(A2, B2, C2), special_g2(A2).
    :- has_triangle_weight_60(A2, B2, C2), special_g2(B2).
    :- has_triangle_weight_60(A2, B2, C2), special_g2(C2).
    """
    return program

def solve_isomorphism():
    ctl = clingo.Control(["1"])
    
    program = generate_asp_program()
    ctl.add("base", [], program)
    ctl.ground([("base", [])])
    
    solution_data = None
    
    def on_model(model):
        nonlocal solution_data
        atoms = model.symbols(atoms=True)
        
        mapping = {}
        for atom in atoms:
            if atom.name == "maps_to" and len(atom.arguments) == 2:
                v1 = str(atom.arguments[0]).strip('"')
                v2 = str(atom.arguments[1]).strip('"')
                mapping[v1] = v2
        
        solution_data = mapping
    
    result = ctl.solve(on_model=on_model)
    
    if result.satisfiable and solution_data:
        return True, solution_data
    else:
        return False, None

def format_output(is_isomorphic, mapping):
    if not is_isomorphic or not mapping:
        return {
            "is_isomorphic": False,
            "mapping": None,
            "preserved_weighted_edges": []
        }
    
    g1_edges = [
        ("1", "3", 10), ("1", "4", 20), ("2", "3", 20), ("2", "4", 10),
        ("5", "7", 10), ("5", "8", 20), ("6", "7", 20), ("6", "8", 10),
        ("1", "5", 30), ("2", "6", 30), ("3", "7", 40), ("4", "8", 40)
    ]
    
    preserved_edges = []
    for u1, v1, w in g1_edges:
        u2 = mapping[u1]
        v2 = mapping[v1]
        
        g1_edge = [u1, v1, w] if u1 < v1 else [v1, u1, w]
        g2_edge = [u2, v2, w] if u2 < v2 else [v2, u2, w]
        
        preserved_edges.append([g1_edge, g2_edge])
    
    preserved_edges.sort(key=lambda x: (x[0][0], x[0][1]))
    
    return {
        "is_isomorphic": True,
        "mapping": mapping,
        "preserved_weighted_edges": preserved_edges
    }

is_isomorphic, mapping = solve_isomorphism()
output = format_output(is_isomorphic, mapping)
print(json.dumps(output, indent=2))
