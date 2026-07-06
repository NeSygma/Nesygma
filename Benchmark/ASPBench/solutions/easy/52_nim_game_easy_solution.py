import clingo
import json


def calculate_nim_sum(piles):
    """Calculate XOR of all pile values"""
    result = 0
    for pile in piles:
        result ^= pile
    return result


def solve_nim_game(piles):
    """Find all valid moves using ASP"""
    ctl = clingo.Control(["0"])
    
    program = """
    % Facts: Initial pile state
    """
    
    for idx, stones in enumerate(piles, 1):
        program += f'pile({idx}, {stones}).\n'
    
    program += """
    % Choice rule: select exactly one move (remove S stones from pile P)
    1 { move(P, S) : pile(P, N), S = 1..N } 1.
    
    % Calculate resulting piles after the move
    resulting_pile(P, N - S) :- move(P, S), pile(P, N).
    resulting_pile(P, N) :- pile(P, N), not move(P, _).
    
    #show move/2.
    #show resulting_pile/2.
    """
    
    ctl.add("base", [], program)
    ctl.ground([("base", [])])
    
    all_moves = []
    
    def on_model(model):
        move_atom = None
        resulting_piles_dict = {}
        
        for atom in model.symbols(atoms=True):
            if atom.name == "move" and len(atom.arguments) == 2:
                pile_idx = atom.arguments[0].number
                stones_removed = atom.arguments[1].number
                move_atom = (pile_idx, stones_removed)
            elif atom.name == "resulting_pile" and len(atom.arguments) == 2:
                pile_idx = atom.arguments[0].number
                stones = atom.arguments[1].number
                resulting_piles_dict[pile_idx] = stones
        
        if move_atom:
            resulting_piles = [resulting_piles_dict[i] 
                             for i in sorted(resulting_piles_dict.keys())]
            all_moves.append({
                "pile": move_atom[0],
                "stones_removed": move_atom[1],
                "resulting_piles": resulting_piles
            })
    
    ctl.solve(on_model=on_model)
    return all_moves


def find_optimal_moves(initial_piles):
    """Find all optimal moves that result in nim-sum = 0"""
    all_moves = solve_nim_game(initial_piles)
    
    optimal_moves = []
    for move in all_moves:
        resulting_nim_sum = calculate_nim_sum(move["resulting_piles"])
        if resulting_nim_sum == 0:
            optimal_moves.append({
                "pile": move["pile"],
                "stones": move["stones_removed"],
                "resulting_piles": move["resulting_piles"]
            })
    
    return optimal_moves


def main():
    initial_piles = [3, 4, 5]
    nim_sum = calculate_nim_sum(initial_piles)
    is_winning = nim_sum != 0
    
    optimal_moves = find_optimal_moves(initial_piles)
    
    solution = {
        "game_state": "winning" if is_winning else "losing",
        "optimal_moves": optimal_moves,
        "nim_sum": nim_sum,
        "analysis": {
            "is_winning_position": is_winning,
            "strategy": (
                "From a winning position (nim-sum ≠ 0), the optimal strategy "
                "is to make a move that reduces the nim-sum to 0, forcing the "
                "opponent into a losing position. "
                f"The current nim-sum is {nim_sum} (binary: {bin(nim_sum)}). "
                "To achieve nim-sum = 0, we need to remove stones from a pile "
                "such that the XOR of all remaining piles equals 0. This is "
                "done by removing 2 stones from pile 1, changing it from 3 to "
                "1, resulting in piles [1, 4, 5] with nim-sum = 1 ⊕ 4 ⊕ 5 = 0."
            ),
            "after_optimal_move": {
                "nim_sum": 0,
                "position": "losing"
            }
        }
    }
    
    print(json.dumps(solution, indent=2))


if __name__ == "__main__":
    main()
