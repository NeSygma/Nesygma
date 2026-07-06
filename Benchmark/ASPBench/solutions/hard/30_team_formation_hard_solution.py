import clingo
import json

asp_program = """
person("Alex", "Senior").
person("Ben", "Senior").
person("Chloe", "Senior").
person("David", "Senior").
person("Grace", "Senior").
person("Harry", "Senior").
person("Eva", "Junior").
person("Frank", "Junior").
person("Ivy", "Junior").
person("Jack", "Junior").
person("Kate", "Junior").
person("Leo", "Junior").

has_skill("Alex", "Programming").
has_skill("Alex", "Security").
has_skill("Ben", "Programming").
has_skill("Ben", "DevOps").
has_skill("Chloe", "Design").
has_skill("Chloe", "Management").
has_skill("David", "Testing").
has_skill("David", "DataScience").
has_skill("Grace", "Management").
has_skill("Grace", "DataScience").
has_skill("Harry", "DevOps").
has_skill("Harry", "Security").
has_skill("Eva", "Programming").
has_skill("Eva", "Cloud").
has_skill("Frank", "Design").
has_skill("Frank", "Testing").
has_skill("Ivy", "Design").
has_skill("Ivy", "Cloud").
has_skill("Jack", "Testing").
has_skill("Jack", "Programming").
has_skill("Kate", "Management").
has_skill("Kate", "DevOps").
has_skill("Leo", "DataScience").
has_skill("Leo", "Security").

project("Alpha").
project("Beta").
project("Gamma").

project_requires("Alpha", "Security").
project_requires("Beta", "Cloud").

incompatible("Alex", "Ben").
incompatible("Ben", "Alex").
incompatible("Chloe", "Grace").
incompatible("Grace", "Chloe").
incompatible("David", "Harry").
incompatible("Harry", "David").

synergy_pair("Programming", "DevOps").
synergy_pair("DevOps", "Programming").
synergy_pair("Design", "DataScience").
synergy_pair("DataScience", "Design").
synergy_pair("Management", "Testing").
synergy_pair("Testing", "Management").
synergy_pair("Security", "Cloud").
synergy_pair("Cloud", "Security").

primary_skill("Programming").
primary_skill("Design").
primary_skill("Testing").
primary_skill("Management").
primary_skill("DataScience").
primary_skill("DevOps").

team(1).
team(2).
team(3).

1 { in_team(P, T) : team(T) } 1 :- person(P, _).

1 { team_project(T, Proj) : project(Proj) } 1 :- team(T).

:- project(Proj), #count { T : team_project(T, Proj) } != 1.

1 { leads(P, T) : person(P, "Senior") } 1 :- team(T).

:- team(T), #count { P : in_team(P, T) } != 4.

:- leads(P, T), not in_team(P, T).

:- in_team(P1, T), in_team(P2, T), incompatible(P1, P2).

:- team_project(T, Proj), project_requires(Proj, Skill),
   #count { P : in_team(P, T), has_skill(P, Skill) } = 0.

leader_primary_skill(P, Skill) :- 
    leads(P, _), 
    has_skill(P, Skill), 
    primary_skill(Skill),
    not has_lower_primary(P, Skill).

has_lower_primary(P, Skill) :- 
    has_skill(P, Skill), 
    has_skill(P, Skill2),
    primary_skill(Skill),
    primary_skill(Skill2),
    Skill2 < Skill.

:- leads(P1, T1), leads(P2, T2), T1 != T2,
   leader_primary_skill(P1, Skill),
   leader_primary_skill(P2, Skill).

team_has_synergy(T, S1, S2) :- 
    team(T),
    synergy_pair(S1, S2),
    S1 < S2,
    in_team(P1, T), has_skill(P1, S1),
    in_team(P2, T), has_skill(P2, S2).

team_synergy(T, Count) :- 
    team(T),
    Count = #count { S1, S2 : team_has_synergy(T, S1, S2) }.

total_synergy(Total) :- Total = #sum { Count, T : team_synergy(T, Count) }.

:- total_synergy(Total), Total < 11.

#show in_team/2.
#show leads/2.
#show team_project/2.
#show team_synergy/2.
#show total_synergy/1.
"""

ctl = clingo.Control(["1"])
ctl.add("base", [], asp_program)
ctl.ground([("base", [])])

solution_data = None

def on_model(model):
    global solution_data
    atoms = model.symbols(atoms=True)
    
    assignments = {}
    leaders = {}
    projects = {}
    team_synergies = {}
    total_syn = 0
    
    for atom in atoms:
        if atom.name == "in_team" and len(atom.arguments) == 2:
            person = str(atom.arguments[0]).strip('"')
            team = atom.arguments[1].number
            if team not in assignments:
                assignments[team] = []
            assignments[team].append(person)
        
        elif atom.name == "leads" and len(atom.arguments) == 2:
            person = str(atom.arguments[0]).strip('"')
            team = atom.arguments[1].number
            leaders[team] = person
        
        elif atom.name == "team_project" and len(atom.arguments) == 2:
            team = atom.arguments[0].number
            project = str(atom.arguments[1]).strip('"')
            projects[team] = project
        
        elif atom.name == "team_synergy" and len(atom.arguments) == 2:
            team = atom.arguments[0].number
            synergy = atom.arguments[1].number
            team_synergies[team] = synergy
        
        elif atom.name == "total_synergy" and len(atom.arguments) == 1:
            total_syn = atom.arguments[0].number
    
    solution_data = {
        'assignments': assignments,
        'leaders': leaders,
        'projects': projects,
        'team_synergies': team_synergies,
        'total_synergy': total_syn
    }

result = ctl.solve(on_model=on_model)

if result.satisfiable:
    output = {
        "teams": []
    }
    
    for team_id in sorted(solution_data['assignments'].keys()):
        team_obj = {
            "team_id": team_id,
            "project": solution_data['projects'][team_id],
            "leader": solution_data['leaders'][team_id],
            "members": sorted(solution_data['assignments'][team_id]),
            "synergy_score": solution_data['team_synergies'][team_id]
        }
        output["teams"].append(team_obj)
    
    output["total_synergy"] = solution_data['total_synergy']
    
    print(json.dumps(output, indent=2))
else:
    error_output = {
        "error": "No solution exists",
        "reason": "Could not satisfy all constraints with the given data"
    }
    print(json.dumps(error_output, indent=2))
