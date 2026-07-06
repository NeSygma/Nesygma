import clingo
import json


def solve_bin_packing():
    ctl = clingo.Control(["1"])
    
    items = {
        1: 4, 2: 6, 3: 2, 4: 3, 5: 7,
        6: 1, 7: 5, 8: 2, 9: 4
    }
    
    program = """
    item(1, 4). item(2, 6). item(3, 2). item(4, 3). item(5, 7).
    item(6, 1). item(7, 5). item(8, 2). item(9, 4).
    
    capacity(10).
    bin(1..9).
    
    1 { assigned(I, B) : bin(B) } 1 :- item(I, _).
    
    used(B) :- assigned(_, B).
    
    :- bin(B), capacity(Cap), 
       #sum { Size,I : assigned(I, B), item(I, Size) } > Cap.
    
    :- #count { B : used(B) } > 4.
    
    #show assigned/2.
    #show used/1.
    """
    
    ctl.add("base", [], program)
    ctl.ground([("base", [])])
    
    solution_data = None
    
    def on_model(model):
        nonlocal solution_data
        atoms = model.symbols(atoms=True)
        
        assignments = {}
        used_bins = set()
        
        for atom in atoms:
            if atom.name == "assigned" and len(atom.arguments) == 2:
                item_id = atom.arguments[0].number
                bin_id = atom.arguments[1].number
                if bin_id not in assignments:
                    assignments[bin_id] = []
                assignments[bin_id].append(item_id)
                used_bins.add(bin_id)
            elif atom.name == "used" and len(atom.arguments) == 1:
                used_bins.add(atom.arguments[0].number)
        
        solution_data = {
            "assignments": assignments,
            "used_bins": sorted(used_bins),
            "items": items
        }
    
    result = ctl.solve(on_model=on_model)
    
    if result.satisfiable and solution_data:
        bins_output = []
        bin_counter = 1
        
        for bin_id in solution_data["used_bins"]:
            if bin_id in solution_data["assignments"]:
                item_list = sorted(solution_data["assignments"][bin_id])
                total_size = sum(items[item_id] for item_id in item_list)
                bins_output.append({
                    "bin_id": bin_counter,
                    "items": item_list,
                    "total_size": total_size
                })
                bin_counter += 1
        
        output = {
            "bins": bins_output,
            "num_bins": len(bins_output),
            "feasible": True
        }
        
        return output
    else:
        return {
            "bins": [],
            "num_bins": 0,
            "feasible": False,
            "error": "No solution found"
        }


if __name__ == "__main__":
    result = solve_bin_packing()
    print(json.dumps(result, indent=2))
