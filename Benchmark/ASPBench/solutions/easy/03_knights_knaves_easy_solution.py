import clingo
import json

program = """
person(alice).
person(bob).
person(charlie).

1 { knight(P) ; knave(P) } 1 :- person(P).

alice_statement_true :- knave(bob).

bob_statement_true :- knight(alice), knight(charlie).
bob_statement_true :- knave(alice), knave(charlie).

charlie_statement_true :- knight(alice).

:- knight(alice), not alice_statement_true.
:- knight(bob), not bob_statement_true.
:- knight(charlie), not charlie_statement_true.

:- knave(alice), alice_statement_true.
:- knave(bob), bob_statement_true.
:- knave(charlie), charlie_statement_true.
"""

ctl = clingo.Control(["1"])
ctl.add("base", [], program)
ctl.ground([("base", [])])

solution = None

def on_model(model):
    global solution
    solution = {}
    for atom in model.symbols(atoms=True):
        if atom.name == "knight":
            person = str(atom.arguments[0])
            solution[person] = "knight"
        elif atom.name == "knave":
            person = str(atom.arguments[0])
            solution[person] = "knave"

result = ctl.solve(on_model=on_model)

if result.satisfiable and solution:
    print(json.dumps(solution, indent=2))
else:
    print(json.dumps({"error": "No solution exists"}))
