import json
from functools import reduce
from operator import xor


def solve_quantum_nim():
    """
    Solve Quantum Nim to find all optimal moves for the current player.
    
    A move is optimal if it results in a nim-sum of 0, forcing the opponent
    into a losing position.
    """
    
    initial_piles = [6, 7, 10, 13]
    current_player = 1
    split_available = True
    
    initial_nim_sum = reduce(xor, initial_piles)
    is_winning = initial_nim_sum != 0
    
    optimal_moves = []
    
    for pile_idx, pile_size in enumerate(initial_piles):
        for stones_removed in range(1, pile_size + 1):
            new_piles = initial_piles.copy()
            new_size = pile_size - stones_removed
            
            if new_size == 0:
                new_piles.pop(pile_idx)
            else:
                new_piles[pile_idx] = new_size
            
            if len(new_piles) != len(set(new_piles)):
                continue
            
            if len(new_piles) == 0:
                nim_sum = 0
            else:
                nim_sum = reduce(xor, new_piles)
            
            if nim_sum == 0:
                optimal_moves.append({
                    "move_type": "standard",
                    "pile_index": pile_idx,
                    "stones_removed": stones_removed,
                    "resulting_piles": sorted(new_piles)
                })
    
    if current_player == 1 and split_available:
        for pile_idx, pile_size in enumerate(initial_piles):
            if pile_size % 2 != 0:
                continue
            
            for size1 in range(1, pile_size):
                size2 = pile_size - size1
                if size2 <= 0:
                    continue
                
                new_piles = initial_piles.copy()
                new_piles.pop(pile_idx)
                new_piles.extend([size1, size2])
                
                if len(new_piles) != len(set(new_piles)):
                    continue
                
                nim_sum = reduce(xor, new_piles)
                
                if nim_sum == 0:
                    optimal_moves.append({
                        "move_type": "power_split",
                        "pile_index": pile_idx,
                        "split_into": sorted([size1, size2]),
                        "resulting_piles": sorted(new_piles)
                    })
    
    standard_count = sum(1 for m in optimal_moves if m["move_type"] == "standard")
    power_count = sum(1 for m in optimal_moves if m["move_type"] == "power_split")
    
    analysis = f"A winning position. {standard_count} standard move(s) lead to a nim-sum of 0."
    if power_count == 0:
        analysis += " No optimal power moves are possible."
    else:
        analysis += f" {power_count} optimal power move(s) are possible."
    
    result = {
        "initial_nim_sum": initial_nim_sum,
        "is_winning_position": is_winning,
        "optimal_moves": optimal_moves,
        "analysis": analysis
    }
    
    return result


solution = solve_quantum_nim()
print(json.dumps(solution, indent=2))
