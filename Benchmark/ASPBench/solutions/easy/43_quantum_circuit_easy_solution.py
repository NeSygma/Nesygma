import clingo
import json

program = """
% Facts: Qubits
qubit("q0"). qubit("q1"). qubit("q2"). qubit("q3").

% Facts: Gates
gate("h_q0").
gate("h_q1").
gate("x_q2").
gate("cnot_q0_q1").
gate("cnot_q1_q2").
gate("cnot_q0_q3").

% Facts: Gate-Qubit relationships
uses("h_q0", "q0").
uses("h_q1", "q1").
uses("x_q2", "q2").
uses("cnot_q0_q1", "q0").
uses("cnot_q0_q1", "q1").
uses("cnot_q1_q2", "q1").
uses("cnot_q1_q2", "q2").
uses("cnot_q0_q3", "q0").
uses("cnot_q0_q3", "q3").

% Time domain: Use expected optimal depth of 3
time(1..3).

% Choice rule: Each gate must be scheduled at exactly one time step
1 { scheduled(G, T) : time(T) } 1 :- gate(G).

% Constraint: Two gates cannot execute at the same time if they share a qubit
:- scheduled(G1, T), scheduled(G2, T), G1 != G2, 
   uses(G1, Q), uses(G2, Q).

% Define circuit depth as the maximum time step used
circuit_depth(D) :- D = #max { T : scheduled(_, T) }.

% Constraint: Circuit depth must be at most 3 (the expected optimal)
:- circuit_depth(D), D > 3.
"""

ctl = clingo.Control(["1"])
ctl.add("base", [], program)
ctl.ground([("base", [])])

solution_data = None

def on_model(model):
    global solution_data
    
    schedule = {}
    depth = 0
    
    for atom in model.symbols(atoms=True):
        if atom.name == "scheduled" and len(atom.arguments) == 2:
            gate = str(atom.arguments[0]).strip('"')
            time_step = atom.arguments[1].number
            
            if time_step not in schedule:
                schedule[time_step] = []
            schedule[time_step].append(gate)
            depth = max(depth, time_step)
        elif atom.name == "circuit_depth" and len(atom.arguments) == 1:
            depth = atom.arguments[0].number
    
    solution_data = {
        "circuit_depth": depth,
        "schedule": schedule
    }

result = ctl.solve(on_model=on_model)

if result.satisfiable:
    gate_schedule = []
    for t in sorted(solution_data['schedule'].keys()):
        gate_schedule.append({
            "time": t,
            "gates": sorted(solution_data['schedule'][t])
        })
    
    output = {
        "circuit_depth": solution_data['circuit_depth'],
        "gate_schedule": gate_schedule
    }
    
    print(json.dumps(output, indent=2))
else:
    print(json.dumps({"error": "No solution exists", 
                      "reason": "Unable to schedule gates within depth constraint"}))
