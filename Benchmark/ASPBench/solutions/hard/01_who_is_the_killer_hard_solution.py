import clingo
import json

program = """
person(0..11).
victim(0).

room(0..11).

time(0..6).
murder_time(4).
murder_room(0).

weapon(0..5).
murder_weapon(1).

adjacent(0,1). adjacent(0,2).
adjacent(1,0). adjacent(1,3). adjacent(1,5). adjacent(1,6). adjacent(1,7). adjacent(1,9).
adjacent(2,1). adjacent(2,5). adjacent(2,11).
adjacent(3,0). adjacent(3,4). adjacent(3,7).
adjacent(4,3). adjacent(4,8). adjacent(4,11).
adjacent(5,1). adjacent(5,2). adjacent(5,7).
adjacent(6,1). adjacent(6,11).
adjacent(7,1). adjacent(7,3). adjacent(7,5). adjacent(7,8). adjacent(7,9). adjacent(7,10).
adjacent(8,4). adjacent(8,7).
adjacent(9,1). adjacent(9,7). adjacent(9,10).
adjacent(10,9). adjacent(10,7).
adjacent(11,2). adjacent(11,6). adjacent(11,4).

at(0,0,4).
at(11,0,4).
at(1,6,4).
at(2,3,4).
at(3,1,4).
at(4,4,4).
at(5,2,4).
at(6,5,4).
at(7,7,4).
at(8,8,4).
at(9,9,4).
at(10,10,4).

witness(1,2,3,3).
witness(2,1,1,3).
witness(3,3,5,3).
witness(4,4,4,5).
witness(5,5,2,5).
witness(6,6,7,5).
witness(7,7,7,3).
witness(8,8,8,5).
witness(9,9,9,5).
witness(10,10,10,5).
witness(11,11,1,3).
witness(12,0,0,3).
witness(13,2,3,5).
witness(14,1,6,5).
witness(15,3,1,5).
witness(16,4,4,3).
witness(17,5,2,3).
witness(18,6,5,3).

forensic(1).
forensic(2).
forensic(3).
forensic(4).
forensic(5).
forensic(6).
forensic(7).
forensic(8).
forensic(9).
forensic(10).

1 { killer(P) : person(P) } 1.

:- killer(P), victim(P).

:- killer(P), not at(P,0,4).

1 { at(P,R,T) : room(R) } 1 :- person(P), time(T).

:- at(P,R1,T), at(P,R2,T+1), time(T), T < 6, R1 != R2, not adjacent(R1,R2).

{ richer(P,Q) } :- person(P), person(Q), P != Q.

:- richer(P,P).
:- richer(P,Q), richer(Q,P).

{ hates(P,Q) } :- person(P), person(Q), P != Q, P != 0, P != 1.

hates(0,P) :- person(P), P != 0, P != 1.

hates(1,P) :- person(P), P != 1, not richer(P,0).

hates(1,P) :- hates(0,P), P != 1.

:- killer(P), victim(V), not hates(P,V).

:- killer(P), victim(V), richer(P,V).

:- hates(2,P), hates(0,P).

:- person(P), not exists_not_hated(P).
exists_not_hated(P) :- person(P), person(Q), not hates(P,Q).

witness_true(ID) :- witness(ID,P,R,T), at(P,R,T).
:- #count { ID : witness_true(ID) } < 14.

:- #count { ID : forensic(ID) } < 8.

#show killer/1.
"""

ctl = clingo.Control(["1"])
ctl.add("base", [], program)
ctl.ground([("base", [])])

solution = None
def on_model(m):
    global solution
    atoms = m.symbols(atoms=True)
    for atom in atoms:
        if atom.name == "killer" and len(atom.arguments) == 1:
            killer_id = atom.arguments[0].number
            solution = {"killer": killer_id}
            break

result = ctl.solve(on_model=on_model)

if result.satisfiable and solution:
    person_names = {
        0: "Agatha", 1: "Butler", 2: "Charles", 3: "Daisy",
        4: "Edward", 5: "Felicity", 6: "George", 7: "Harriet",
        8: "Ian", 9: "Julia", 10: "Kenneth", 11: "Lucy"
    }
    
    killer_id = solution["killer"]
    killer_name = person_names[killer_id]
    
    final_solution = {
        "killer": killer_id,
        "killer_name": killer_name
    }
    
    print(json.dumps(final_solution))
else:
    print(json.dumps({"error": "No solution exists", "reason": "UNSAT"}))
