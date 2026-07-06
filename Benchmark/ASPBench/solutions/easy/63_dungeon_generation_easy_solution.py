import clingo
import json
from collections import deque

def solve_dungeon():
    asp_program = """
% Facts from problem description

% Rooms: room(id, type, size)
room("room1", "entrance", "small").
room("room2", "chamber", "large").
room("room3", "corridor", "small").
room("room4", "chamber", "medium").
room("room5", "treasury", "medium").
room("room6", "corridor", "small").
room("room7", "boss_room", "large").

% Connections (bidirectional)
connects("room1", "room2").
connects("room1", "room3").
connects("room2", "room4").
connects("room3", "room5").
connects("room4", "room6").
connects("room5", "room6").
connects("room5", "room7").

% Make connections symmetric
connects(R2, R1) :- connects(R1, R2).

% Treasures: treasure(id, value, rarity)
treasure("treasure1", 100, "common").
treasure("treasure2", 500, "rare").
treasure("treasure3", 1000, "legendary").

% Monsters: monster(type, danger_level, group_size)
monster("goblin", 2, 3).
monster("orc", 4, 2).
monster("dragon", 8, 1).

% Constants
max_danger(10).
entrance("room1").
exit("room7").

% Rarity ordering for strategic placement
rarity_value("common", 1).
rarity_value("rare", 2).
rarity_value("legendary", 3).

% --- CHOICE RULES ---

% Each treasure must be placed in exactly one room
1 { treasure_in(T, R) : room(R, _, _) } 1 :- treasure(T, _, _).

% Monsters can be placed in rooms (0 to group_size count per room per monster type)
0 { monster_in(M, R, Count) : Count = 1..GroupSize } 1 :- 
    monster(M, _, GroupSize), room(R, _, _).

% --- DERIVED PREDICATES ---

% Calculate danger level for each room
room_danger(R, TotalDanger) :- 
    room(R, _, _),
    TotalDanger = #sum { Danger * Count, M : monster_in(M, R, Count), monster(M, Danger, _) }.

% Reachability from entrance
reachable(R) :- entrance(R).
reachable(R2) :- reachable(R1), connects(R1, R2).

% --- CONSTRAINTS ---

% Constraint 1: Danger limit per room (max 10)
:- room_danger(R, D), max_danger(MaxD), D > MaxD.

% Constraint 2: All rooms must be reachable
:- room(R, _, _), not reachable(R).

% Constraint 3: Legendary treasure should be in a room with danger >= 6
:- treasure_in(T, R), treasure(T, _, "legendary"), room_danger(R, D), D < 6.

% Constraint 4: Common treasure should not be in highest danger rooms
:- treasure_in(T, R), treasure(T, _, "common"), room_danger(R, D), D > 6.

% Constraint 5: Entrance should be safe
:- entrance(R), room_danger(R, D), D > 4.

% Constraint 6: At least some monsters should be placed
:- #count { M, R : monster_in(M, R, _) } < 3.
"""

    ctl = clingo.Control(["1"])
    ctl.add("base", [], asp_program)
    ctl.ground([("base", [])])

    solution_data = None

    def on_model(model):
        nonlocal solution_data
        solution_data = {
            'treasure_placements': [],
            'monster_placements': [],
            'room_dangers': {}
        }
        
        for atom in model.symbols(atoms=True):
            if atom.name == "treasure_in" and len(atom.arguments) == 2:
                treasure_id = str(atom.arguments[0])
                room_id = str(atom.arguments[1])
                solution_data['treasure_placements'].append({
                    'treasure': treasure_id,
                    'room': room_id
                })
            elif atom.name == "monster_in" and len(atom.arguments) == 3:
                monster_type = str(atom.arguments[0])
                room_id = str(atom.arguments[1])
                count = atom.arguments[2].number
                solution_data['monster_placements'].append({
                    'monster': monster_type,
                    'room': room_id,
                    'count': count
                })
            elif atom.name == "room_danger" and len(atom.arguments) == 2:
                room_id = str(atom.arguments[0])
                danger = atom.arguments[1].number
                solution_data['room_dangers'][room_id] = danger

    result = ctl.solve(on_model=on_model)

    if not result.satisfiable:
        return {"error": "No solution exists", "reason": "Constraints cannot be satisfied"}

    return solution_data

