import clingo
import json

program = """
vertex(1..24).

vertex_zone(1,1). vertex_zone(2,1). vertex_zone(3,1). vertex_zone(4,1).
vertex_zone(5,1). vertex_zone(6,1). vertex_zone(7,1). vertex_zone(8,1).
vertex_zone(9,2). vertex_zone(10,2). vertex_zone(11,2). vertex_zone(12,2).
vertex_zone(13,2). vertex_zone(14,2). vertex_zone(15,2). vertex_zone(16,2).
vertex_zone(17,3). vertex_zone(18,3). vertex_zone(19,3). vertex_zone(20,3).
vertex_zone(21,3). vertex_zone(22,3). vertex_zone(23,3). vertex_zone(24,3).

vertex_type(1,core). vertex_type(9,core). vertex_type(17,core).
vertex_type(2,support). vertex_type(3,support). vertex_type(10,support).
vertex_type(11,support). vertex_type(18,support). vertex_type(19,support).
vertex_type(4,peripheral). vertex_type(5,peripheral). vertex_type(6,peripheral).
vertex_type(7,peripheral). vertex_type(8,peripheral). vertex_type(12,peripheral).
vertex_type(13,peripheral). vertex_type(14,peripheral). vertex_type(15,peripheral).
vertex_type(16,peripheral). vertex_type(20,peripheral). vertex_type(21,peripheral).
vertex_type(22,peripheral). vertex_type(23,peripheral). vertex_type(24,peripheral).

edge(1,2). edge(2,1).
edge(1,4). edge(4,1).
edge(1,10). edge(10,1).
edge(1,17). edge(17,1).
edge(2,5). edge(5,2).
edge(2,9). edge(9,2).
edge(3,6). edge(6,3).
edge(4,7). edge(7,4).
edge(5,8). edge(8,5).
edge(6,7). edge(7,6).
edge(8,16). edge(16,8).
edge(8,24). edge(24,8).
edge(9,10). edge(10,9).
edge(9,12). edge(12,9).
edge(9,17). edge(17,9).
edge(10,14). edge(14,10).
edge(11,15). edge(15,11).
edge(12,16). edge(16,12).
edge(13,14). edge(14,13).
edge(16,24). edge(24,16).
edge(17,18). edge(18,17).
edge(17,20). edge(20,17).
edge(18,19). edge(19,18).
edge(18,21). edge(21,18).
edge(19,22). edge(22,19).
edge(20,23). edge(23,20).
edge(21,24). edge(24,21).

{ in_set(V) } :- vertex(V).

:- in_set(V1), in_set(V2), edge(V1,V2).

:- #count { V : in_set(V), vertex_type(V,core) } > 2.

:- in_set(V), vertex_type(V,core), vertex_zone(V,Z),
   #count { S : in_set(S), vertex_type(S,support), vertex_zone(S,Z) } = 0.

has_zone1_peripheral :- in_set(V), vertex_type(V,peripheral), vertex_zone(V,1).
:- has_zone1_peripheral, in_set(V), vertex_zone(V,3).

peripheral_count(N) :- N = #count { V : in_set(V), vertex_type(V,peripheral) }.
core_count(N) :- N = #count { V : in_set(V), vertex_type(V,core) }.
:- peripheral_count(P), core_count(C), P > C.

#maximize { 1,V : in_set(V) }.
"""

ctl = clingo.Control(["0"])
ctl.add("base", [], program)
ctl.ground([("base", [])])

vertex_types = {
    1: 'core', 9: 'core', 17: 'core',
    2: 'support', 3: 'support', 10: 'support', 11: 'support', 18: 'support', 19: 'support',
    4: 'peripheral', 5: 'peripheral', 6: 'peripheral', 7: 'peripheral', 8: 'peripheral',
    12: 'peripheral', 13: 'peripheral', 14: 'peripheral', 15: 'peripheral', 16: 'peripheral',
    20: 'peripheral', 21: 'peripheral', 22: 'peripheral', 23: 'peripheral', 24: 'peripheral'
}

solution_data = None

def on_model(model):
    global solution_data
    independent_set = []
    for atom in model.symbols(atoms=True):
        if atom.name == "in_set" and len(atom.arguments) == 1:
            vertex = atom.arguments[0].number
            independent_set.append(vertex)
    
    independent_set.sort()
    
    core_vertices = []
    support_vertices = []
    peripheral_vertices = []
    
    for v in independent_set:
        vtype = vertex_types[v]
        if vtype == 'core':
            core_vertices.append(v)
        elif vtype == 'support':
            support_vertices.append(v)
        elif vtype == 'peripheral':
            peripheral_vertices.append(v)
    
    solution_data = {
        "independent_set": independent_set,
        "size": len(independent_set),
        "core_vertices": core_vertices,
        "support_vertices": support_vertices,
        "peripheral_vertices": peripheral_vertices,
        "core_count": len(core_vertices),
        "support_count": len(support_vertices),
        "peripheral_count": len(peripheral_vertices)
    }

result = ctl.solve(on_model=on_model)

if result.satisfiable and solution_data:
    print(json.dumps(solution_data, indent=2))
else:
    print(json.dumps({"error": "No solution exists"}))
