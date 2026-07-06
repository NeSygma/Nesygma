import clingo
import json

def generate_asp_facts():
    facts = []
    
    for i in range(1, 41):
        facts.append(f'resident("r{i}").')
    
    capacities = {
        'h1': 2, 'h2': 2, 'h3': 2, 'h4': 2, 'h5': 2, 'h6': 2,
        'h7': 4, 'h8': 3, 'h9': 1,
        'h10': 3, 'h11': 3, 'h12': 2,
        'h13': 3, 'h14': 3, 'h15': 2,
        'h16': 2, 'h17': 2,
        'h18': 1, 'h19': 1, 'h20': 1
    }
    
    for h, cap in capacities.items():
        facts.append(f'hospital("{h}").')
        facts.append(f'capacity("{h}", {cap}).')
    
    res_prefs = {
        'r1': ['h1', 'h2'], 'r2': ['h1', 'h2'], 'r3': ['h2', 'h1'], 'r4': ['h2', 'h1'],
        'r5': ['h3', 'h4'], 'r6': ['h3', 'h4'], 'r7': ['h4', 'h3'], 'r8': ['h4', 'h3'],
        'r9': ['h5', 'h6'], 'r10': ['h5', 'h6'], 'r11': ['h6', 'h5'], 'r12': ['h6', 'h5'],
        'r13': ['h7', 'h8', 'h9'], 'r14': ['h7', 'h8', 'h9'], 'r15': ['h8', 'h7', 'h9'],
        'r16': ['h8', 'h7', 'h9'], 'r17': ['h7', 'h8', 'h9'], 'r18': ['h7', 'h9', 'h8'],
        'r19': ['h8', 'h9', 'h7'], 'r20': ['h9', 'h8', 'h7'],
        'r21': ['h10', 'h11', 'h12'], 'r22': ['h10', 'h12', 'h11'], 'r23': ['h11', 'h10', 'h12'],
        'r24': ['h11', 'h12', 'h10'], 'r25': ['h10', 'h11', 'h12'], 'r26': ['h11', 'h10', 'h12'],
        'r27': ['h12', 'h11', 'h10'], 'r28': ['h12', 'h10', 'h11'],
        'r29': ['h13', 'h14', 'h15'], 'r30': ['h13', 'h15', 'h14'], 'r31': ['h14', 'h13', 'h15'],
        'r32': ['h14', 'h15', 'h13'], 'r33': ['h13', 'h14', 'h15'], 'r34': ['h14', 'h13', 'h15'],
        'r35': ['h15', 'h14', 'h13'], 'r36': ['h15', 'h13', 'h14'],
        'r37': ['h16', 'h17'], 'r38': ['h16', 'h17'], 'r39': ['h17', 'h16'], 'r40': ['h17', 'h16'],
    }
    
    for r, prefs in res_prefs.items():
        for rank, h in enumerate(prefs, 1):
            facts.append(f'res_pref("{r}", "{h}", {rank}).')
    
    hosp_prefs = {
        'h1': ['r3', 'r4', 'r1', 'r2'], 'h2': ['r1', 'r2', 'r3', 'r4'],
        'h3': ['r7', 'r8', 'r5', 'r6'], 'h4': ['r5', 'r6', 'r7', 'r8'],
        'h5': ['r11', 'r12', 'r9', 'r10'], 'h6': ['r9', 'r10', 'r11', 'r12'],
        'h7': ['r13', 'r14', 'r17', 'r18', 'r15', 'r16', 'r19', 'r20'],
        'h8': ['r15', 'r16', 'r19', 'r13', 'r14', 'r17', 'r18', 'r20'],
        'h9': ['r20', 'r19', 'r18', 'r17', 'r16', 'r15', 'r14', 'r13'],
        'h10': ['r21', 'r22', 'r25', 'r23', 'r24', 'r26', 'r27', 'r28'],
        'h11': ['r23', 'r24', 'r26', 'r21', 'r22', 'r25', 'r27', 'r28'],
        'h12': ['r27', 'r28', 'r23', 'r24', 'r21', 'r22', 'r25', 'r26'],
        'h13': ['r29', 'r30', 'r33', 'r31', 'r32', 'r34', 'r35', 'r36'],
        'h14': ['r31', 'r32', 'r34', 'r29', 'r30', 'r33', 'r35', 'r36'],
        'h15': ['r35', 'r36', 'r31', 'r32', 'r29', 'r30', 'r33', 'r34'],
        'h16': ['r39', 'r40', 'r37', 'r38'], 'h17': ['r37', 'r38', 'r39', 'r40'],
    }
    
    for h, prefs in hosp_prefs.items():
        for rank, r in enumerate(prefs, 1):
            facts.append(f'hosp_pref("{h}", "{r}", {rank}).')
    
    return '\n'.join(facts)

def solve_stable_matching():
    facts = generate_asp_facts()
    
    asp_program = facts + """

{ matched(R, H) : res_pref(R, H, _), hosp_pref(H, R, _) } 1 :- resident(R).

:- hospital(H), capacity(H, Cap), #count { R : matched(R, H) } > Cap.

prefers_over_current(R, H) :- 
    resident(R), 
    res_pref(R, H, RankH),
    matched(R, H_current),
    res_pref(R, H_current, RankCurrent),
    RankH < RankCurrent.

prefers_over_current(R, H) :- 
    resident(R),
    res_pref(R, H, _),
    not matched(R, _).

has_capacity(H) :- 
    hospital(H),
    capacity(H, Cap),
    #count { R : matched(R, H) } < Cap.

prefers_over_assignee(H, R) :-
    hospital(H),
    hosp_pref(H, R, RankR),
    matched(R_current, H),
    hosp_pref(H, R_current, RankCurrent),
    RankR < RankCurrent.

would_accept(H, R) :- has_capacity(H), hosp_pref(H, R, _).
would_accept(H, R) :- prefers_over_assignee(H, R).

:- prefers_over_current(R, H), would_accept(H, R), not matched(R, H).

#show matched/2.
"""
    
    ctl = clingo.Control(["0"])
    ctl.add("base", [], asp_program)
    ctl.ground([("base", [])])
    
    all_matchings = []
    
    def on_model(model):
        matching = []
        for atom in model.symbols(atoms=True):
            if atom.name == "matched" and len(atom.arguments) == 2:
                resident = str(atom.arguments[0]).strip('"')
                hospital = str(atom.arguments[1]).strip('"')
                matching.append([resident, hospital])
        matching.sort()
        all_matchings.append(matching)
    
    result = ctl.solve(on_model=on_model)
    
    if result.satisfiable:
        return all_matchings
    else:
        return None

matchings = solve_stable_matching()

if matchings is not None:
    output = {
        "stable_matchings": matchings,
        "count": len(matchings)
    }
    print(json.dumps(output, indent=2))
else:
    print(json.dumps({"error": "No solution exists"}))
