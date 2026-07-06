import clingo
import json

items_data = [
    (1, 9, "electronics", "fragile", "high"),
    (2, 8, "electronics", "sturdy", "high"),
    (3, 3, "electronics", "sturdy", "high"),
    (4, 9, "liquid", "fragile", "high"),
    (5, 7, "liquid", "sturdy", "high"),
    (6, 4, "liquid", "sturdy", "high"),
    (7, 10, "electronics", "fragile", "high"),
    (8, 10, "standard", "sturdy", "high"),
    (9, 10, "liquid", "fragile", "high"),
    (10, 10, "standard", "sturdy", "high"),
    (11, 8, "standard", "sturdy", "high"),
    (12, 7, "standard", "sturdy", "high"),
    (13, 5, "standard", "sturdy", "low"),
    (14, 8, "standard", "fragile", "low"),
    (15, 6, "standard", "fragile", "low"),
    (16, 6, "standard", "sturdy", "low"),
    (17, 8, "standard", "fragile", "low"),
    (18, 6, "standard", "fragile", "low"),
    (19, 6, "standard", "sturdy", "low"),
    (20, 7, "standard", "sturdy", "low"),
    (21, 7, "standard", "sturdy", "low"),
    (22, 6, "standard", "sturdy", "low"),
    (23, 7, "standard", "sturdy", "low"),
    (24, 5, "standard", "fragile", "low"),
    (25, 5, "standard", "fragile", "low"),
    (26, 3, "standard", "sturdy", "low"),
    (27, 5, "standard", "sturdy", "low"),
]

def generate_asp_facts(items_data):
    facts = []
    for item_id, size, category, fragility, priority in items_data:
        facts.append(f'item({item_id}).')
        facts.append(f'size({item_id}, {size}).')
        facts.append(f'category({item_id}, "{category}").')
        facts.append(f'fragility({item_id}, "{fragility}").')
        facts.append(f'priority({item_id}, "{priority}").')
    max_bins = 20
    facts.append(f'bin(1..{max_bins}).')
    for b in range(1, 7):
        facts.append(f'priority_bin({b}).')
    facts.append('bin_capacity(20).')
    facts.append('fragile_limit(2).')
    return " ".join(facts)

asp_program = """
1 { assigned(I, B) : bin(B) } 1 :- item(I).

:- bin(B), bin_capacity(Cap), 
   #sum { S,I : assigned(I,B), size(I,S) } > Cap.

:- assigned(I1, B), assigned(I2, B), 
   category(I1, "electronics"), category(I2, "liquid").

:- bin(B), fragile_limit(Limit),
   #count { I : assigned(I,B), fragility(I,"fragile") } > Limit.

:- assigned(I, B), priority(I, "high"), not priority_bin(B).

used_bin(B) :- assigned(_, B).
#minimize { 1,B : used_bin(B) }.
"""

def solve_bin_packing():
    ctl = clingo.Control(["1"])
    full_program = generate_asp_facts(items_data) + " " + asp_program
    ctl.add("base", [], full_program)
    ctl.ground([("base", [])])
    solution_data = None
    
    def on_model(model):
        nonlocal solution_data
        atoms = model.symbols(atoms=True)
        assignments = {}
        for atom in atoms:
            if atom.name == "assigned" and len(atom.arguments) == 2:
                item_id = atom.arguments[0].number
                bin_id = atom.arguments[1].number
                if bin_id not in assignments:
                    assignments[bin_id] = []
                assignments[bin_id].append(item_id)
        solution_data = assignments
    
    result = ctl.solve(on_model=on_model)
    return result.satisfiable, solution_data

def format_solution(assignments, items_data):
    if not assignments:
        return {
            "error": "No solution exists",
            "reason": "Unable to satisfy all constraints"
        }
    item_dict = {}
    for item_id, size, category, fragility, priority in items_data:
        item_dict[item_id] = {
            "item_id": item_id,
            "size": size,
            "category": category,
            "fragility": fragility,
            "priority": priority
        }
    bins = []
    total_priority_utilization = 0
    for bin_id in sorted(assignments.keys()):
        item_ids = assignments[bin_id]
        bin_items = []
        total_size = 0
        fragile_count = 0
        has_high_priority = False
        for item_id in sorted(item_ids):
            item = item_dict[item_id]
            bin_items.append(item)
            total_size += item["size"]
            if item["fragility"] == "fragile":
                fragile_count += 1
            if item["priority"] == "high":
                has_high_priority = True
        if has_high_priority:
            total_priority_utilization += total_size
        bins.append({
            "bin_id": bin_id,
            "items": bin_items,
            "total_size": total_size,
            "fragile_count": fragile_count,
            "is_priority_bin": has_high_priority
        })
    return {
        "feasible": True,
        "optimal": False,
        "num_bins": len(bins),
        "total_priority_utilization": total_priority_utilization,
        "bins": bins
    }

is_satisfiable, assignments = solve_bin_packing()
solution_json = format_solution(assignments, items_data)
print(json.dumps(solution_json, indent=2))
