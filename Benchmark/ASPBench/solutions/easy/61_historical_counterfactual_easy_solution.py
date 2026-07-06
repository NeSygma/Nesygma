import clingo
import json

ctl = clingo.Control()

program = """
event("discovery_of_america", 1492).
event("columbian_exchange", 1500).
event("spanish_empire", 1520).
event("industrial_revolution", 1750).
event("world_wars", 1914).

requires("columbian_exchange", "discovery_of_america").
requires("spanish_empire", "discovery_of_america").
requires("industrial_revolution", "spanish_empire").
requires("world_wars", "industrial_revolution").

intervention("discovery_of_america").

occurs_original(E) :- event(E, _).

prevented(E) :- intervention(E).
prevented(E) :- requires(E, P), prevented(P).

occurs_alternate(E) :- event(E, _), not prevented(E).

direct_effect(E) :- requires(E, P), intervention(P).

cascade_effect(E) :- prevented(E), not intervention(E), not direct_effect(E).

preserved(E) :- occurs_alternate(E).

#show occurs_original/1.
#show occurs_alternate/1.
#show prevented/1.
#show direct_effect/1.
#show cascade_effect/1.
#show preserved/1.
#show intervention/1.
"""

ctl.add("base", [], program)
ctl.ground([("base", [])])

solution_data = None

def extract_solution(model):
    global solution_data
    
    original_timeline = []
    alternate_timeline = []
    prevented_events = []
    direct_effects = []
    cascade_effects = []
    preserved_events = []
    intervention_events = []
    
    event_years = {
        "discovery_of_america": 1492,
        "columbian_exchange": 1500,
        "spanish_empire": 1520,
        "industrial_revolution": 1750,
        "world_wars": 1914
    }
    
    for atom in model.symbols(atoms=True):
        if atom.name == "occurs_original" and len(atom.arguments) == 1:
            event = str(atom.arguments[0]).strip('"')
            original_timeline.append(event)
        elif atom.name == "occurs_alternate" and len(atom.arguments) == 1:
            event = str(atom.arguments[0]).strip('"')
            alternate_timeline.append(event)
        elif atom.name == "prevented" and len(atom.arguments) == 1:
            event = str(atom.arguments[0]).strip('"')
            prevented_events.append(event)
        elif atom.name == "direct_effect" and len(atom.arguments) == 1:
            event = str(atom.arguments[0]).strip('"')
            direct_effects.append(event)
        elif atom.name == "cascade_effect" and len(atom.arguments) == 1:
            event = str(atom.arguments[0]).strip('"')
            cascade_effects.append(event)
        elif atom.name == "preserved" and len(atom.arguments) == 1:
            event = str(atom.arguments[0]).strip('"')
            preserved_events.append(event)
        elif atom.name == "intervention" and len(atom.arguments) == 1:
            event = str(atom.arguments[0]).strip('"')
            intervention_events.append(event)
    
    original_timeline.sort(key=lambda e: event_years.get(e, 0))
    alternate_timeline.sort(key=lambda e: event_years.get(e, 0))
    
    solution_data = {
        "original_timeline": original_timeline,
        "alternate_timeline": alternate_timeline,
        "prevented_events": prevented_events,
        "causal_analysis": {
            "direct_effects": direct_effects,
            "cascade_effects": cascade_effects,
            "preserved_events": preserved_events,
            "intervention_events": intervention_events
        }
    }

result = ctl.solve(on_model=extract_solution)

if result.satisfiable and solution_data:
    print(json.dumps(solution_data, indent=2))
else:
    print(json.dumps({"error": "No solution exists",
                      "reason": "Problem is unsatisfiable"}))
