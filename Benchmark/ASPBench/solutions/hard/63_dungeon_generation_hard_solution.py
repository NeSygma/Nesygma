import clingo
import json
from collections import deque

instance_data = {
    "rooms": [
        {"id": "entrance", "type": "entrance"},
        {"id": "hallway", "type": "chamber"},
        {"id": "barracks", "type": "chamber"},
        {"id": "secret_closet", "type": "secret"},
        {"id": "mess_hall", "type": "chamber"},
        {"id": "kitchen", "type": "chamber"},
        {"id": "treasury", "type": "chamber"},
        {"id": "boss_antechamber", "type": "chamber"},
        {"id": "boss_lair", "type": "boss"}
    ],
    "connections": [
        {"from": "entrance", "to": "hallway", "locked_by": None},
        {"from": "hallway", "to": "barracks", "locked_by": None},
        {"from": "barracks", "to": "secret_closet", "locked_by": None},
        {"from": "hallway", "to": "mess_hall", "locked_by": None},
        {"from": "mess_hall", "to": "kitchen", "locked_by": None},
        {"from": "mess_hall", "to": "treasury", "locked_by": "iron_key"},
        {"from": "treasury", "to": "boss_antechamber", "locked_by": "gold_key"},
        {"from": "boss_antechamber", "to": "boss_lair", "locked_by": None}
    ],
    "items": [
        {"id": "iron_key", "type": "key"},
        {"id": "gold_key", "type": "key"},
        {"id": "trap_kit", "type": "tool"}
    ],
    "treasures": [
        {"id": "silver_locket", "value": 100},
        {"id": "jeweled_crown", "value": 500},
        {"id": "dragon_hoard", "value": 1000}
    ],
    "monsters": [
        {"id": "goblin", "danger_level": 2},
        {"id": "orc", "danger_level": 5},
        {"id": "troll", "danger_level": 10},
        {"id": "dragon", "danger_level": 15}
    ],
    "traps": [
        {"id": "spike_trap", "danger_level": 3, "disarm_tool": "trap_kit"}
    ],
    "constraints": {
        "max_danger_per_room": 15,
        "boss_room_id": "boss_lair"
    }
}

def generate_asp_facts(data):
    facts = []
    
    for room in data["rooms"]:
        facts.append(f'room("{room["id"]}", "{room["type"]}").')
    
    for conn in data["connections"]:
        locked_by = f'"{conn["locked_by"]}"' if conn["locked_by"] else '"null"'
        facts.append(f'connection("{conn["from"]}", "{conn["to"]}", {locked_by}).')
    
    for item in data["items"]:
        facts.append(f'item("{item["id"]}", "{item["type"]}").')
    
    for treasure in data["treasures"]:
        facts.append(f'treasure("{treasure["id"]}", {treasure["value"]}).')
    
    for monster in data["monsters"]:
        facts.append(f'monster("{monster["id"]}", {monster["danger_level"]}).')
    
    for trap in data["traps"]:
        facts.append(f'trap("{trap["id"]}", {trap["danger_level"]}, "{trap["disarm_tool"]}").')
    
    facts.append(f'max_danger({data["constraints"]["max_danger_per_room"]}).')
    facts.append(f'boss_room("{data["constraints"]["boss_room_id"]}").')
    
    return "\n".join(facts)

asp_facts = generate_asp_facts(instance_data)

asp_program = """
""" + asp_facts + """

1 { item_in(I, R) : room(R, _) } 1 :- item(I, _).
1 { treasure_in(T, R) : room(R, _) } 1 :- treasure(T, _).
0 { trap_in(Trap, R) : room(R, _) } 1 :- trap(Trap, _, _).
{ monster_in(M, R, Count) : room(R, _), Count = 1..3 } :- monster(M, _).

reachable("entrance").
reachable(To) :- reachable(From), connection(From, To, "null").
reachable(To) :- reachable(From), connection(From, To, Key), Key != "null", 
                 item_in(Key, KeyRoom), reachable(KeyRoom).

:- item_in(Key, R), item(Key, "key"), not reachable(R).

:- item_in("iron_key", R), connection("mess_hall", "treasury", "iron_key"),
   not reachable_before_treasury(R).

reachable_before_treasury("entrance").
reachable_before_treasury(To) :- reachable_before_treasury(From), 
                                   connection(From, To, "null").
reachable_before_treasury(To) :- reachable_before_treasury(From),
                                   connection(From, To, Key), Key != "null",
                                   Key != "iron_key",
                                   item_in(Key, KeyRoom), 
                                   reachable_before_treasury(KeyRoom).

:- item_in("gold_key", R), connection("treasury", "boss_antechamber", "gold_key"),
   not reachable_before_boss_ante(R).

reachable_before_boss_ante("entrance").
reachable_before_boss_ante(To) :- reachable_before_boss_ante(From), 
                                    connection(From, To, "null").
reachable_before_boss_ante(To) :- reachable_before_boss_ante(From),
                                    connection(From, To, Key), Key != "null",
                                    Key != "gold_key",
                                    item_in(Key, KeyRoom), 
                                    reachable_before_boss_ante(KeyRoom).

:- boss_room(BR), monster("dragon", _), not monster_in("dragon", BR, _).
:- monster_in("dragon", R, _), boss_room(BR), R != BR.
1 { monster_in("dragon", BR, 1) } 1 :- boss_room(BR).

monster_danger(R, D) :- room(R, _), 
    D = #sum { Danger * Count, M : monster_in(M, R, Count), monster(M, Danger) }.

trap_active(Trap, R) :- trap_in(Trap, R), trap(Trap, _, Tool), not item_in(Tool, R).

trap_danger(R, D) :- room(R, _),
    D = #sum { Danger, Trap : trap_active(Trap, R), trap(Trap, Danger, _) }.

room_danger(R, Total) :- room(R, _),
    monster_danger(R, MD),
    trap_danger(R, TD),
    Total = MD + TD.

room_danger(R, TD) :- room(R, _),
    not monster_danger(R, _),
    trap_danger(R, TD).

room_danger(R, MD) :- room(R, _),
    monster_danger(R, MD),
    not trap_danger(R, _).

room_danger(R, 0) :- room(R, _),
    not monster_danger(R, _),
    not trap_danger(R, _).

:- room_danger(R, D), max_danger(Max), D > Max.
:- room(R, _), not reachable(R).
:- boss_room(BR), not reachable(BR).
"""

