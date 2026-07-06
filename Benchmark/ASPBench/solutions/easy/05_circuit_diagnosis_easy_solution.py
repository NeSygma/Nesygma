import clingo
import json

def solve_circuit_diagnosis():
    ctl = clingo.Control(["0", "--opt-mode=optN"])
    
    program = """
    component(and1; or1; notgate1; xor1; and2).
    
    gate_type(and1, andgate).
    gate_type(or1, orgate).
    gate_type(notgate1, notgate).
    gate_type(xor1, xorgate).
    gate_type(and2, andgate).
    
    gate_input(and1, 1, in1).
    gate_input(and1, 2, in2).
    gate_output(and1, w1).
    
    gate_input(or1, 1, w1).
    gate_input(or1, 2, in3).
    gate_output(or1, w2).
    
    gate_input(notgate1, 1, w2).
    gate_output(notgate1, out1).
    
    gate_input(xor1, 1, in1).
    gate_input(xor1, 2, in4).
    gate_output(xor1, w3).
    
    gate_input(and2, 1, w3).
    gate_input(and2, 2, in2).
    gate_output(and2, out2).
    
    input_value(in1, 1).
    input_value(in2, 0).
    input_value(in3, 1).
    input_value(in4, 1).
    
    observed_output(out1, 1).
    observed_output(out2, 0).
    
    wire(in1; in2; in3; in4; w1; w2; w3; out1; out2).
    value(0; 1).
    
    { faulty(C) } :- component(C).
    
    1 { wire_value(W, V) : value(V) } 1 :- wire(W).
    
    wire_value(W, V) :- input_value(W, V).
    
    wire_value(Out, 1) :- gate_type(G, andgate), gate_output(G, Out), 
                          component(G), not faulty(G),
                          gate_input(G, 1, In1), gate_input(G, 2, In2),
                          wire_value(In1, 1), wire_value(In2, 1).
    wire_value(Out, 0) :- gate_type(G, andgate), gate_output(G, Out), 
                          component(G), not faulty(G),
                          gate_input(G, 1, In1), gate_input(G, 2, In2),
                          wire_value(In1, 0).
    wire_value(Out, 0) :- gate_type(G, andgate), gate_output(G, Out), 
                          component(G), not faulty(G),
                          gate_input(G, 1, In1), gate_input(G, 2, In2),
                          wire_value(In2, 0).
    
    wire_value(Out, 1) :- gate_type(G, orgate), gate_output(G, Out), 
                          component(G), not faulty(G),
                          gate_input(G, 1, In1), gate_input(G, 2, In2),
                          wire_value(In1, 1).
    wire_value(Out, 1) :- gate_type(G, orgate), gate_output(G, Out), 
                          component(G), not faulty(G),
                          gate_input(G, 1, In1), gate_input(G, 2, In2),
                          wire_value(In2, 1).
    wire_value(Out, 0) :- gate_type(G, orgate), gate_output(G, Out), 
                          component(G), not faulty(G),
                          gate_input(G, 1, In1), gate_input(G, 2, In2),
                          wire_value(In1, 0), wire_value(In2, 0).
    
    wire_value(Out, 1) :- gate_type(G, notgate), gate_output(G, Out), 
                          component(G), not faulty(G),
                          gate_input(G, 1, In), wire_value(In, 0).
    wire_value(Out, 0) :- gate_type(G, notgate), gate_output(G, Out), 
                          component(G), not faulty(G),
                          gate_input(G, 1, In), wire_value(In, 1).
    
    wire_value(Out, 1) :- gate_type(G, xorgate), gate_output(G, Out), 
                          component(G), not faulty(G),
                          gate_input(G, 1, In1), gate_input(G, 2, In2),
                          wire_value(In1, 1), wire_value(In2, 0).
    wire_value(Out, 1) :- gate_type(G, xorgate), gate_output(G, Out), 
                          component(G), not faulty(G),
                          gate_input(G, 1, In1), gate_input(G, 2, In2),
                          wire_value(In1, 0), wire_value(In2, 1).
    wire_value(Out, 0) :- gate_type(G, xorgate), gate_output(G, Out), 
                          component(G), not faulty(G),
                          gate_input(G, 1, In1), gate_input(G, 2, In2),
                          wire_value(In1, 0), wire_value(In2, 0).
    wire_value(Out, 0) :- gate_type(G, xorgate), gate_output(G, Out), 
                          component(G), not faulty(G),
                          gate_input(G, 1, In1), gate_input(G, 2, In2),
                          wire_value(In1, 1), wire_value(In2, 1).
    
    :- observed_output(W, V), wire_value(W, V2), V != V2.
    
    #minimize { 1,C : faulty(C) }.
    """
    
    ctl.add("base", [], program)
    ctl.ground([("base", [])])
    
    diagnoses = []
    
    def on_model(model):
        if model.optimality_proven:
            faulty_components = []
            for atom in model.symbols(atoms=True):
                if atom.name == "faulty" and len(atom.arguments) == 1:
                    comp = str(atom.arguments[0])
                    faulty_components.append(comp)
            
            faulty_components.sort()
            if faulty_components not in diagnoses:
                diagnoses.append(faulty_components)
    
    result = ctl.solve(on_model=on_model)
    
    if result.satisfiable:
        output = {
            "diagnoses": [
                {"components": diag, "minimal": True}
                for diag in diagnoses
            ],
            "explanation": "Each diagnosis represents a minimal set of components that, if faulty, would explain the observed discrepancy."
        }
        return output
    else:
        return {
            "error": "No solution exists",
            "reason": "No diagnosis could explain the observed outputs"
        }

if __name__ == "__main__":
    solution = solve_circuit_diagnosis()
    print(json.dumps(solution, indent=2))
