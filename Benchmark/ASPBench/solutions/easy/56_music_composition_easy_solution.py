import clingo
import json

def create_asp_program():
    return """
    % Facts: C major scale with semitone values (C=0)
    note("C", 0).
    note("D", 2).
    note("E", 4).
    note("F", 5).
    note("G", 7).
    note("A", 9).
    note("B", 11).
    
    % Positions in melody
    position(1..8).
    
    % Choice rule: Each position gets exactly one note
    1 { melody(Pos, NoteName) : note(NoteName, _) } 1 :- position(Pos).
    
    % Constraint: Start on C
    :- melody(1, N), N != "C".
    
    % Constraint: End on C
    :- melody(8, N), N != "C".
    
    % Define intervals between consecutive notes
    interval(Pos, Diff) :- 
        melody(Pos, N1), melody(Pos+1, N2),
        note(N1, S1), note(N2, S2),
        position(Pos), Pos < 8,
        Diff = S2 - S1.
    
    % Constraint: No leaps greater than 4 semitones (in absolute value)
    :- interval(Pos, Diff), Diff > 4.
    :- interval(Pos, Diff), Diff < -4.
    
    % Define leaps (intervals > 2 semitones in absolute value)
    leap(Pos) :- interval(Pos, Diff), Diff > 2.
    leap(Pos) :- interval(Pos, Diff), Diff < -2.
    
    % Define direction: up(Pos) if interval is positive, down(Pos) if negative
    up(Pos) :- interval(Pos, Diff), Diff > 0.
    down(Pos) :- interval(Pos, Diff), Diff < 0.
    
    % Direction change: when direction switches from up to down or vice versa
    direction_change(Pos) :- 
        position(Pos), Pos > 1, Pos < 8,
        up(Pos-1), down(Pos).
    direction_change(Pos) :- 
        position(Pos), Pos > 1, Pos < 8,
        down(Pos-1), up(Pos).
    
    % Show only melody atoms in output
    #show melody/2.
    #show interval/2.
    #show leap/1.
    #show direction_change/1.
    """

def solve_melody():
    ctl = clingo.Control(["1"])
    
    program = create_asp_program()
    ctl.add("base", [], program)
    ctl.ground([("base", [])])
    
    solution_data = None
    
    def on_model(model):
        nonlocal solution_data
        atoms = model.symbols(atoms=True)
        
        melody_atoms = [a for a in atoms if a.name == "melody"]
        melody_dict = {}
        for atom in melody_atoms:
            pos = atom.arguments[0].number
            note = str(atom.arguments[1])[1:-1]
            melody_dict[pos] = note
        
        interval_atoms = [a for a in atoms if a.name == "interval"]
        interval_dict = {}
        for atom in interval_atoms:
            pos = atom.arguments[0].number
            diff = atom.arguments[1].number
            interval_dict[pos] = diff
        
        leap_atoms = [a for a in atoms if a.name == "leap"]
        leap_positions = [a.arguments[0].number for a in leap_atoms]
        
        dir_change_atoms = [a for a in atoms if a.name == "direction_change"]
        dir_change_positions = [a.arguments[0].number for a in dir_change_atoms]
        
        solution_data = {
            'melody_dict': melody_dict,
            'interval_dict': interval_dict,
            'leap_count': len(leap_positions),
            'direction_changes': len(dir_change_positions)
        }
    
    result = ctl.solve(on_model=on_model)
    
    if result.satisfiable and solution_data:
        return solution_data
    else:
        return None

def format_output(solution_data):
    if not solution_data:
        return json.dumps({"error": "No solution exists"})
    
    melody = [solution_data['melody_dict'][i] for i in range(1, 9)]
    intervals = [solution_data['interval_dict'][i] for i in range(1, 8)]
    
    analysis = {
        "key": "C_major",
        "total_steps": 8,
        "leap_count": solution_data['leap_count'],
        "direction_changes": solution_data['direction_changes'],
        "final_resolution": melody[-1] == "C"
    }
    
    output = {
        "melody": melody,
        "intervals": intervals,
        "analysis": analysis
    }
    
    return output

solution = solve_melody()
output = format_output(solution)
print(json.dumps(output, indent=2))
