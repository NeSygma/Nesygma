import clingo
import json

def create_asp_program_original():
    """Create ASP program for original timeline with deterministic pivot selection"""
    return """
event("ancient_knowledge", 100).
event("fall_of_rome", 476).
event("dark_ages", 500).
event("renaissance", 1300).
event("age_of_sail", 1400).
event("age_of_steam", 1700).
event("discovery_of_new_world", 1492).
event("global_trade_routes", 1550).
event("industrial_revolution", 1760).
event("information_age", 1970).
event("alternate_industrial_revolution", 1780).
event("digital_renaissance", 1980).

prereq("fall_of_rome", "ancient_knowledge").
prereq("dark_ages", "fall_of_rome").
prereq("renaissance", "dark_ages").
prereq("age_of_sail", "renaissance").
prereq("age_of_steam", "renaissance").
prereq("discovery_of_new_world", "age_of_sail").
prereq("global_trade_routes", "age_of_sail").
prereq("industrial_revolution", "age_of_steam").
prereq("information_age", "industrial_revolution").
prereq("digital_renaissance", "alternate_industrial_revolution").

pivot("paradigm", "age_of_sail").
pivot("paradigm", "age_of_steam").

cond_prereq("alternate_industrial_revolution", "global_trade_routes", "age_of_steam").

possible(E) :- event(E, _), not has_prereq(E).
possible(E) :- event(E, _), has_prereq(E), all_prereqs_met(E).

has_prereq(E) :- prereq(E, _).

all_prereqs_met(E) :- event(E, _), not missing_prereq(E).

missing_prereq(E) :- prereq(E, R), not occurs(R).

needs_cond_prereq(E, R) :- cond_prereq(E, R, Unless), not occurs(Unless).

:- occurs(E), needs_cond_prereq(E, R), not occurs(R).

:- pivot(G, E1), pivot(G, E2), E1 != E2, occurs(E1), occurs(E2).

pivot_group_has_possible(G) :- pivot(G, E), possible(E).

earliest_in_group(G, MinYear) :- pivot_group_has_possible(G),
    MinYear = #min { Year : pivot(G, E), possible(E), event(E, Year) }.

occurs(E) :- pivot(G, E), possible(E), event(E, Year), earliest_in_group(G, Year).

occurs(E) :- possible(E), not is_pivot(E).

is_pivot(E) :- pivot(_, E).

#show occurs/1.
"""

def create_asp_program_alternate():
    """Create ASP program for alternate timeline with interventions applied"""
    return """
event("ancient_knowledge", 100).
event("fall_of_rome", 476).
event("dark_ages", 500).
event("renaissance", 1300).
event("age_of_sail", 1400).
event("age_of_steam", 1700).
event("discovery_of_new_world", 1492).
event("global_trade_routes", 1550).
event("industrial_revolution", 1760).
event("information_age", 1970).
event("alternate_industrial_revolution", 1780).
event("digital_renaissance", 1980).

prereq("fall_of_rome", "ancient_knowledge").
prereq("dark_ages", "fall_of_rome").
prereq("renaissance", "dark_ages").
prereq("age_of_sail", "renaissance").
prereq("age_of_steam", "renaissance").
prereq("discovery_of_new_world", "age_of_sail").
prereq("global_trade_routes", "age_of_sail").
prereq("industrial_revolution", "age_of_steam").
prereq("information_age", "industrial_revolution").
prereq("digital_renaissance", "alternate_industrial_revolution").

pivot("paradigm", "age_of_sail").
pivot("paradigm", "age_of_steam").

cond_prereq("alternate_industrial_revolution", "global_trade_routes", "age_of_steam").

intervention_prevent("age_of_sail").

:- occurs(E), intervention_prevent(E).

possible(E) :- event(E, _), not has_prereq(E).
possible(E) :- event(E, _), has_prereq(E), all_prereqs_met(E).

has_prereq(E) :- prereq(E, _).

all_prereqs_met(E) :- event(E, _), not missing_prereq(E).

missing_prereq(E) :- prereq(E, R), not occurs(R).

needs_cond_prereq(E, R) :- cond_prereq(E, R, Unless), not occurs(Unless).

:- occurs(E), needs_cond_prereq(E, R), not occurs(R).

:- pivot(G, E1), pivot(G, E2), E1 != E2, occurs(E1), occurs(E2).

pivot_group_has_possible(G) :- pivot(G, E), possible(E), not intervention_prevent(E).

earliest_in_group(G, MinYear) :- pivot_group_has_possible(G),
    MinYear = #min { Year : pivot(G, E), possible(E), not intervention_prevent(E), event(E, Year) }.

occurs(E) :- pivot(G, E), possible(E), event(E, Year), earliest_in_group(G, Year), 
    not intervention_prevent(E).

occurs(E) :- possible(E), not is_pivot(E), not intervention_prevent(E).

is_pivot(E) :- pivot(_, E).

#show occurs/1.
"""

