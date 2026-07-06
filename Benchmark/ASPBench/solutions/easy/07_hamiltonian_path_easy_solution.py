import clingo
import json

def create_asp_program():
    program = """
    vertex(0). vertex(1). vertex(2). vertex(3). vertex(4). vertex(5).
    
    edge(0,1). edge(0,2). 
    edge(1,2). edge(1,3). edge(1,4). 
    edge(2,1). edge(2,3). edge(2,4). 
    edge(3,4). edge(3,5). 
    edge(4,3). edge(4,5).
    
    position(0..5).
    
    1 { path(V, P) : vertex(V) } 1 :- position(P).
    
    1 { path(V, P) : position(P) } 1 :- vertex(V).
    
    :- not path(0, 0).
    
    :- not path(5, 5).
    
    :- path(V1, P), path(V2, P+1), position(P), P < 5, not edge(V1, V2).
    """
    return program

def solve_hamiltonian_paths():
    ctl = clingo.Control(["0"])
    
    program = create_asp_program()
    ctl.add("base", [], program)
    
    ctl.ground([("base", [])])
    
    all_paths = []
    
    def on_model(model):
        path_atoms = []
        for atom in model.symbols(atoms=True):
            if atom.name == "path" and len(atom.arguments) == 2:
                vertex = atom.arguments[0].number
                position = atom.arguments[1].number
                path_atoms.append((vertex, position))
        
        path_atoms.sort(key=lambda x: x[1])
        path_sequence = [vertex for vertex, pos in path_atoms]
        all_paths.append(path_sequence)
    
    result = ctl.solve(on_model=on_model)
    
    return all_paths, result

def format_output(paths, result):
    output = {
        "paths": paths,
        "count": len(paths),
        "exists": result.satisfiable and len(paths) > 0
    }
    return output

paths, result = solve_hamiltonian_paths()
output = format_output(paths, result)
print(json.dumps(output, indent=2))
