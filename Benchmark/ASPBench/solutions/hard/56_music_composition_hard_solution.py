import clingo
import json

notes_data = [
    ("C", 0),
    ("D", 2),
    ("E", 4),
    ("F", 5),
    ("G", 7),
    ("A", 9),
    ("B", 11)
]

def midi_value(note_name, octave):
    """Calculate MIDI value for a note"""
    base_offset = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
    return 12 * (octave + 1) + base_offset[note_name]

soprano_notes = []
alto_notes = []

for octave in range(3, 6):
    for note_name, offset in notes_data:
        midi = midi_value(note_name, octave)
        note_str = f"{note_name}{octave}"
        
        if 60 <= midi <= 81:
            soprano_notes.append((note_str, midi))
        
        if 52 <= midi <= 72:
            alto_notes.append((note_str, midi))

program_parts = []

program_parts.append("time(1..8).")

for note_str, midi in soprano_notes:
    program_parts.append(f'soprano_note("{note_str}", {midi}).')

for note_str, midi in alto_notes:
    program_parts.append(f'alto_note("{note_str}", {midi}).')

note_names_set = set()
for note_str, _ in soprano_notes + alto_notes:
    note_name = ''.join([c for c in note_str if c.isalpha()])
    note_names_set.add((note_str, note_name))

for note_str, note_name in note_names_set:
    program_parts.append(f'note_name("{note_str}", "{note_name}").')

allowed_intervals = [3, 4, 7, 8, 9, 12, 15, 16]
for interval in allowed_intervals:
    program_parts.append(f'allowed_harmonic_interval({interval}).')

v_chord_notes = ["G", "B", "D"]
for note in v_chord_notes:
    program_parts.append(f'v_chord_note("{note}").')

program_parts.append('''
is_v_chord(Note) :- note_name(Note, Name), v_chord_note(Name).
''')

program_parts.append('''
1 { assign_soprano(T, Note) : soprano_note(Note, _) } 1 :- time(T).
1 { assign_alto(T, Note) : alto_note(Note, _) } 1 :- time(T).
''')

program_parts.append('''
:- assign_alto(1, Note), Note != "C4".
:- assign_soprano(1, Note), Note != "E4", Note != "G4".
''')

program_parts.append('''
:- assign_soprano(8, Note), Note != "C5".
:- assign_alto(8, Note), Note != "C4".
''')

program_parts.append('''
:- assign_soprano(7, Note), not is_v_chord(Note).
:- assign_alto(7, Note), not is_v_chord(Note).
''')

program_parts.append('''
:- assign_soprano(T, SNote), assign_alto(T, ANote),
   soprano_note(SNote, SMidi), alto_note(ANote, AMidi),
   SMidi <= AMidi.
''')

program_parts.append('''
:- assign_soprano(T, N1), assign_soprano(T+1, N2),
   soprano_note(N1, M1), soprano_note(N2, M2),
   time(T), time(T+1),
   |M1 - M2| > 7.

:- assign_alto(T, N1), assign_alto(T+1, N2),
   alto_note(N1, M1), alto_note(N2, M2),
   time(T), time(T+1),
   |M1 - M2| > 7.
''')

program_parts.append('''
:- assign_soprano(T, SNote), assign_alto(T, ANote),
   soprano_note(SNote, SMidi), alto_note(ANote, AMidi),
   not allowed_harmonic_interval(SMidi - AMidi).
''')

program_parts.append('''
harmonic_interval(T, Interval) :- 
    assign_soprano(T, SNote), assign_alto(T, ANote),
    soprano_note(SNote, SMidi), alto_note(ANote, AMidi),
    Interval = SMidi - AMidi.

:- harmonic_interval(T, 7), harmonic_interval(T+1, 7),
   time(T), time(T+1).

:- harmonic_interval(T, 12), harmonic_interval(T+1, 12),
   time(T), time(T+1).
''')

asp_program = "\n".join(program_parts)

ctl = clingo.Control(["1"])

ctl.add("base", [], asp_program)

ctl.ground([("base", [])])

solution_found = False
composition_data = {}

def on_model(model):
    global solution_found, composition_data
    solution_found = True
    
    soprano_assignments = {}
    alto_assignments = {}
    
    for atom in model.symbols(atoms=True):
        if atom.name == "assign_soprano" and len(atom.arguments) == 2:
            time_step = atom.arguments[0].number
            note = str(atom.arguments[1]).strip('"')
            soprano_assignments[time_step] = note
        elif atom.name == "assign_alto" and len(atom.arguments) == 2:
            time_step = atom.arguments[0].number
            note = str(atom.arguments[1]).strip('"')
            alto_assignments[time_step] = note
    
    composition_data = {
        "soprano": soprano_assignments,
        "alto": alto_assignments
    }

result = ctl.solve(on_model=on_model)

if result.satisfiable:
    midi_lookup = {}
    for note_str, midi in soprano_notes + alto_notes:
        midi_lookup[note_str] = midi
    
    composition = []
    for t in range(1, 9):
        soprano_note = composition_data['soprano'][t]
        alto_note = composition_data['alto'][t]
        
        soprano_midi = midi_lookup[soprano_note]
        alto_midi = midi_lookup[alto_note]
        harmonic_interval = soprano_midi - alto_midi
        
        composition.append({
            "time": t,
            "soprano_note": soprano_note,
            "alto_note": alto_note,
            "harmonic_interval_semitones": harmonic_interval
        })
    
    parallel_fifths = 0
    parallel_octaves = 0
    for i in range(len(composition) - 1):
        interval1 = composition[i]["harmonic_interval_semitones"]
        interval2 = composition[i+1]["harmonic_interval_semitones"]
        
        if interval1 == 7 and interval2 == 7:
            parallel_fifths += 1
        if interval1 == 12 and interval2 == 12:
            parallel_octaves += 1
    
    voice_crossings = 0
    for entry in composition:
        s_midi = midi_lookup[entry["soprano_note"]]
        a_midi = midi_lookup[entry["alto_note"]]
        if s_midi <= a_midi:
            voice_crossings += 1
    
    output = {
        "composition": composition,
        "analysis": {
            "key": "C_major",
            "num_steps": 8,
            "voices": ["soprano", "alto"],
            "parallel_fifths": parallel_fifths,
            "parallel_octaves": parallel_octaves,
            "voice_crossings": voice_crossings,
            "cadence": "authentic"
        }
    }
    
    print(json.dumps(output, indent=2))
else:
    print(json.dumps({"error": "No solution exists", "reason": "Constraints are unsatisfiable"}))
