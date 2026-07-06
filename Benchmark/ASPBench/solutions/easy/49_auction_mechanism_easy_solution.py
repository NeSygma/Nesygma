import clingo
import json

def solve_auction():
    ctl = clingo.Control(["1"])
    
    program = """
    bidder("A"). bidder("B"). bidder("C"). bidder("D").
    
    item("item1"). item("item2"). item("item3"). item("item4"). item("item5").
    
    bid(1, "A", 100).
    bid(2, "A", 50).
    bid(3, "B", 120).
    bid(4, "B", 80).
    bid(5, "C", 150).
    bid(6, "D", 40).
    
    bid_item(1, "item1"). bid_item(1, "item2").
    bid_item(2, "item3").
    bid_item(3, "item2"). bid_item(3, "item3").
    bid_item(4, "item4"). bid_item(4, "item5").
    bid_item(5, "item1"). bid_item(5, "item3"). bid_item(5, "item5").
    bid_item(6, "item4").
    
    { win(BidID) } :- bid(BidID, _, _).
    
    :- item(I), win(B1), win(B2), B1 != B2, bid_item(B1, I), bid_item(B2, I).
    
    total_revenue(R) :- R = #sum { Price, BidID : win(BidID), bid(BidID, _, Price) }.
    
    :- total_revenue(R), R < 230.
    
    #maximize { Price, BidID : win(BidID), bid(BidID, _, Price) }.
    """
    
    ctl.add("base", [], program)
    ctl.ground([("base", [])])
    
    solution = None
    
    def on_model(m):
        nonlocal solution
        atoms = m.symbols(atoms=True)
        
        winning_bids = []
        item_allocation = {}
        total_revenue = 0
        
        winning_bid_ids = set()
        for atom in atoms:
            if atom.name == "win" and len(atom.arguments) == 1:
                bid_id = atom.arguments[0].number
                winning_bid_ids.add(bid_id)
        
        bid_data = {
            1: ("A", ["item1", "item2"], 100),
            2: ("A", ["item3"], 50),
            3: ("B", ["item2", "item3"], 120),
            4: ("B", ["item4", "item5"], 80),
            5: ("C", ["item1", "item3", "item5"], 150),
            6: ("D", ["item4"], 40)
        }
        
        for bid_id in sorted(winning_bid_ids):
            bidder, items, price = bid_data[bid_id]
            winning_bids.append({
                "bidder": bidder,
                "items": items,
                "price": price
            })
            total_revenue += price
            
            for item in items:
                item_allocation[item] = bidder
        
        all_items = ["item1", "item2", "item3", "item4", "item5"]
        for item in all_items:
            if item not in item_allocation:
                item_allocation[item] = None
        
        solution = {
            "winning_bids": winning_bids,
            "total_revenue": total_revenue,
            "item_allocation": item_allocation
        }
    
    result = ctl.solve(on_model=on_model)
    
    if result.satisfiable and solution:
        return solution
    else:
        return {"error": "No solution exists", "reason": "Could not find allocation meeting constraints"}

solution = solve_auction()
print(json.dumps(solution, indent=2))
