import clingo
import json

def create_asp_program():
    program = """
suite(1..8).

nationality(american; brazilian; canadian; dutch; egyptian; french; german; hungarian).
profession(architect; biologist; chemist; doctor; engineer; lawyer; musician; pilot).
car_brand(audi; bmw; ford; honda; mercedes; nissan; toyota; volvo).
beverage(coffee; juice; milk; soda; tea; water; wine; whiskey).
music_genre(blues; classical; folk; jazz; pop; rap; reggae; rock).
pet_type(cat; dog; fish; hamster; lizard; parrot; rabbit; snake).
vacation_dest(bali; dubai; london; newyork; paris; rome; sydney; tokyo).

1 { has_nationality(S, N) : nationality(N) } 1 :- suite(S).
1 { has_profession(S, P) : profession(P) } 1 :- suite(S).
1 { has_car(S, C) : car_brand(C) } 1 :- suite(S).
1 { has_drink(S, D) : beverage(D) } 1 :- suite(S).
1 { has_music(S, M) : music_genre(M) } 1 :- suite(S).
1 { has_pet(S, P) : pet_type(P) } 1 :- suite(S).
1 { has_destination(S, D) : vacation_dest(D) } 1 :- suite(S).

1 { has_nationality(S, N) : suite(S) } 1 :- nationality(N).
1 { has_profession(S, P) : suite(S) } 1 :- profession(P).
1 { has_car(S, C) : suite(S) } 1 :- car_brand(C).
1 { has_drink(S, D) : suite(S) } 1 :- beverage(D).
1 { has_music(S, M) : suite(S) } 1 :- music_genre(M).
1 { has_pet(S, P) : suite(S) } 1 :- pet_type(P).
1 { has_destination(S, D) : suite(S) } 1 :- vacation_dest(D).

:- not has_drink(4, milk).
:- not has_nationality(4, hungarian).
:- has_nationality(S1, american), has_profession(S2, lawyer), S1 != S2.
:- has_car(S1, bmw), has_profession(S2, biologist), S1 != S2.
:- has_nationality(S1, canadian), has_pet(S2, snake), S1 != S2.
:- has_music(S1, classical), has_car(S2, audi), S1 != S2.
:- has_nationality(S1, german), has_drink(S2, coffee), S1 != S2.
:- has_destination(S1, tokyo), has_profession(S2, chemist), S1 != S2.
:- has_profession(S1, engineer), has_profession(S2, lawyer), S2 != S1 + 1.
:- has_pet(S1, dog), not has_car(S1-1, volvo), not has_car(S1+1, volvo).
:- has_music(S1, rock), not has_music(S1-1, pop), not has_music(S1+1, pop).
:- has_destination(S1, paris), not has_pet(S1-1, fish), not has_pet(S1+1, fish).
:- has_profession(S, pilot), S \\ 2 != 0.
:- has_drink(S1, wine), has_drink(S2, coffee), S1 <= S2.
:- has_car(S1, ford), not has_drink(S1-1, tea), not has_drink(S1+1, tea).
:- has_car(1, nissan).
:- has_car(8, nissan).
:- has_music(S1, jazz), has_music(S2, blues), S1 >= S2.
:- not has_nationality(1, dutch).
"""
    return program

def solve_zebra_puzzle():
    ctl = clingo.Control(["1"])
    
    program = create_asp_program()
    ctl.add("base", [], program)
    ctl.ground([("base", [])])
    
    solution_data = None
    
    def on_model(m):
        nonlocal solution_data
        atoms = m.symbols(atoms=True)
        
        suites = {}
        for i in range(1, 9):
            suites[i] = {
                "suite": i,
                "nationality": None,
                "profession": None,
                "car": None,
                "drink": None,
                "music": None,
                "pet": None,
                "destination": None
            }
        
        for atom in atoms:
            if atom.name == "has_nationality" and len(atom.arguments) == 2:
                suite_num = atom.arguments[0].number
                nat = str(atom.arguments[1])
                suites[suite_num]["nationality"] = nat.capitalize()
            elif atom.name == "has_profession" and len(atom.arguments) == 2:
                suite_num = atom.arguments[0].number
                prof = str(atom.arguments[1])
                suites[suite_num]["profession"] = prof.capitalize()
            elif atom.name == "has_car" and len(atom.arguments) == 2:
                suite_num = atom.arguments[0].number
                car = str(atom.arguments[1])
                suites[suite_num]["car"] = car.upper() if car in ["bmw"] else car.capitalize()
            elif atom.name == "has_drink" and len(atom.arguments) == 2:
                suite_num = atom.arguments[0].number
                drink = str(atom.arguments[1])
                suites[suite_num]["drink"] = drink.capitalize()
            elif atom.name == "has_music" and len(atom.arguments) == 2:
                suite_num = atom.arguments[0].number
                music = str(atom.arguments[1])
                suites[suite_num]["music"] = music.capitalize()
            elif atom.name == "has_pet" and len(atom.arguments) == 2:
                suite_num = atom.arguments[0].number
                pet = str(atom.arguments[1])
                suites[suite_num]["pet"] = pet.capitalize()
            elif atom.name == "has_destination" and len(atom.arguments) == 2:
                suite_num = atom.arguments[0].number
                dest = str(atom.arguments[1])
                if dest == "newyork":
                    dest = "New York"
                else:
                    dest = dest.capitalize()
                suites[suite_num]["destination"] = dest
        
        lizard_owner = None
        for suite_num, attrs in suites.items():
            if attrs["pet"] == "Lizard":
                lizard_owner = attrs["nationality"]
                break
        
        solution_data = {
            "solution": [suites[i] for i in range(1, 9)],
            "lizard_owner": lizard_owner
        }
    
    result = ctl.solve(on_model=on_model)
    
    if result.satisfiable:
        return solution_data
    else:
        return {"error": "No solution exists", "reason": "Constraints are unsatisfiable"}

result = solve_zebra_puzzle()
print(json.dumps(result, indent=2))
