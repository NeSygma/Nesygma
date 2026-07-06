import clingo
import json

asp_program = """
qubit(q0; q1; q2; q3; q4; q5; q6; q7).

adjacent(q0, q1). adjacent(q1, q0).
adjacent(q1, q2). adjacent(q2, q1).
adjacent(q2, q3). adjacent(q3, q2).
adjacent(q4, q5). adjacent(q5, q4).
adjacent(q5, q6). adjacent(q6, q5).
adjacent(q6, q7). adjacent(q7, q6).
adjacent(q0, q4). adjacent(q4, q0).
adjacent(q1, q5). adjacent(q5, q1).
adjacent(q2, q6). adjacent(q6, q2).
adjacent(q3, q7). adjacent(q7, q3).

single_gate(h_q0, q0).
single_gate(x_q1, q1).

cnot_gate(cnot_q2_q3, q2, q3).
cnot_gate(cnot_q4_q5, q4, q5).
cnot_gate(cnot_q0_q2, q0, q2).

toffoli_gate(toffoli_q5_q7_q6, q5, q7, q6).

depends(cnot_q4_q5, toffoli_q5_q7_q6).

gate(G) :- single_gate(G, _).
gate(G) :- cnot_gate(G, _, _).
gate(G) :- toffoli_gate(G, _, _, _).

#const max_time = 6.
time(0..max_time).

at_position(L, L, 0) :- qubit(L).

1 { execute(G, T) : time(T), T > 0 } 1 :- gate(G).

{ swap(P1, P2, T) : adjacent(P1, P2), P1 < P2 } :- time(T), T > 0.

at_position(L1, P2, T+1) :- swap(P1, P2, T), at_position(L1, P1, T), at_position(L2, P2, T), L1 != L2.
at_position(L2, P1, T+1) :- swap(P1, P2, T), at_position(L1, P1, T), at_position(L2, P2, T), L1 != L2.

at_position(L, P, T+1) :- at_position(L, P, T), time(T+1), 
    not swap(P, _, T), not swap(_, P, T).

:- qubit(L), time(T), #count { P : at_position(L, P, T) } != 1.

:- qubit(P), time(T), #count { L : at_position(L, P, T) } != 1.

:- depends(G1, G2), execute(G1, T1), execute(G2, T2), T1 >= T2.

:- cnot_gate(G, LC, LT), execute(G, T), 
   at_position(LC, PC, T), at_position(LT, PT, T),
   not adjacent(PC, PT).

:- toffoli_gate(G, LC1, LC2, LT), execute(G, T),
   at_position(LC1, PC1, T), at_position(LT, PT, T),
   not adjacent(PC1, PT).
:- toffoli_gate(G, LC1, LC2, LT), execute(G, T),
   at_position(LC2, PC2, T), at_position(LT, PT, T),
   not adjacent(PC2, PT).

uses_physical(P, single, G, T) :- single_gate(G, L), execute(G, T), at_position(L, P, T).

uses_physical(PC, cnot_c, G, T) :- cnot_gate(G, LC, _), execute(G, T), at_position(LC, PC, T).
uses_physical(PT, cnot_t, G, T) :- cnot_gate(G, _, LT), execute(G, T), at_position(LT, PT, T).

uses_physical(PC1, toffoli_c1, G, T) :- toffoli_gate(G, LC1, _, _), execute(G, T), at_position(LC1, PC1, T).
uses_physical(PC2, toffoli_c2, G, T) :- toffoli_gate(G, _, LC2, _), execute(G, T), at_position(LC2, PC2, T).
uses_physical(PT, toffoli_t, G, T) :- toffoli_gate(G, _, _, LT), execute(G, T), at_position(LT, PT, T).

uses_physical(P1, swap1, (P1,P2), T) :- swap(P1, P2, T).
uses_physical(P2, swap2, (P1,P2), T) :- swap(P1, P2, T).

:- uses_physical(P, Type1, Op1, T), uses_physical(P, Type2, Op2, T),
   (Type1, Op1) != (Type2, Op2).

has_operation(T) :- execute(_, T).
has_operation(T) :- swap(_, _, T).
circuit_depth(D) :- D = #max { T : has_operation(T) }.

total_swaps(N) :- N = #count { P1, P2, T : swap(P1, P2, T) }.

#minimize { D@2 : circuit_depth(D) }.
#minimize { N@1 : total_swaps(N) }.

#show execute/2.
#show swap/3.
#show circuit_depth/1.
#show total_swaps/1.
"""

ctl = clingo.Control(["0"])
ctl.add("base", [], asp_program)
ctl.ground([("base", [])])

solution_data = None

def on_model(model):
    global solution_data
    
    atoms = model.symbols(atoms=True)
    
    executions = {}
    swaps = {}
    depth = 0
    swap_count = 0
    
    for atom in atoms:
        if atom.name == "execute" and len(atom.arguments) == 2:
            gate = str(atom.arguments[0])
            time = atom.arguments[1].number
            if time not in executions:
                executions[time] = []
            executions[time].append(gate)
        
        elif atom.name == "swap" and len(atom.arguments) == 3:
            q1 = str(atom.arguments[0])
            q2 = str(atom.arguments[1])
            time = atom.arguments[2].number
            if time not in swaps:
                swaps[time] = []
            swaps[time].append(f"swap_{q1}_{q2}")
        
        elif atom.name == "circuit_depth":
            depth = atom.arguments[0].number
        
        elif atom.name == "total_swaps":
            swap_count = atom.arguments[0].number
    
    solution_data = {
        "executions": executions,
        "swaps": swaps,
        "depth": depth,
        "swap_count": swap_count
    }

result = ctl.solve(on_model=on_model)

if result.satisfiable:
    gate_schedule = []
    all_times = sorted(set(list(solution_data['executions'].keys()) + list(solution_data['swaps'].keys())))
    
    for t in all_times:
        gates = []
        
        if t in solution_data['executions']:
            gates.extend(solution_data['executions'][t])
        
        if t in solution_data['swaps']:
            gates.extend(solution_data['swaps'][t])
        
        gates.sort()
        
        gate_schedule.append({
            "time": t,
            "gates": gates
        })
    
    output = {
        "circuit_depth": solution_data['depth'],
        "swaps_used": solution_data['swap_count'],
        "gate_schedule": gate_schedule
    }
    
    print(json.dumps(output, indent=2))
else:
    print(json.dumps({"error": "No solution exists", "reason": "UNSAT"}))
