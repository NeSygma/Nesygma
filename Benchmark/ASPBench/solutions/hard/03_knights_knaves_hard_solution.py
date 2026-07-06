import clingo
import json

program = """
person(alice). person(bob). person(charlie). person(diana).
person(ethan). person(fiona). person(george). person(hannah).
person(ian). person(julia). person(kevin). person(lily).
person(mason). person(nina). person(oliver). person(paula).
person(quentin). person(rachel). person(sam). person(tina).
person(ursula). person(victor). person(wendy). person(xavier).

group(alice, a). group(bob, a). group(charlie, a). group(diana, a).
group(ethan, a). group(fiona, a). group(george, a). group(hannah, a).
group(ian, b). group(julia, b). group(kevin, b). group(lily, b).
group(mason, b). group(nina, b). group(oliver, b). group(paula, b).
group(quentin, c). group(rachel, c). group(sam, c). group(tina, c).
group(ursula, c). group(victor, c). group(wendy, c). group(xavier, c).

{ knight(P) } :- person(P).
knave(P) :- person(P), not knight(P).

same_type(P1, P2) :- knight(P1), knight(P2).
same_type(P1, P2) :- knave(P1), knave(P2).
different_types(P1, P2) :- knight(P1), knave(P2).
different_types(P1, P2) :- knave(P1), knight(P2).

group_a_knights(N) :- N = #count { P : knight(P), group(P, a) }.
group_b_knights(N) :- N = #count { P : knight(P), group(P, b) }.
group_c_knights(N) :- N = #count { P : knight(P), group(P, c) }.
total_knights(N) :- N = #count { P : knight(P) }.

alice_cond2 :- knave(bob).
alice_cond2 :- knight(charlie).
alice_statement_true :- knave(hannah), alice_cond2, group_a_knights(4).
:- knight(alice), not alice_statement_true.
:- knave(alice), alice_statement_true.

bob_statement_true :- same_type(bob, diana).
:- knight(bob), not bob_statement_true.
:- knave(bob), bob_statement_true.

charlie_statement_true :- total_knights(12).
:- knight(charlie), not charlie_statement_true.
:- knave(charlie), charlie_statement_true.

diana_statement_true :- different_types(ethan, fiona), knave(hannah).
:- knight(diana), not diana_statement_true.
:- knave(diana), diana_statement_true.

ethan_statement_true :- knight(george), knight(alice).
ethan_statement_true :- knave(george), knave(alice).
:- knight(ethan), not ethan_statement_true.
:- knave(ethan), ethan_statement_true.

fiona_statement_true :- different_types(bob, charlie), knight(fiona).
:- knight(fiona), not fiona_statement_true.
:- knave(fiona), fiona_statement_true.

george_statement_true :- same_type(alice, hannah).
:- knight(george), not george_statement_true.
:- knave(george), george_statement_true.

hannah_count(N) :- N = #count { P : knight(P), member_bcd(P) }.
member_bcd(bob). member_bcd(charlie). member_bcd(diana).
hannah_statement_true :- hannah_count(1).
:- knight(hannah), not hannah_statement_true.
:- knave(hannah), hannah_statement_true.

ian_statement_true :- same_type(alice, paula), knave(julia).
:- knight(ian), not ian_statement_true.
:- knave(ian), ian_statement_true.

julia_statement_true :- knight(kevin), knight(nina).
:- knight(julia), not julia_statement_true.
:- knave(julia), julia_statement_true.

kevin_statement_true :- knight(oliver).
kevin_statement_true :- knave(lily).
:- knight(kevin), not kevin_statement_true.
:- knave(kevin), kevin_statement_true.

lily_statement_true :- group_b_knights(4), knave(oliver).
:- knight(lily), not lily_statement_true.
:- knave(lily), lily_statement_true.

mason_statement_true :- same_type(bob, ethan), knave(julia).
:- knight(mason), not mason_statement_true.
:- knave(mason), mason_statement_true.

nina_statement_true :- different_types(ian, paula).
:- knight(nina), not nina_statement_true.
:- knave(nina), nina_statement_true.

oliver_count(N) :- N = #count { P : knight(P), member_ghij(P) }.
member_ghij(george). member_ghij(hannah). member_ghij(ian). member_ghij(julia).
oliver_statement_true :- oliver_count(2).
:- knight(oliver), not oliver_statement_true.
:- knave(oliver), oliver_statement_true.

paula_statement_true :- knight(rachel), knave(quentin).
paula_statement_true :- knave(rachel), knight(quentin).
:- knight(paula), not paula_statement_true.
:- knave(paula), paula_statement_true.

quentin_statement_true :- group_c_knights(N), N >= 5.
:- knight(quentin), not quentin_statement_true.
:- knave(quentin), quentin_statement_true.

rachel_statement_true :- knight(charlie), knight(lily), knave(victor).
:- knight(rachel), not rachel_statement_true.
:- knave(rachel), rachel_statement_true.

sam_statement_true :- knave(tina), knave(oliver), knave(ursula).
:- knight(sam), not sam_statement_true.
:- knave(sam), sam_statement_true.

tina_statement_true :- knave(rachel).
tina_statement_true :- knave(mason).
:- knight(tina), not tina_statement_true.
:- knave(tina), tina_statement_true.

ursula_statement_true :- knight(ian), knight(julia).
:- knight(ursula), not ursula_statement_true.
:- knave(ursula), ursula_statement_true.

victor_count(N) :- N = #count { P : knave(P), member_abcd(P) }.
member_abcd(alice). member_abcd(bob). member_abcd(charlie). member_abcd(diana).
victor_statement_true :- victor_count(2).
:- knight(victor), not victor_statement_true.
:- knave(victor), victor_statement_true.

wendy_statement_true :- knave(victor), knave(ursula), knight(xavier).
:- knight(wendy), not wendy_statement_true.
:- knave(wendy), wendy_statement_true.

xavier_statement_true :- group_c_knights(4), knight(sam).
:- knight(xavier), not xavier_statement_true.
:- knave(xavier), xavier_statement_true.
"""

ctl = clingo.Control(["1"])
ctl.add("base", [], program)
ctl.ground([("base", [])])

solution = None

def on_model(model):
    global solution
    solution = {}
    
    for atom in model.symbols(atoms=True):
        if atom.name == "knight" and len(atom.arguments) == 1:
            person_name = str(atom.arguments[0]).strip('"')
            solution[person_name] = "knight"
    
    all_people = [
        "alice", "bob", "charlie", "diana", "ethan", "fiona", "george", "hannah",
        "ian", "julia", "kevin", "lily", "mason", "nina", "oliver", "paula",
        "quentin", "rachel", "sam", "tina", "ursula", "victor", "wendy", "xavier"
    ]
    
    for person in all_people:
        if person not in solution:
            solution[person] = "knave"

result = ctl.solve(on_model=on_model)

if result.satisfiable:
    print(json.dumps(solution, indent=2))
else:
    print(json.dumps({"error": "No solution exists", "reason": "The constraints are unsatisfiable"}))
