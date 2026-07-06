import random
import json


class Strategy:
    def __init__(self, name):
        self.name = name
        self.reset()
    
    def reset(self):
        self.history = []
        self.opponent_history = []
    
    def play(self):
        raise NotImplementedError
    
    def update(self, my_move, opponent_move):
        self.history.append(my_move)
        self.opponent_history.append(opponent_move)


class COOP(Strategy):
    def play(self):
        return 'C'


class DEFECT(Strategy):
    def play(self):
        return 'D'


class TFT(Strategy):
    def play(self):
        if len(self.opponent_history) == 0:
            return 'C'
        return self.opponent_history[-1]


class GTFT(Strategy):
    def play(self):
        if len(self.opponent_history) == 0:
            return 'C'
        last_opponent_move = self.opponent_history[-1]
        if last_opponent_move == 'D':
            if random.random() < 0.1:
                return 'C'
        return last_opponent_move


class RAND(Strategy):
    def play(self):
        return 'C' if random.random() < 0.5 else 'D'


def get_payoff(move1, move2):
    if move1 == 'C' and move2 == 'C':
        return 3
    elif move1 == 'D' and move2 == 'D':
        return 1
    elif move1 == 'D' and move2 == 'C':
        return 5
    else:
        return 0


def play_match(strategy1, strategy2, rounds=100):
    strategy1.reset()
    strategy2.reset()
    
    score1 = 0
    score2 = 0
    
    for _ in range(rounds):
        move1 = strategy1.play()
        move2 = strategy2.play()
        
        score1 += get_payoff(move1, move2)
        score2 += get_payoff(move2, move1)
        
        strategy1.update(move1, move2)
        strategy2.update(move2, move1)
    
    return score1, score2


def run_tournament(seed=69):
    random.seed(seed)
    
    strategies = [
        COOP("COOP"),
        DEFECT("DEFECT"),
        TFT("TFT"),
        GTFT("GTFT"),
        RAND("RAND")
    ]
    
    total_scores = {s.name: 0 for s in strategies}
    
    for i, strat1 in enumerate(strategies):
        for j, strat2 in enumerate(strategies):
            score1, score2 = play_match(strat1, strat2, 100)
            total_scores[strat1.name] += score1
    
    sorted_results = sorted(total_scores.items(), 
                           key=lambda x: x[1], reverse=True)
    
    result = {
        "tournament_results": [
            {"strategy": name, "total_score": score}
            for name, score in sorted_results
        ],
        "winner": sorted_results[0][0]
    }
    
    return result


if __name__ == "__main__":
    result = run_tournament()
    print(json.dumps(result, indent=2))
