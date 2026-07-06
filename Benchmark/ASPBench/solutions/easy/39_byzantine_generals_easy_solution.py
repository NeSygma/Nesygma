import clingo
import json

def solve_byzantine_generals():
    ctl = clingo.Control(["1"])
    
    program = """
    general("G1"). general("G2"). general("G3"). general("G4").
    
    initial_proposal("G1", 1).
    initial_proposal("G2", 1).
    initial_proposal("G3", 0).
    initial_proposal("G4", 1).
    
    traitor("G4").
    
    value(0). value(1).
    
    honest(G) :- general(G), not traitor(G).
    
    vote_count(V, N) :- value(V), 
                        N = #count { G : honest(G), initial_proposal(G, V) }.
    
    max_votes(M) :- M = #max { N : vote_count(_, N) }.
    
    has_max_votes(V) :- vote_count(V, M), max_votes(M).
    
    consensus(V) :- has_max_votes(V), not smaller_with_max(V).
    smaller_with_max(V) :- has_max_votes(V), has_max_votes(V2), V2 < V.
    
    :- not consensus(_).
    :- consensus(V1), consensus(V2), V1 != V2.
    
    all_honest_agree(V) :- value(V), 
                           honest_count(H),
                           vote_count(V, H).
    
    honest_count(N) :- N = #count { G : honest(G) }.
    
    :- all_honest_agree(V), not consensus(V).
    """
    
    ctl.add("base", [], program)
    ctl.ground([("base", [])])
    
    solution = None
    
    def on_model(m):
        nonlocal solution
        atoms = m.symbols(atoms=True)
        
        consensus_value = None
        honest_generals = []
        traitor_general = None
        
        for atom in atoms:
            if atom.match("consensus", 1):
                consensus_value = atom.arguments[0].number
            elif atom.match("honest", 1):
                honest_generals.append(str(atom.arguments[0]).strip('"'))
            elif atom.match("traitor", 1):
                traitor_general = str(atom.arguments[0]).strip('"')
        
        solution = {
            "consensus": consensus_value,
            "honest_generals": sorted(honest_generals),
            "traitor": traitor_general
        }
    
    result = ctl.solve(on_model=on_model)
    
    if result.satisfiable:
        return solution
    else:
        return {"error": "No solution exists", "reason": "UNSAT"}

solution = solve_byzantine_generals()
print(json.dumps(solution, indent=2))