ctl = clingo.Control(["1"])
ctl.add("base", [], asp_program)
ctl.ground([("base", [])])

solution_data = None

def on_model(model):
    global solution_data
    
    item_placements = {}
    treasure_placements = {}
    monster_placements = {}
    trap_placements = {}
    room_dangers = {}
    
    for atom in model.symbols(atoms=True):
        name = atom.name
        
        if name == "item_in" and len(atom.arguments) == 2:
            item = str(atom.arguments[0]).strip('"')
            room = str(atom.arguments[1]).strip('"')
            item_placements[item] = room
            
        elif name == "treasure_in" and len(atom.arguments) == 2:
            treasure = str(atom.arguments[0]).strip('"')
            room = str(atom.arguments[1]).strip('"')
            treasure_placements[treasure] = room
            
        elif name == "monster_in" and len(atom.arguments) == 3:
            monster = str(atom.arguments[0]).strip('"')
            room = str(atom.arguments[1]).strip('"')
            count = int(str(atom.arguments[2]))
            if room not in monster_placements:
                monster_placements[room] = []
            monster_placements[room].append({"type": monster, "count": count})
            
        elif name == "trap_in" and len(atom.arguments) == 2:
            trap = str(atom.arguments[0]).strip('"')
            room = str(atom.arguments[1]).strip('"')
            trap_placements[room] = trap
            
        elif name == "room_danger" and len(atom.arguments) == 2:
            room = str(atom.arguments[0]).strip('"')
            danger = int(str(atom.arguments[1]))
            room_dangers[room] = danger
    
    solution_data = {
        "item_placements": item_placements,
        "treasure_placements": treasure_placements,
        "monster_placements": monster_placements,
        "trap_placements": trap_placements,
        "room_dangers": room_dangers
    }

result = ctl.solve(on_model=on_model)

if not result.satisfiable:
    print(json.dumps({"error": "No solution exists"}))
else:
    room_layout = []
    for room_data in instance_data["rooms"]:
        room_id = room_data["id"]
        
        monsters = solution_data["monster_placements"].get(room_id, [])
        treasures = [t for t, r in solution_data["treasure_placements"].items() if r == room_id]
        items = [i for i, r in solution_data["item_placements"].items() if r == room_id]
        
        traps = []
        if room_id in solution_data["trap_placements"]:
            trap_id = solution_data["trap_placements"][room_id]
            trap_tool = None
            for trap in instance_data["traps"]:
                if trap["id"] == trap_id:
                    trap_tool = trap["disarm_tool"]
                    break
            is_active = trap_tool not in items
            traps.append({"type": trap_id, "active": is_active})
        
        danger = solution_data["room_dangers"].get(room_id, 0)
        
        room_layout.append({
            "room_id": room_id,
            "monsters": monsters,
            "treasures": treasures,
            "items": items,
            "traps": traps,
            "danger_level": danger
        })
    
    def find_path(connections, start, end, item_locs):
        initial_keys = set()
        for item, room in item_locs.items():
            if room == start and item.endswith("_key"):
                initial_keys.add(item)
        
        queue = deque([(start, [start], initial_keys)])
        visited = {}
        
        while queue:
            current, path, keys = queue.popleft()
            
            if current == end:
                return path
            
            state = (current, frozenset(keys))
            if state in visited:
                continue
            visited[state] = True
            
            for conn in connections:
                if conn["from"] == current:
                    to_room = conn["to"]
                    required_key = conn["locked_by"]
                    
                    can_pass = required_key is None or required_key in keys
                    
                    if can_pass:
                        new_path = path + [to_room]
                        new_keys = keys.copy()
                        
                        for item, room in item_locs.items():
                            if room == to_room and item.endswith("_key"):
                                new_keys.add(item)
                        
                        queue.append((to_room, new_path, new_keys))
        
        return None
    
    main_path = find_path(instance_data["connections"], "entrance", "boss_lair", 
                          solution_data["item_placements"])
    
    key_order = []
    for item, room in solution_data["item_placements"].items():
        if item.endswith("_key"):
            unlocks_room = None
            for conn in instance_data["connections"]:
                if conn["locked_by"] == item:
                    unlocks_room = conn["to"]
                    break
            
            key_order.append({
                "key": item,
                "found_in": room,
                "unlocks": unlocks_room
            })
    
    if main_path:
        key_order.sort(key=lambda x: main_path.index(x["found_in"]) if x["found_in"] in main_path else 999)
    
    path_analysis = {
        "solvable": main_path is not None,
        "main_path": main_path if main_path else [],
        "key_acquisition_order": key_order
    }
    
    total_danger = sum(solution_data["room_dangers"].values())
    
    balance_analysis = {
        "total_danger": total_danger,
        "difficulty_progression_score": 0
    }
    
    output = {
        "instance": instance_data,
        "solution": {
            "room_layout": room_layout,
            "path_analysis": path_analysis,
            "balance_analysis": balance_analysis
        }
    }
    
    print(json.dumps(output, indent=2))
