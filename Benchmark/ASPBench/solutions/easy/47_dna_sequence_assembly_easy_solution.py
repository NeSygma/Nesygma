import clingo
import json

fragments = [
    "ATCGATCG",
    "CGATCGTA",
    "ATCGTAAC",
    "CGTAACGG",
    "TAACGGCT",
    "ACGGCTGA",
    "GGCTGAAA",
    "CTGAAATC"
]

def find_overlap(frag1, frag2, min_overlap=3):
    """Find the maximum overlap when frag1 comes before frag2"""
    max_overlap = min(len(frag1), len(frag2))
    for overlap_len in range(max_overlap, min_overlap - 1, -1):
        if frag1[-overlap_len:] == frag2[:overlap_len]:
            return overlap_len, len(frag1) - overlap_len, 0
    return 0, -1, -1

overlaps = {}
for i in range(len(fragments)):
    for j in range(len(fragments)):
        if i != j:
            overlap_len, pos1, pos2 = find_overlap(fragments[i], fragments[j])
            if overlap_len >= 3:
                overlaps[(i, j)] = (overlap_len, pos1, pos2)

asp_program = """
fragment(0..7).
position(0..7).
"""

for (i, j), (overlap_len, _, _) in overlaps.items():
    asp_program += f'overlap({i}, {j}, {overlap_len}).\n'

asp_program += """
1 { at_position(F, P) : fragment(F) } 1 :- position(P).
1 { at_position(F, P) : position(P) } 1 :- fragment(F).

follows(F1, F2) :- at_position(F1, P), at_position(F2, P+1), position(P), P < 7.

:- follows(F1, F2), not overlap(F1, F2, _).

total_overlap(Total) :- Total = #sum { OL, F1, F2 : follows(F1, F2), overlap(F1, F2, OL) }.

:- total_overlap(Total), Total < 39.

#show at_position/2.
#show follows/2.
#show total_overlap/1.
"""

ctl = clingo.Control(["1"])
ctl.add("base", [], asp_program)
ctl.ground([("base", [])])

solution_data = None

def on_model(model):
    global solution_data
    atoms = model.symbols(atoms=True)
    
    positions = {}
    follows_pairs = []
    total_overlap_val = 0
    
    for atom in atoms:
        if atom.name == "at_position" and len(atom.arguments) == 2:
            frag = atom.arguments[0].number
            pos = atom.arguments[1].number
            positions[pos] = frag
        elif atom.name == "follows" and len(atom.arguments) == 2:
            f1 = atom.arguments[0].number
            f2 = atom.arguments[1].number
            follows_pairs.append((f1, f2))
        elif atom.name == "total_overlap" and len(atom.arguments) == 1:
            total_overlap_val = atom.arguments[0].number
    
    solution_data = {
        'positions': positions,
        'follows': follows_pairs,
        'total_overlap': total_overlap_val
    }

result = ctl.solve(on_model=on_model)

if result.satisfiable and solution_data:
    assembly_path = [solution_data['positions'][i] for i in range(8)]
    
    consensus = fragments[assembly_path[0]]
    overlap_details = []
    
    for i in range(len(assembly_path) - 1):
        frag1_idx = assembly_path[i]
        frag2_idx = assembly_path[i + 1]
        
        overlap_len, pos1, pos2 = overlaps[(frag1_idx, frag2_idx)]
        
        consensus += fragments[frag2_idx][overlap_len:]
        
        overlap_details.append({
            "fragment1": frag1_idx,
            "fragment2": frag2_idx,
            "overlap_length": overlap_len,
            "position1": pos1,
            "position2": pos2
        })
    
    output = {
        "fragments": fragments,
        "consensus_sequence": consensus,
        "assembly_path": assembly_path,
        "overlap_details": overlap_details
    }
    
    print(json.dumps(output, indent=2))
else:
    print(json.dumps({"error": "No solution exists", "reason": "Could not find valid assembly"}))