def build_output(solution_data):
    room_info = {
        "room1": {"type": "entrance", "size": "small"},
        "room2": {"type": "chamber", "size": "large"},
        "room3": {"type": "corridor", "size": "small"},
        "room4": {"type": "chamber", "size": "medium"},
        "room5": {"type": "treasury", "size": "medium"},
        "room6": {"type": "corridor", "size": "small"},
        "room7": {"type": "boss_room", "size": "large"}
    }

    treasure_info = {
        "treasure1": {"value": 100, "rarity": "common"},
        "treasure2": {"value": 500, "rarity": "rare"},
        "treasure3": {"value": 1000, "rarity": "legendary"}
    }

    connections = {
        "room1": ["room2", "room3"],
        "room2": ["room1", "room4"],
        "room3": ["room1", "room5"],
        "room4": ["room2", "room6"],
        "room5": ["room3", "room6", "room7"],
        "room6": ["room4", "room5"],
        "room7": ["room5"]
    }

    room_layout = []
    for room_id in sorted(room_info.keys()):
        clean_room_id = f'"{room_id}"'
        
        monsters = []
        for mp in solution_data['monster_placements']:
            if mp['room'] == clean_room_id:
                monster_type = mp['monster'].strip('"')
                monsters.append({
                    "type": monster_type,
                    "count": mp['count']
                })
        
        treasures = []
        for tp in solution_data['treasure_placements']:
            if tp['room'] == clean_room_id:
                treasures.append(tp['treasure'].strip('"'))
        
        danger_level = solution_data['room_dangers'].get(clean_room_id, 0)
        
        room_layout.append({
            "room_id": room_id,
            "monsters": monsters,
            "treasures": treasures,
            "danger_level": danger_level
        })

    def find_path_bfs(start, end, connections):
        queue = deque([(start, [start])])
        visited = {start}
        
        while queue:
            current, path = queue.popleft()
            
            if current == end:
                return path
            
            for neighbor in connections.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        return None

    entrance_to_exit_path = find_path_bfs("room1", "room7", connections)

    def calculate_path_stats(path, room_layout):
        total_danger = 0
        treasures_found = []
        
        for room_id in path:
            for room in room_layout:
                if room['room_id'] == room_id:
                    total_danger += room['danger_level']
                    treasures_found.extend(room['treasures'])
                    break
        
        return total_danger, treasures_found

    path_danger, path_treasures = calculate_path_stats(entrance_to_exit_path, room_layout)

    connectivity = {
        "paths": [
            {
                "from": "room1",
                "to": "room7",
                "route": entrance_to_exit_path,
                "total_danger": path_danger,
                "treasures_found": path_treasures
            }
        ],
        "isolated_rooms": []
    }

    total_danger = sum(room['danger_level'] for room in room_layout)

    treasure_distribution = {"common": 0, "rare": 0, "legendary": 0}
    for room in room_layout:
        for treasure_id in room['treasures']:
            rarity = treasure_info[treasure_id]['rarity']
            treasure_distribution[rarity] += 1

    if total_danger <= 15:
        difficulty = "easy"
    elif total_danger <= 30:
        difficulty = "balanced"
    elif total_danger <= 45:
        difficulty = "hard"
    else:
        difficulty = "extreme"

    balance_analysis = {
        "total_danger": total_danger,
        "treasure_distribution": treasure_distribution,
        "difficulty_progression": difficulty
    }

    return {
        "room_layout": room_layout,
        "connectivity": connectivity,
        "balance_analysis": balance_analysis
    }

if __name__ == "__main__":
    solution_data = solve_dungeon()
    if "error" in solution_data:
        print(json.dumps(solution_data))
    else:
        final_output = build_output(solution_data)
        print(json.dumps(final_output, indent=2))
