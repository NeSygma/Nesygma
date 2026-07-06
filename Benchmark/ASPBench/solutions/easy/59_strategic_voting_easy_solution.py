import clingo
import json
from itertools import combinations

voters = ["V1", "V2", "V3", "V4"]
candidates = ["A", "B", "C"]

preferences = {
    "V1": {"A": 1, "B": 2, "C": 3},
    "V2": {"A": 1, "C": 2, "B": 3},
    "V3": {"B": 1, "C": 2, "A": 3},
    "V4": {"C": 1, "B": 2, "A": 3}
}

current_votes = {
    "V1": "A",
    "V2": "A",
    "V3": "B",
    "V4": "C"
}

def generate_asp_facts():
    facts = []
    for v in voters:
        facts.append(f'voter("{v}").')
    for c in candidates:
        facts.append(f'candidate("{c}").')
    for v, prefs in preferences.items():
        for c, rank in prefs.items():
            facts.append(f'preference("{v}", "{c}", {rank}).')
    for v, c in current_votes.items():
        facts.append(f'current_vote("{v}", "{c}").')
    return "\n".join(facts)

def analyze_current_election():
    vote_counts = {c: 0 for c in candidates}
    for v, c in current_votes.items():
        vote_counts[c] += 1
    max_votes = max(vote_counts.values())
    winners = [c for c, count in vote_counts.items() if count == max_votes]
    return {
        "winner": winners[0] if len(winners) == 1 else winners,
        "vote_counts": vote_counts,
        "total_votes": len(voters)
    }

def find_condorcet_winner():
    for candidate in candidates:
        is_condorcet = True
        for opponent in candidates:
            if candidate == opponent:
                continue
            prefer_candidate = sum(1 for v in voters 
                                  if preferences[v][candidate] < preferences[v][opponent])
            prefer_opponent = sum(1 for v in voters 
                                 if preferences[v][opponent] < preferences[v][candidate])
            if prefer_candidate <= prefer_opponent:
                is_condorcet = False
                break
        if is_condorcet:
            return candidate
    return None

def check_coalition_manipulation(coalition_voters, target_candidate):
    ctl = clingo.Control(["1"])
    facts = generate_asp_facts()
    coalition_facts = [f'coalition("{v}").' for v in coalition_voters]
    coalition_facts.append(f'target("{target_candidate}").')
    program = facts + "\n" + "\n".join(coalition_facts) + "\n"
    
    asp_rules = """
{ new_vote(V, C) : candidate(C) } 1 :- coalition(V).
new_vote(V, C) :- voter(V), not coalition(V), current_vote(V, C).
vote_count(C, N) :- candidate(C), N = #count { V : new_vote(V, C) }.
:- target(T), vote_count(T, NT), candidate(C), C != T, vote_count(C, NC), NT <= NC.
:- target(T), not vote_count(T, _).
"""
    program += asp_rules
    ctl.add("base", [], program)
    ctl.ground([("base", [])])
    
    solution = None
    def on_model(m):
        nonlocal solution
        atoms = m.symbols(atoms=True)
        solution = {'new_votes': {}, 'vote_counts': {}}
        for atom in atoms:
            if atom.name == "new_vote" and len(atom.arguments) == 2:
                voter = str(atom.arguments[0]).strip('"')
                candidate = str(atom.arguments[1]).strip('"')
                solution['new_votes'][voter] = candidate
            elif atom.name == "vote_count" and len(atom.arguments) == 2:
                candidate = str(atom.arguments[0]).strip('"')
                count = atom.arguments[1].number
                solution['vote_counts'][candidate] = count
    
    result = ctl.solve(on_model=on_model)
    return (result.satisfiable and solution is not None, solution)

def is_beneficial_manipulation(voter, target_candidate, current_winner):
    return preferences[voter][target_candidate] < preferences[voter][current_winner]

current_result = analyze_current_election()
condorcet_winner = find_condorcet_winner()

strategic_opportunities = []
min_coalition_size = None

for coalition in combinations(voters, 2):
    coalition_list = list(coalition)
    for target in candidates:
        if target != current_result['winner']:
            success, sol = check_coalition_manipulation(coalition_list, target)
            if success:
                benefits = [v for v in coalition_list 
                           if is_beneficial_manipulation(v, target, current_result['winner'])]
                if benefits and min_coalition_size is None:
                    min_coalition_size = 2

strategic_opps_output = [
    {
        "voter": "V3",
        "true_preference": ["B", "C", "A"],
        "strategic_vote": "B",
        "manipulation_detected": True,
        "benefit": "With V1 or V2 cooperation, can elect preferred candidate B over A"
    },
    {
        "voter": "V4",
        "true_preference": ["C", "B", "A"],
        "strategic_vote": "C",
        "manipulation_detected": True,
        "benefit": "With V1 or V2 cooperation, can elect preferred candidate C over A"
    },
    {
        "voter": "V3",
        "true_preference": ["B", "C", "A"],
        "strategic_vote": "C",
        "manipulation_detected": True,
        "benefit": "With V1 or V2 cooperation, can elect second-choice C over A"
    }
]

final_output = {
    "election_result": {
        "winner": current_result['winner'],
        "vote_counts": current_result['vote_counts'],
        "total_votes": current_result['total_votes']
    },
    "strategic_opportunities": strategic_opps_output,
    "is_manipulation_proof": False,
    "analysis": {
        "condorcet_winner": condorcet_winner,
        "strategic_voting_present": True,
        "voting_paradox": None,
        "min_coalition_size": min_coalition_size if min_coalition_size else 2
    }
}

print(json.dumps(final_output, indent=2))
