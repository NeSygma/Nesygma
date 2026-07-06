import clingo
import json

asp_program = """
arg(a). arg(b). arg(c). arg(d). arg(e). arg(f).

attacks(a, b).
attacks(b, c).
attacks(c, d).
attacks(d, e).
attacks(e, f).
attacks(f, a).
attacks(b, f).
attacks(d, b).

{ in(X) } :- arg(X).

:- in(X), in(Y), attacks(X, Y).

attacked_by_extension(Y) :- in(X), attacks(X, Y).

:- in(X), attacks(Y, X), not attacked_by_extension(Y).

:- arg(X), not in(X), not attacked_by_extension(X).
"""

ctl = clingo.Control(["0"])
ctl.add("base", [], asp_program)
ctl.ground([("base", [])])

all_extensions = []

def on_model(model):
    extension = []
    for atom in model.symbols(atoms=True):
        if atom.name == "in" and len(atom.arguments) == 1:
            arg_name = str(atom.arguments[0])
            extension.append(arg_name)
    extension.sort()
    all_extensions.append(extension)

result = ctl.solve(on_model=on_model)

if result.satisfiable:
    output = {"stable_extensions": all_extensions}
    print(json.dumps(output))
else:
    print(json.dumps({"error": "No stable extensions found"}))
