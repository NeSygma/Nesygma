import clingo
import json

def solve_blocks_world():
    asp_program = """
    block(a). block(b). block(c). block(d). block(e). block(f).
    block(g). block(h). block(i). block(j). block(k). block(l).
    
    weight(a, 1). weight(b, 2). weight(c, 3). weight(d, 4).
    weight(e, 5). weight(f, 6). weight(g, 7). weight(h, 8).
    weight(i, 9). weight(j, 10). weight(k, 11). weight(l, 12).
    
    time(0..50).
    action_time(0..49).
    
    on_table(d, 0).
    on(c, d, 0).
    on(b, c, 0).
    on(a, b, 0).
    
    on_table(h, 0).
    on(g, h, 0).
    on(f, g, 0).
    on(e, f, 0).
    
    on_table(l, 0).
    on(k, l, 0).
    on(j, k, 0).
    on(i, j, 0).
    
    goal_on_table(l).
    goal_on(i, l).
    goal_on(f, i).
    goal_on(c, f).
    
    goal_on_table(k).
    goal_on(h, k).
    goal_on(e, h).
    goal_on(b, e).
    
    goal_on_table(j).
    goal_on(g, j).
    goal_on(d, g).
    goal_on(a, d).
    
    clear(B, T) :- block(B), time(T), not has_block_on_top(B, T).
    has_block_on_top(B, T) :- on(_, B, T).
    
    on_something(B, T) :- on_table(B, T).
    on_something(B, T) :- on(B, _, T).
    
    valid_move_source(B, T) :- clear(B, T), on_something(B, T), 
        action_time(T).
    
    { move_to_block(B, To, T) : block(To), clear(To, T), B != To } :- 
        valid_move_source(B, T).
    
    { move_to_table(B, T) } :- valid_move_source(B, T).
    
    :- move_to_block(B1, _, T), move_to_block(B2, _, T), B1 != B2.
    :- move_to_block(B1, _, T), move_to_table(B2, T), B1 != B2.
    :- move_to_block(B, _, T), move_to_table(B, T).
    :- move_to_table(B1, T), move_to_table(B2, T), B1 != B2.
    
    action_taken(T) :- move_to_block(_, _, T).
    action_taken(T) :- move_to_table(_, T).
    
    :- move_to_block(B, B, T).
    
    :- move_to_block(B, To, T), weight(B, W1), weight(To, W2), W1 > W2.
    
    :- move_to_table(B, T), on_table(B, T).
    
    :- move_to_block(B, To, T), on(B, To, T).
    
    on(B, To, T+1) :- move_to_block(B, To, T).
    
    on_table(B, T+1) :- move_to_table(B, T).
    
    on_table(B, T+1) :- on_table(B, T), time(T+1), 
        not move_to_block(B, _, T),
        not has_block_on_top(B, T).
    on_table(B, T+1) :- on_table(B, T), time(T+1),
        has_block_on_top(B, T).
    
    on(B, Below, T+1) :- on(B, Below, T), time(T+1),
        not move_to_block(B, _, T),
        not move_to_table(B, T).
    
    :- on_table(B, T), on(B, _, T).
    
    :- on(B, Below1, T), on(B, Below2, T), Below1 != Below2.
    
    :- block(B), time(T), not on_table(B, T), not on(B, _, T).
    
    :- time(T), #count { B : on_table(B, T) } > 6.
    
    height(B, 1, T) :- on_table(B, T).
    height(B, H+1, T) :- on(B, Below, T), height(Below, H, T), H < 5.
    
    :- height(_, H, T), H > 5.
    
    :- block(B), time(T), on_something(B, T), not has_height(B, T).
    has_height(B, T) :- height(B, _, T).
    
    :- goal_on_table(B), not on_table(B, 50).
    :- goal_on(B, Below), not on(B, Below, 50).
    
    last_action(T) :- action_taken(T), not action_taken(T+1), 
        action_time(T).
    
    #minimize { T : last_action(T) }.
    """
    
    ctl = clingo.Control(["1"])
    ctl.add("base", [], asp_program)
    ctl.ground([("base", [])])
    
    solution_data = None
    
    def on_model(model):
        nonlocal solution_data
        
        actions = []
        
        for atom in model.symbols(atoms=True):
            if atom.name == "move_to_block" and len(atom.arguments) == 3:
                block = str(atom.arguments[0])
                to_block = str(atom.arguments[1])
                timestep = atom.arguments[2].number
                actions.append({
                    'time': timestep,
                    'block': block.upper(),
                    'to': to_block.upper(),
                    'type': 'to_block'
                })
            elif atom.name == "move_to_table" and len(atom.arguments) == 2:
                block = str(atom.arguments[0])
                timestep = atom.arguments[1].number
                actions.append({
                    'time': timestep,
                    'block': block.upper(),
                    'to': 'table',
                    'type': 'to_table'
                })
        
        actions.sort(key=lambda x: x['time'])
        
        state = {
            'on_table': {'d', 'h', 'l'},
            'on': {
                'a': 'b', 'b': 'c', 'c': 'd',
                'e': 'f', 'f': 'g', 'g': 'h',
                'i': 'j', 'j': 'k', 'k': 'l'
            }
        }
        
        formatted_actions = []
        for i, action in enumerate(actions):
            block = action['block'].lower()
            
            if block in state['on_table']:
                from_pos = 'table'
            elif block in state['on']:
                from_pos = state['on'][block].upper()
            else:
                from_pos = 'unknown'
            
            formatted_actions.append({
                'step': i + 1,
                'action': 'move',
                'block': action['block'],
                'from': from_pos,
                'to': action['to']
            })
            
            if block in state['on_table']:
                state['on_table'].remove(block)
            elif block in state['on']:
                del state['on'][block]
            
            if action['type'] == 'to_table':
                state['on_table'].add(block)
            else:
                state['on'][block] = action['to'].lower()
        
        solution_data = {
            'plan_length': len(formatted_actions),
            'actions': formatted_actions
        }
    
    result = ctl.solve(on_model=on_model)
    
    if result.satisfiable:
        return solution_data
    else:
        return {"error": "No solution exists", 
                "reason": "Problem is unsatisfiable"}

solution = solve_blocks_world()
print(json.dumps(solution, indent=2))
