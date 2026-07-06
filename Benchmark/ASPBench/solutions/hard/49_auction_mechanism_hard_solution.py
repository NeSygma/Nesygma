import clingo
import json

bidders_data = [
    {"bidder": "a", "budget": 150, "synergy_bonus": 20},
    {"bidder": "b", "budget": 200, "synergy_bonus": 10},
    {"bidder": "c", "budget": 180, "synergy_bonus": 25},
    {"bidder": "d", "budget": 100, "synergy_bonus": 5}
]

items_data = [
    {"item": "item1", "category": "electronics"},
    {"item": "item2", "category": "electronics"},
    {"item": "item3", "category": "furniture"},
    {"item": "item4", "category": "furniture"},
    {"item": "item5", "category": "electronics"},
    {"item": "item6", "category": "furniture"},
    {"item": "lic_E", "category": "license_electronics"},
    {"item": "lic_F", "category": "license_furniture"}
]

bids_data = [
    {"id": 1, "bidder": "a", "items": ["item1", "item2"], "price": 70},
    {"id": 2, "bidder": "a", "items": ["lic_E"], "price": 40},
    {"id": 3, "bidder": "b", "items": ["item3", "item4"], "price": 90},
    {"id": 4, "bidder": "b", "items": ["lic_F"], "price": 50},
    {"id": 5, "bidder": "b", "items": ["item5"], "price": 60},
    {"id": 6, "bidder": "c", "items": ["item1", "item5"], "price": 100},
    {"id": 7, "bidder": "c", "items": ["lic_E"], "price": 60},
    {"id": 8, "bidder": "c", "items": ["item3", "item6"], "price": 80},
    {"id": 9, "bidder": "d", "items": ["lic_F"], "price": 25},
    {"id": 10, "bidder": "d", "items": ["item4"], "price": 70}
]

def generate_asp_program():
    facts = []
    
    for b in bidders_data:
        facts.append(f'bidder("{b["bidder"]}", {b["budget"]}, {b["synergy_bonus"]}).')
    
    for i in items_data:
        facts.append(f'item("{i["item"]}", "{i["category"]}").')
    
    for bid in bids_data:
        facts.append(f'bid({bid["id"]}, "{bid["bidder"]}", {bid["price"]}).')
        for item in bid["items"]:
            facts.append(f'bid_contains({bid["id"]}, "{item}").')
    
    program = "\n".join(facts) + """

{ win(BidID) } :- bid(BidID, _, _).

:- win(B1), win(B2), B1 != B2, bid_contains(B1, Item), bid_contains(B2, Item).

bidder_total_cost(Bidder, Total) :- 
    bidder(Bidder, _, _),
    Total = #sum { Price, BidID : win(BidID), bid(BidID, Bidder, Price) }.

:- bidder_total_cost(Bidder, Total), bidder(Bidder, Budget, _), Total > Budget.

gets_synergy(Bidder) :- bidder(Bidder, _, _), 
    #count { BidID : win(BidID), bid(BidID, Bidder, _) } >= 2.

wins_electronics(Bidder) :- win(BidID), bid(BidID, Bidder, _), 
    bid_contains(BidID, Item), item(Item, "electronics").

:- wins_electronics(Bidder), not wins_license_electronics(Bidder).

wins_license_electronics(Bidder) :- win(BidID), bid(BidID, Bidder, _),
    bid_contains(BidID, "lic_E").

wins_furniture(Bidder) :- win(BidID), bid(BidID, Bidder, _),
    bid_contains(BidID, Item), item(Item, "furniture").

:- wins_furniture(Bidder), not wins_license_furniture(Bidder).

wins_license_furniture(Bidder) :- win(BidID), bid(BidID, Bidder, _),
    bid_contains(BidID, "lic_F").

bidder_item_count(Bidder, Count) :-
    bidder(Bidder, _, _),
    Count = #count { Item : win(BidID), bid(BidID, Bidder, _), bid_contains(BidID, Item) }.

:- bidder_item_count(Bidder, Count), Count > 3.

bid_revenue(R) :- R = #sum { Price, BidID : win(BidID), bid(BidID, _, Price) }.
synergy_revenue(S) :- S = #sum { Bonus, Bidder : gets_synergy(Bidder), bidder(Bidder, _, Bonus) }.

total_revenue(Revenue) :- bid_revenue(BR), synergy_revenue(SR), Revenue = BR + SR.

#maximize { Revenue : total_revenue(Revenue) }.

#show win/1.
#show total_revenue/1.
#show gets_synergy/1.
"""
    
    return program

def build_solution_json(solution_data):
    synergy_bonuses = []
    for bidder_name in solution_data['synergy_bidders']:
        for b in bidders_data:
            if b['bidder'] == bidder_name:
                synergy_bonuses.append({
                    "bidder": bidder_name,
                    "bonus": b['synergy_bonus']
                })
                break
    
    item_allocation = {}
    for bid_id in solution_data['winning_bids']:
        for bid in bids_data:
            if bid['id'] == bid_id:
                bidder = bid['bidder']
                for item in bid['items']:
                    item_allocation[item] = bidder
                break
    
    output = {
        "bidders": bidders_data,
        "items": items_data,
        "bids": bids_data,
        "winning_bids": solution_data['winning_bids'],
        "total_revenue": solution_data['total_revenue'],
        "synergy_bonuses": synergy_bonuses,
        "item_allocation": item_allocation
    }
    
    return output

asp_program = generate_asp_program()

ctl = clingo.Control(["0"])
ctl.add("base", [], asp_program)
ctl.ground([("base", [])])

solution_data = None
best_revenue = -1

def on_model(model):
    global solution_data, best_revenue
    
    winning_bids = []
    total_rev = 0
    synergy_bidders = []
    
    for atom in model.symbols(atoms=True):
        if atom.name == "win" and len(atom.arguments) == 1:
            bid_id = atom.arguments[0].number
            winning_bids.append(bid_id)
        elif atom.name == "total_revenue" and len(atom.arguments) == 1:
            total_rev = atom.arguments[0].number
        elif atom.name == "gets_synergy" and len(atom.arguments) == 1:
            bidder = str(atom.arguments[0])[1:-1]
            synergy_bidders.append(bidder)
    
    if total_rev > best_revenue:
        best_revenue = total_rev
        solution_data = {
            "winning_bids": sorted(winning_bids),
            "total_revenue": total_rev,
            "synergy_bidders": synergy_bidders
        }

result = ctl.solve(on_model=on_model)

if result.satisfiable:
    final_solution = build_solution_json(solution_data)
    print(json.dumps(final_solution, indent=2))
else:
    print(json.dumps({"error": "No solution exists", "reason": "UNSAT"}))
