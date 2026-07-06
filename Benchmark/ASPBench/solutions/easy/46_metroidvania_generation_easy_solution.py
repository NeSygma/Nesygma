import clingo
import json


def solve_metroidvania():
    asp_program = """
    room("A"; "B"; "C"; "D"; "E"; "F"; "G"; "H").
    key("key1"; "key2"; "key3").
    requirement("null"; "key1"; "key2"; "key3").
    
    start("A").
    
    room_pair(R1, R2) :- room(R1), room(R2), R1 != R2.
    
    0 { conn(R1, R2, Req) : requirement(Req) } 1 :- room_pair(R1, R2).
    
    1 { item_at(K, R) : room(R) } 1 :- key(K).
    
    :- room(R), R != "A", not conn(_, R, _).
    
    :- start(S), not conn(S, _, _).
    
    reachable("A", 0).
    
    key_available(K, N) :- item_at(K, R), reachable(R, N-1), N > 0, N <= 10.
    
    reachable(R2, N) :- reachable(R1, N-1), conn(R1, R2, "null"), N > 0, N <= 10.
    reachable(R2, N) :- reachable(R1, N-1), conn(R1, R2, K), key_available(K, N), 
                        key(K), N > 0, N <= 10.
    
    :- room(R), not reachable(R, _).
    
    :- room(R), not conn(R, _, _), not conn(_, R, _).
    
    :- #count { R1, R2 : conn(R1, R2, _) } < 8.
    
    :- #count { R1, R2 : conn(R1, R2, _) } > 15.
    
    :- item_at(K, R), key(K), not reachable_without_key(R, K).
    
    reachable_without_key(R, ExcludeKey) :- start(R), key(ExcludeKey).
    
    reachable_without_key(R2, ExcludeKey) :- 
        reachable_without_key(R1, ExcludeKey),
        conn(R1, R2, "null"),
        key(ExcludeKey).
    
    reachable_without_key(R2, ExcludeKey) :- 
        reachable_without_key(R1, ExcludeKey),
        conn(R1, R2, K),
        key(K), key(ExcludeKey),
        K != ExcludeKey,
        key_available_without(K, ExcludeKey).
    
    key_available_without(K, ExcludeKey) :- 
        item_at(K, R), 
        reachable_without_key(R, ExcludeKey),
        K != ExcludeKey.
    
    #show conn/3.
    #show item_at/2.
    """
    
    ctl = clingo.Control(["1"])
    ctl.add("base", [], asp_program)
    ctl.ground([("base", [])])
    
    solution_data = None
    
    def on_model(m):
        nonlocal solution_data
        atoms = m.symbols(atoms=True)
        
        connections = []
        item_locations = {}
        
        for atom in atoms:
            if atom.name == "conn" and len(atom.arguments) == 3:
                from_room = str(atom.arguments[0]).strip('"')
                to_room = str(atom.arguments[1]).strip('"')
                requires = str(atom.arguments[2]).strip('"')
                
                connections.append({
                    "from": from_room,
                    "to": to_room,
                    "requires": None if requires == "null" else requires
                })
            
            elif atom.name == "item_at" and len(atom.arguments) == 2:
                key_name = str(atom.arguments[0]).strip('"')
                room_name = str(atom.arguments[1]).strip('"')
                item_locations[key_name] = room_name
        
        solution_data = {
            "connections": connections,
            "item_locations": item_locations
        }
    
    result = ctl.solve(on_model=on_model)
    
    if not result.satisfiable:
        return {"error": "No solution exists", 
                "reason": "Cannot create valid Metroidvania layout with given constraints"}
    
    return solution_data


def verify_reachability(connections, item_locations, start_room="A"):
    graph = {}
    for conn in connections:
        if conn["from"] not in graph:
            graph[conn["from"]] = []
        graph[conn["from"]].append({
            "to": conn["to"],
            "requires": conn["requires"]
        })
    
    reachable_rooms = set([start_room])
    available_keys = set()
    changed = True
    
    max_iterations = 20
    iteration = 0
    
    while changed and iteration < max_iterations:
        changed = False
        iteration += 1
        
        for room in list(reachable_rooms):
            for key, location in item_locations.items():
                if location == room and key not in available_keys:
                    available_keys.add(key)
                    changed = True
        
        for room in list(reachable_rooms):
            if room in graph:
                for edge in graph[room]:
                    target = edge["to"]
                    required_key = edge["requires"]
                    
                    if target not in reachable_rooms:
                        if required_key is None or required_key in available_keys:
                            reachable_rooms.add(target)
                            changed = True
    
    all_rooms = set(["A", "B", "C", "D", "E", "F", "G", "H"])
    return all_rooms.issubset(reachable_rooms)


solution = solve_metroidvania()

if "error" in solution:
    print(json.dumps(solution))
else:
    verification = verify_reachability(solution["connections"], solution["item_locations"])
    
    final_output = {
        "rooms": ["A", "B", "C", "D", "E", "F", "G", "H"],
        "connections": solution["connections"],
        "item_locations": solution["item_locations"],
        "reachability_verified": verification
    }
    
    print(json.dumps(final_output, indent=2))
