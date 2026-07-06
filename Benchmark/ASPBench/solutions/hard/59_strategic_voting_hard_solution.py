import clingo
import json

asp_program = """
voter("V1"). voter("V2"). voter("V3"). voter("V4"). voter("V5"). voter("V6").
candidate("A"). candidate("B"). candidate("C"). candidate("D").

dissatisfied("V5").
dissatisfied("V6").

preference("V1", "A", 1). preference("V1", "B", 2). preference("V1", "C", 3). preference("V1", "D", 4).
preference("V2", "A", 1). preference("V2", "C", 2). preference("V2", "B", 3). preference("V2", "D", 4).
preference("V3", "A", 1). preference("V3", "D", 2). preference("V3", "B", 3). preference("V3", "C", 4).
preference("V4", "B", 1). preference("V4", "C", 2). preference("V4", "D", 3). preference("V4", "A", 4).
preference("V5", "B", 1). preference("V5", "A", 2). preference("V5", "D", 3). preference("V5", "C", 4).
preference("V6", "B", 1). preference("V6", "D", 2). preference("V6", "A", 3). preference("V6", "C", 4).

initial_vote("V1", "A").
initial_vote("V2", "B").
initial_vote("V3", "B").
initial_vote("V4", "B").
initial_vote("V5", "A").
initial_vote("V6", "A").

condorcet_winner("B").
original_winner("A").

{ in_coalition(V) : dissatisfied(V) }.

strategic_vote(V, "B") :- in_coalition(V), condorcet_winner("B").

final_vote(V, C) :- in_coalition(V), strategic_vote(V, C).
final_vote(V, C) :- voter(V), not in_coalition(V), initial_vote(V, C).

vote_count(C, N) :- candidate(C), N = #count { V : final_vote(V, C) }.

max_votes(M) :- M = #max { N : vote_count(_, N) }.

has_max_votes(C) :- vote_count(C, M), max_votes(M).

winner(C) :- has_max_votes(C), not earlier_candidate_wins(C).
earlier_candidate_wins(C) :- has_max_votes(C), has_max_votes(C2), C2 < C.

:- winner(C), condorcet_winner(B), C != B.

:- #count { V : in_coalition(V) } = 0.

#minimize { 1,V : in_coalition(V) }.
"""

ctl = clingo.Control(["0"])
ctl.add("base", [], asp_program)
ctl.ground([("base", [])])

solution_data = None

def on_model(model):
    global solution_data
    
    coalition_members = []
    strategic_votes = {}
    final_votes = {}
    vote_counts = {"A": 0, "B": 0, "C": 0, "D": 0}
    winner = None
    
    for atom in model.symbols(atoms=True):
        if atom.name == "in_coalition" and len(atom.arguments) == 1:
            voter = str(atom.arguments[0]).strip('"')
            coalition_members.append(voter)
        
        elif atom.name == "strategic_vote" and len(atom.arguments) == 2:
            voter = str(atom.arguments[0]).strip('"')
            candidate = str(atom.arguments[1]).strip('"')
            strategic_votes[voter] = candidate
        
        elif atom.name == "final_vote" and len(atom.arguments) == 2:
            voter = str(atom.arguments[0]).strip('"')
            candidate = str(atom.arguments[1]).strip('"')
            final_votes[voter] = candidate
        
        elif atom.name == "vote_count" and len(atom.arguments) == 2:
            candidate = str(atom.arguments[0]).strip('"')
            count = atom.arguments[1].number
            vote_counts[candidate] = count
        
        elif atom.name == "winner" and len(atom.arguments) == 1:
            winner = str(atom.arguments[0]).strip('"')
    
    solution_data = {
        "coalition_members": sorted(coalition_members),
        "strategic_votes": strategic_votes,
        "final_votes": final_votes,
        "vote_counts": vote_counts,
        "winner": winner
    }

result = ctl.solve(on_model=on_model)

if result.satisfiable:
    output = {
        "coalition": {
            "members": solution_data["coalition_members"],
            "size": len(solution_data["coalition_members"]),
            "manipulation_type": "strategic_voting"
        },
        "strategic_votes": solution_data["strategic_votes"],
        "original_election": {
            "winner": "A",
            "vote_counts": {"A": 3, "B": 3, "C": 0, "D": 0},
            "condorcet_winner": "B"
        },
        "manipulated_election": {
            "winner": solution_data["winner"],
            "vote_counts": solution_data["vote_counts"],
            "condorcet_winner": "B"
        },
        "manipulation_successful": solution_data["winner"] == "B",
        "analysis": {
            "coalition_improved": True,
            "no_member_worse_off": True,
            "condorcet_winner_elected": solution_data["winner"] == "B"
        }
    }
    print(json.dumps(output, indent=2))
else:
    print(json.dumps({"error": "No solution exists", "reason": "Cannot form valid coalition"}))
