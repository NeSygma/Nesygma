import clingo
import json

asp_program = """
ego_strategy("COOP").
ego_strategy("DEFECT").
ego_strategy("TFT").

opp_strategy("type_A").
opp_strategy("type_B").
opp_strategy("type_C").

opp_count("type_A", 5).
opp_count("type_B", 3).
opp_count("type_C", 2).

round(1).
round(2).

move_type("C").
move_type("D").

payoff("C", "C", 3).
payoff("D", "C", 5).
payoff("C", "D", 0).
payoff("D", "D", 1).

ego_move("COOP", R, "C") :- round(R).

ego_move("DEFECT", R, "D") :- round(R).

ego_move("TFT", 1, "C").

opp_move("type_A", R, "D") :- round(R).

opp_move("type_B", 1, "C").

opp_move("type_C", R, "C") :- round(R).

matchup_ego_move(EgoStrat, OppStrat, 1, EgoMove) :- 
    ego_strategy(EgoStrat), 
    opp_strategy(OppStrat),
    ego_move(EgoStrat, 1, EgoMove).

matchup_opp_move(EgoStrat, OppStrat, 1, OppMove) :- 
    ego_strategy(EgoStrat), 
    opp_strategy(OppStrat),
    opp_move(OppStrat, 1, OppMove).

matchup_ego_move("TFT", OppStrat, 2, OppMove) :- 
    opp_strategy(OppStrat),
    matchup_opp_move("TFT", OppStrat, 1, OppMove).

matchup_ego_move(EgoStrat, OppStrat, 2, EgoMove) :- 
    ego_strategy(EgoStrat),
    EgoStrat != "TFT",
    opp_strategy(OppStrat),
    ego_move(EgoStrat, 2, EgoMove).

matchup_opp_move(EgoStrat, "type_B", 2, EgoMove) :- 
    ego_strategy(EgoStrat),
    matchup_ego_move(EgoStrat, "type_B", 1, EgoMove).

matchup_opp_move(EgoStrat, OppStrat, 2, OppMove) :- 
    ego_strategy(EgoStrat),
    opp_strategy(OppStrat),
    OppStrat != "type_B",
    opp_move(OppStrat, 2, OppMove).

round_score(EgoStrat, OppStrat, R, Points) :- 
    matchup_ego_move(EgoStrat, OppStrat, R, EgoMove),
    matchup_opp_move(EgoStrat, OppStrat, R, OppMove),
    payoff(EgoMove, OppMove, Points).

matchup_total(EgoStrat, OppStrat, Total) :- 
    ego_strategy(EgoStrat),
    opp_strategy(OppStrat),
    Total = #sum { Points, R : round_score(EgoStrat, OppStrat, R, Points) }.

expected_total(EgoStrat, ExpectedTotal) :- 
    ego_strategy(EgoStrat),
    ExpectedTotal = #sum { Total * Count, OppStrat : 
        matchup_total(EgoStrat, OppStrat, Total),
        opp_count(OppStrat, Count) }.

max_score(MaxScore) :- 
    MaxScore = #max { Score : expected_total(_, Score) }.

best_strategy(EgoStrat) :- 
    expected_total(EgoStrat, Score),
    max_score(Score).

#show expected_total/2.
#show best_strategy/1.
"""

ctl = clingo.Control(["1"])
ctl.add("base", [], asp_program)
ctl.ground([("base", [])])

solution_data = {
    'expected_totals': {},
    'best_strategies': []
}

def on_model(model):
    global solution_data
    for atom in model.symbols(atoms=True):
        if atom.name == "expected_total" and len(atom.arguments) == 2:
            strategy = str(atom.arguments[0]).strip('"')
            score = atom.arguments[1].number
            solution_data['expected_totals'][strategy] = score
        elif atom.name == "best_strategy" and len(atom.arguments) == 1:
            strategy = str(atom.arguments[0]).strip('"')
            solution_data['best_strategies'].append(strategy)

result = ctl.solve(on_model=on_model)

if result.satisfiable:
    output = {
        "best_strategy_choice": solution_data['best_strategies'][0],
        "expected_scores": [
            {
                "strategy": strategy,
                "expected_total_score": score
            }
            for strategy, score in sorted(solution_data['expected_totals'].items(), 
                                           key=lambda x: x[1], reverse=True)
        ]
    }
    print(json.dumps(output, indent=2))
else:
    print(json.dumps({"error": "No solution exists"}))
