import clingo
import json

fragments = {
    "F0": "ATGGGCGC",
    "F1": "GGCGCCAT",
    "F2": "GCCATT",
    "F3": "ATTTAA",
    "F4": "ATGCCTCG",
    "F5": "GCTCGAGG",
    "F6": "TCGAGCTG",
    "F7": "AGCTGA",
    "F8": "ATTCG"
}

def reverse_complement(seq):
    complement = {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G'}
    return ''.join(complement[base] for base in reversed(seq))

def gc_content(seq):
    gc_count = seq.count('G') + seq.count('C')
    return (gc_count / len(seq)) * 100

def find_overlap(seq1, seq2, min_overlap):
    max_possible = min(len(seq1), len(seq2))
    for overlap_len in range(max_possible, min_overlap - 1, -1):
        if seq1[-overlap_len:] == seq2[:overlap_len]:
            return overlap_len
    return 0

overlap_data = []
for f1_id, f1_seq in fragments.items():
    for f2_id, f2_seq in fragments.items():
        if f1_id == f2_id:
            continue
        for f1_orient, f1_actual in [("forward", f1_seq), ("reverse", reverse_complement(f1_seq))]:
            for f2_orient, f2_actual in [("forward", f2_seq), ("reverse", reverse_complement(f2_seq))]:
                gc1 = gc_content(f1_actual)
                gc2 = gc_content(f2_actual)
                min_overlap = 4 if (gc1 > 50 and gc2 > 50) else 3
                overlap_len = find_overlap(f1_actual, f2_actual, min_overlap)
                if overlap_len >= min_overlap:
                    overlap_data.append({
                        'f1': f1_id,
                        'f1_orient': f1_orient,
                        'f2': f2_id,
                        'f2_orient': f2_orient,
                        'overlap': overlap_len
                    })

start_fragments = []
for fid, seq in fragments.items():
    if seq.startswith("ATG"):
        start_fragments.append((fid, "forward"))
    rev_seq = reverse_complement(seq)
    if rev_seq.startswith("ATG"):
        start_fragments.append((fid, "reverse"))

stop_codons = ["TAA", "TAG", "TGA"]
end_fragments = []
for fid, seq in fragments.items():
    if any(seq.endswith(codon) for codon in stop_codons):
        end_fragments.append((fid, "forward"))
    rev_seq = reverse_complement(seq)
    if any(rev_seq.endswith(codon) for codon in stop_codons):
        end_fragments.append((fid, "reverse"))

asp_program = "% Fragment definitions\n"
for fid in fragments.keys():
    asp_program += f'fragment("{fid}").\n'

asp_program += "\n% Overlap facts\n"
for overlap in overlap_data:
    asp_program += f'can_follow("{overlap["f1"]}", "{overlap["f1_orient"]}", "{overlap["f2"]}", "{overlap["f2_orient"]}", {overlap["overlap"]}).\n'

asp_program += "\n% Start codon facts\n"
for fid, orient in start_fragments:
    asp_program += f'can_start("{fid}", "{orient}").\n'

asp_program += "\n% Stop codon facts\n"
for fid, orient in end_fragments:
    asp_program += f'can_end("{fid}", "{orient}").\n'

asp_program += """
orientation("forward"). orientation("reverse").
contig(1..9).

{ chimeric(F) } :- fragment(F).
1 { in_contig(F, C) : contig(C) ; chimeric(F) } 1 :- fragment(F).
1 { has_orientation(F, O) : orientation(O) } 1 :- in_contig(F, _).
1 { position(F, C, P) : P = 0..8 } 1 :- in_contig(F, C).

used_contig(C) :- in_contig(_, C).

:- position(F1, C, P), position(F2, C, P), F1 != F2.
:- used_contig(C), position(_, C, P), P > 0, not position(_, C, P-1).
:- used_contig(C), not position(_, C, 0).
:- position(F1, C, P), position(F2, C, P+1),
   has_orientation(F1, O1), has_orientation(F2, O2),
   not can_follow(F1, O1, F2, O2, _).
:- used_contig(C), position(F, C, 0), has_orientation(F, O), not can_start(F, O).

last_position(C, P) :- position(_, C, P), not position(_, C, P+1).
:- last_position(C, P), position(F, C, P), has_orientation(F, O), not can_end(F, O).

#minimize { 1,C : used_contig(C) }.
#minimize { 1,F : chimeric(F) }.

#show in_contig/2.
#show has_orientation/2.
#show position/3.
#show chimeric/1.
#show used_contig/1.
"""

ctl = clingo.Control(["0"])
ctl.add("base", [], asp_program)
ctl.ground([("base", [])])

solution_data = {
    'in_contig': [],
    'has_orientation': [],
    'position': [],
    'chimeric': [],
    'used_contig': []
}

def on_model(model):
    solution_data['in_contig'].clear()
    solution_data['has_orientation'].clear()
    solution_data['position'].clear()
    solution_data['chimeric'].clear()
    solution_data['used_contig'].clear()
    
    for atom in model.symbols(shown=True):
        if atom.name == "in_contig":
            frag = str(atom.arguments[0]).strip('"')
            contig = atom.arguments[1].number
            solution_data['in_contig'].append((frag, contig))
        elif atom.name == "has_orientation":
            frag = str(atom.arguments[0]).strip('"')
            orient = str(atom.arguments[1]).strip('"')
            solution_data['has_orientation'].append((frag, orient))
        elif atom.name == "position":
            frag = str(atom.arguments[0]).strip('"')
            contig = atom.arguments[1].number
            pos = atom.arguments[2].number
            solution_data['position'].append((frag, contig, pos))
        elif atom.name == "chimeric":
            frag = str(atom.arguments[0]).strip('"')
            solution_data['chimeric'].append(frag)
        elif atom.name == "used_contig":
            contig = atom.arguments[0].number
            solution_data['used_contig'].append(contig)

result = ctl.solve(on_model=on_model)

if not result.satisfiable:
    print(json.dumps({"error": "No solution exists"}))
else:
    def reconstruct_sequence(fragment_list, orientation_list):
        if not fragment_list:
            return ""
        fid = fragment_list[0]
        orient = orientation_list[0]
        full_sequence = fragments[fid] if orient == "forward" else reverse_complement(fragments[fid])
        
        for i in range(1, len(fragment_list)):
            fid = fragment_list[i]
            orient = orientation_list[i]
            next_seq = fragments[fid] if orient == "forward" else reverse_complement(fragments[fid])
            prev_fid = fragment_list[i-1]
            prev_orient = orientation_list[i-1]
            
            overlap_len = 0
            for overlap in overlap_data:
                if (overlap['f1'] == prev_fid and overlap['f1_orient'] == prev_orient and
                    overlap['f2'] == fid and overlap['f2_orient'] == orient):
                    overlap_len = overlap['overlap']
                    break
            full_sequence += next_seq[overlap_len:]
        return full_sequence
    
    contigs_data = {}
    for contig_id in sorted(solution_data['used_contig']):
        contig_fragments = [(f, c, p) for f, c, p in solution_data['position'] if c == contig_id]
        contig_fragments.sort(key=lambda x: x[2])
        fragment_ids = [f for f, c, p in contig_fragments]
        orientations = [next(o for frag, o in solution_data['has_orientation'] if frag == f) 
                        for f in fragment_ids]
        sequence = reconstruct_sequence(fragment_ids, orientations)
        contigs_data[contig_id] = {
            'fragments': fragment_ids,
            'orientations': orientations,
            'sequence': sequence
        }
    
    output = {
        "contigs": [],
        "excluded": {
            "chimeric": solution_data['chimeric']
        }
    }
    
    for idx, contig_id in enumerate(sorted(solution_data['used_contig']), 1):
        data = contigs_data[contig_id]
        output["contigs"].append({
            "contig_id": idx,
            "fragments": data['fragments'],
            "orientations": data['orientations'],
            "sequence": data['sequence']
        })
    
    print(json.dumps(output, indent=2))