def solve_timeline(program):
    ctl = clingo.Control(["1"])
    ctl.add("base", [], program)
    ctl.ground([("base", [])])
    
    events = []
    
    def on_model(m):
        nonlocal events
        for atom in m.symbols(atoms=True):
            if atom.name == "occurs" and len(atom.arguments) == 1:
                event_id = str(atom.arguments[0]).strip('"')
                events.append(event_id)
    
    result = ctl.solve(on_model=on_model)
    
    if not result.satisfiable:
        return None
    
    return events

event_years = {
    "ancient_knowledge": 100,
    "fall_of_rome": 476,
    "dark_ages": 500,
    "renaissance": 1300,
    "age_of_sail": 1400,
    "age_of_steam": 1700,
    "discovery_of_new_world": 1492,
    "global_trade_routes": 1550,
    "industrial_revolution": 1760,
    "information_age": 1970,
    "alternate_industrial_revolution": 1780,
    "digital_renaissance": 1980
}

original_timeline = solve_timeline(create_asp_program_original())
alternate_timeline = solve_timeline(create_asp_program_alternate())

original_sorted = sorted(original_timeline, key=lambda e: event_years[e])
alternate_sorted = sorted(alternate_timeline, key=lambda e: event_years[e])

prevented_events = sorted(list(set(original_timeline) - set(alternate_timeline)))
activated_events = sorted(list(set(alternate_timeline) - set(original_timeline)))

output = {
    "instance": {
        "events": [
            {"id": "ancient_knowledge", "year": 100},
            {"id": "fall_of_rome", "year": 476},
            {"id": "dark_ages", "year": 500},
            {"id": "renaissance", "year": 1300},
            {"id": "age_of_sail", "year": 1400},
            {"id": "discovery_of_new_world", "year": 1492},
            {"id": "global_trade_routes", "year": 1550},
            {"id": "age_of_steam", "year": 1700},
            {"id": "industrial_revolution", "year": 1760},
            {"id": "alternate_industrial_revolution", "year": 1780},
            {"id": "information_age", "year": 1970},
            {"id": "digital_renaissance", "year": 1980}
        ],
        "prerequisites": [
            {"event": "fall_of_rome", "requires": "ancient_knowledge"},
            {"event": "dark_ages", "requires": "fall_of_rome"},
            {"event": "renaissance", "requires": "dark_ages"},
            {"event": "age_of_sail", "requires": "renaissance"},
            {"event": "age_of_steam", "requires": "renaissance"},
            {"event": "discovery_of_new_world", "requires": "age_of_sail"},
            {"event": "global_trade_routes", "requires": "age_of_sail"},
            {"event": "industrial_revolution", "requires": "age_of_steam"},
            {"event": "information_age", "requires": "industrial_revolution"},
            {"event": "digital_renaissance", "requires": "alternate_industrial_revolution"}
        ],
        "pivots": [
            {"group": "paradigm", "event": "age_of_sail"},
            {"group": "paradigm", "event": "age_of_steam"}
        ],
        "conditional_prerequisites": [
            {"event": "alternate_industrial_revolution", "requires": "global_trade_routes", "unless": "age_of_steam"}
        ],
        "interventions": [
            {"event_id": "age_of_sail", "action": "prevent"}
        ]
    },
    "solution": {
        "original_timeline": original_sorted,
        "alternate_timeline": alternate_sorted,
        "prevented_events": prevented_events,
        "activated_events": activated_events,
        "paradoxes": []
    }
}

print(json.dumps(output, indent=2))
