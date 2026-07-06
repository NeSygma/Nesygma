# SOLUTIONS RESULTS - EASY LEVEL

## PROBLEM 01 - 01_who_is_the_killer_easy_solution.py

- Runtime: 0.09s
- Status: SUCCESS

```json
{
  "killer": 0,
  "killer_name": "Agatha"
}
```

## PROBLEM 02 - 02_graph_coloring_easy_solution.py

- Runtime: 0.09s
- Status: SUCCESS

```json
{
  "num_colors": 3,
  "coloring": [
    {
      "vertex": 1,
      "color": 3
    },
    {
      "vertex": 2,
      "color": 1
    },
    {
      "vertex": 3,
      "color": 2
    },
    {
      "vertex": 4,
      "color": 3
    },
    {
      "vertex": 5,
      "color": 1
    },
    {
      "vertex": 6,
      "color": 2
    }
  ]
}
```

## PROBLEM 03 - 03_knights_knaves_easy_solution.py

- Runtime: 0.08s
- Status: SUCCESS

```json
{
  "bob": "knight",
  "alice": "knave",
  "charlie": "knave"
}
```

## PROBLEM 04 - 04_blocks_world_easy_solution.py

- Runtime: 0.09s
- Status: SUCCESS

```json
{
  "plan_length": 3,
  "actions": [
    {
      "step": 1,
      "action": "move",
      "block": "C",
      "from": "A",
      "to": "table"
    },
    {
      "step": 2,
      "action": "move",
      "block": "B",
      "from": "table",
      "to": "C"
    },
    {
      "step": 3,
      "action": "move",
      "block": "A",
      "from": "table",
      "to": "B"
    }
  ]
}
```

## PROBLEM 05 - 05_circuit_diagnosis_easy_solution.py

- Runtime: 0.08s
- Status: SUCCESS

```json
{
  "diagnoses": [
    {
      "components": [
        "or1"
      ],
      "minimal": true
    },
    {
      "components": [
        "notgate1"
      ],
      "minimal": true
    }
  ],
  "explanation": "Each diagnosis represents a minimal set of components that, if faulty, would explain the observed discrepancy."
}
```

## PROBLEM 06 - 06_stable_marriage_extended_easy_solution.py

- Runtime: 0.08s
- Status: SUCCESS

```json
{
  "stable_matchings": [
    [
      [
        "m1",
        "w2"
      ],
      [
        "m2",
        "w3"
      ],
      [
        "m3",
        "w4"
      ],
      [
        "m4",
        "w1"
      ]
    ],
    [
      [
        "m1",
        "w1"
      ],
      [
        "m2",
        "w2"
      ],
      [
        "m3",
        "w3"
      ],
      [
        "m4",
        "w4"
      ]
    ]
  ],
  "count": 2
}
```

## PROBLEM 07 - 07_hamiltonian_path_easy_solution.py

- Runtime: 0.08s
- Status: SUCCESS

```json
{
  "paths": [
    [
      0,
      2,
      1,
      3,
      4,
      5
    ],
    [
      0,
      2,
      1,
      4,
      3,
      5
    ],
    [
      0,
      1,
      2,
      3,
      4,
      5
    ],
    [
      0,
      1,
      2,
      4,
      3,
      5
    ]
  ],
  "count": 4,
  "exists": true
}
```

## PROBLEM 08 - 08_meeting_scheduling_easy_solution.py

- Runtime: 0.08s
- Status: SUCCESS

```json
{
  "schedule": [
    {
      "meeting": "m1",
      "day": 1,
      "slot": 1,
      "room": "r1"
    },
    {
      "meeting": "m2",
      "day": 1,
      "slot": 2,
      "room": "r2"
    },
    {
      "meeting": "m3",
      "day": 2,
      "slot": 3,
      "room": "r2"
    },
    {
      "meeting": "m5",
      "day": 3,
      "slot": 1,
      "room": "r1"
    },
    {
      "meeting": "m4",
      "day": 3,
      "slot": 3,
      "room": "r2"
    }
  ],
  "conflicts": [],
  "preference_violations": 0,
  "feasible": true
}
```

## PROBLEM 09 - 09_nonogram_solver_easy_solution.py

- Runtime: 0.08s
- Status: SUCCESS

```json
{
  "grid": [
    [
      1,
      1,
      0,
      0,
      0
    ],
    [
      0,
      0,
      1,
      0,
      0
    ],
    [
      0,
      1,
      1,
      1,
      0
    ],
    [
      0,
      1,
      0,
      0,
      1
    ],
    [
      1,
      1,
      0,
      0,
      0
    ]
  ],
  "valid": true
}
```

## PROBLEM 10 - 10_facility_location_easy_solution.py

- Runtime: 0.09s
- Status: SUCCESS

```json
{
  "facilities": [
    "A",
    "C",
    "D"
  ],
  "assignments": {
    "1": "A",
    "2": "A",
    "3": "A",
    "4": "D",
    "5": "C",
    "6": "C",
    "7": "D",
    "8": "C"
  },
  "total_cost": 380,
  "feasible": true
}
```

## PROBLEM 11 - 11_tournament_ranking_easy_solution.py

- Runtime: 0.09s
- Status: SUCCESS

```json
{
  "ranking": [
    "A",
    "B",
    "D",
    "E",
    "C"
  ],
  "violations": 1,
  "valid": true
}
```

## PROBLEM 12 - 12_zebra_puzzle_easy_solution.py

- Runtime: 0.08s
- Status: SUCCESS

```json
{
  "solution": [
    {
      "house": 1,
      "color": "Yellow",
      "nationality": "Norwegian",
      "drink": "Water",
      "cigarette": "Dunhill",
      "pet": "Cats"
    },
    {
      "house": 2,
      "color": "Blue",
      "nationality": "Dane",
      "drink": "Tea",
      "cigarette": "Blends",
      "pet": "Horse"
    },
    {
      "house": 3,
      "color": "Red",
      "nationality": "Brit",
      "drink": "Milk",
      "cigarette": "Pall Mall",
      "pet": "Birds"
    },
    {
      "house": 4,
      "color": "Green",
      "nationality": "German",
      "drink": "Coffee",
      "cigarette": "Prince",
      "pet": "Zebra"
    },
    {
      "house": 5,
      "color": "White",
      "nationality": "Swede",
      "drink": "Beer",
      "cigarette": "Blue Master",
      "pet": "Dog"
    }
  ],
  "zebra_owner": "German"
}
```

## PROBLEM 13 - 13_job_shop_scheduling_easy_solution.py

- Runtime: 0.11s
- Status: SUCCESS

```json
{
  "schedule": [
    {
      "job": 1,
      "operation": 1,
      "machine": 1,
      "start": 0,
      "duration": 3
    },
    {
      "job": 1,
      "operation": 2,
      "machine": 2,
      "start": 4,
      "duration": 2
    },
    {
      "job": 1,
      "operation": 3,
      "machine": 3,
      "start": 6,
      "duration": 4
    },
    {
      "job": 2,
      "operation": 1,
      "machine": 2,
      "start": 0,
      "duration": 2
    },
    {
      "job": 2,
      "operation": 2,
      "machine": 1,
      "start": 5,
      "duration": 5
    },
    {
      "job": 2,
      "operation": 3,
      "machine": 3,
      "start": 10,
      "duration": 1
    },
    {
      "job": 3,
      "operation": 1,
      "machine": 3,
      "start": 0,
      "duration": 4
    },
    {
      "job": 3,
      "operation": 2,
      "machine": 1,
      "start": 4,
      "duration": 1
    },
    {
      "job": 3,
      "operation": 3,
      "machine": 2,
      "start": 8,
      "duration": 3
    }
  ],
  "makespan": 11,
  "feasible": true
}
```

## PROBLEM 14 - 14_cryptarithmetic_easy_solution.py

- Runtime: 0.09s
- Status: SUCCESS

```json
{
  "assignment": {
    "S": 9,
    "E": 5,
    "N": 6,
    "D": 7,
    "M": 1,
    "O": 0,
    "R": 8,
    "Y": 2
  },
  "equation": "SEND + MORE = MONEY becomes 9567 + 1085 = 10652",
  "valid": true
}
```

## PROBLEM 15 - 15_traveling_tournament_easy_solution.py

- Runtime: 0.59s
- Status: SUCCESS

```json
{
  "schedule": [
    [
      {
        "home": "A",
        "away": "C"
      },
      {
        "home": "B",
        "away": "D"
      }
    ],
    [
      {
        "home": "D",
        "away": "A"
      },
      {
        "home": "C",
        "away": "B"
      }
    ],
    [
      {
        "home": "B",
        "away": "A"
      },
      {
        "home": "D",
        "away": "C"
      }
    ],
    [
      {
        "home": "A",
        "away": "D"
      },
      {
        "home": "B",
        "away": "C"
      }
    ],
    [
      {
        "home": "C",
        "away": "A"
      },
      {
        "home": "D",
        "away": "B"
      }
    ],
    [
      {
        "home": "A",
        "away": "B"
      },
      {
        "home": "C",
        "away": "D"
      }
    ]
  ],
  "total_distance": 74.6,
  "feasible": true
}
```

## PROBLEM 16 - 16_nurse_rostering_easy_solution.py

- Runtime: 0.09s
- Status: SUCCESS

```json
{
  "roster": [
    [
      [
        2,
        3
      ],
      [
        4
      ],
      [
        1
      ]
    ],
    [
      [
        2,
        3
      ],
      [
        4
      ],
      [
        1
      ]
    ],
    [
      [
        2,
        3
      ],
      [
        1
      ],
      [
        4
      ]
    ],
    [
      [
        2,
        3
      ],
      [
        1
      ],
      [
        4
      ]
    ],
    [
      [
        1,
        3
      ],
      [
        4
      ],
      [
        2
      ]
    ],
    [
      [
        3,
        4
      ],
      [
        1
      ],
      [
        2
      ]
    ],
    [
      [
        3,
        4
      ],
      [
        2
      ],
      [
        1
      ]
    ]
  ],
  "violations": 16,
  "coverage_met": true
}
```

## PROBLEM 17 - 17_bin_packing_easy_solution.py

- Runtime: 0.08s
- Status: SUCCESS

```json
{
  "bins": [
    {
      "bin_id": 1,
      "items": [
        1,
        2
      ],
      "total_size": 10
    },
    {
      "bin_id": 2,
      "items": [
        7,
        8
      ],
      "total_size": 7
    },
    {
      "bin_id": 3,
      "items": [
        3,
        4,
        6,
        9
      ],
      "total_size": 10
    },
    {
      "bin_id": 4,
      "items": [
        5
      ],
      "total_size": 7
    }
  ],
  "num_bins": 4,
  "feasible": true
}
```

## PROBLEM 18 - 18_magic_square_easy_solution.py

- Runtime: 0.08s
- Status: SUCCESS

```json
{
  "square": [
    [
      8,
      3,
      4
    ],
    [
      1,
      5,
      9
    ],
    [
      6,
      7,
      2
    ]
  ],
  "magic_sum": 15,
  "valid": true
}
```

## PROBLEM 19 - 19_course_timetabling_easy_solution.py

- Runtime: 0.08s
- Status: SUCCESS

```json
{
  "assignments": [
    {
      "course": 0,
      "room": 1,
      "time_slot": 0
    },
    {
      "course": 1,
      "room": 2,
      "time_slot": 1
    },
    {
      "course": 2,
      "room": 0,
      "time_slot": 0
    },
    {
      "course": 3,
      "room": 2,
      "time_slot": 3
    },
    {
      "course": 4,
      "room": 0,
      "time_slot": 1
    }
  ]
}
```

## PROBLEM 20 - 20_set_cover_easy_solution.py

- Runtime: 0.08s
- Status: SUCCESS

```json
{
  "selected_sets": [
    1,
    2,
    3
  ],
  "total_sets": 3,
  "covered_elements": [
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8
  ]
}
```

## PROBLEM 21 - 21_vertex_cover_easy_solution.py

- Runtime: 0.08s
- Status: SUCCESS

```json
{
  "vertex_cover": [
    1,
    2,
    5
  ],
  "cover_size": 3,
  "covered_edges": [
    [
      0,
      1
    ],
    [
      0,
      2
    ],
    [
      1,
      3
    ],
    [
      1,
      5
    ],
    [
      2,
      3
    ],
    [
      2,
      4
    ],
    [
      3,
      5
    ],
    [
      4,
      5
    ]
  ]
}
```

## PROBLEM 22 - 22_clique_finding_easy_solution.py

- Runtime: 0.09s
- Status: SUCCESS

```json
{
  "clique": [
    0,
    1,
    2,
    3
  ],
  "clique_size": 4,
  "clique_edges": [
    [
      0,
      1
    ],
    [
      0,
      2
    ],
    [
      0,
      3
    ],
    [
      1,
      2
    ],
    [
      1,
      3
    ],
    [
      2,
      3
    ]
  ]
}
```

## PROBLEM 23 - 23_resource_allocation_easy_solution.py

- Runtime: 0.08s
- Status: SUCCESS

```json
{
  "selected_tasks": [
    0,
    2,
    4
  ],
  "total_value": 180,
  "resource_usage": {
    "resource_c": 55,
    "resource_b": 60,
    "resource_a": 90
  }
}
```

## PROBLEM 24 - 24_workflow_optimization_easy_solution.py

- Runtime: 0.09s
- Status: SUCCESS

```json
{
  "schedule": [
    {
      "task": 0,
      "start_time": 0,
      "end_time": 3
    },
    {
      "task": 1,
      "start_time": 1,
      "end_time": 3
    },
    {
      "task": 2,
      "start_time": 3,
      "end_time": 7
    },
    {
      "task": 3,
      "start_time": 4,
      "end_time": 5
    },
    {
      "task": 4,
      "start_time": 7,
      "end_time": 12
    },
    {
      "task": 5,
      "start_time": 12,
      "end_time": 14
    },
    {
      "task": 6,
      "start_time": 12,
      "end_time": 15
    },
    {
      "task": 7,
      "start_time": 15,
      "end_time": 17
    }
  ],
  "makespan": 17,
  "critical_path": [
    0,
    2,
    4,
    6,
    7
  ]
}
```

## PROBLEM 25 - 25_sudoku_full_easy_solution.py

- Runtime: 0.09s
- Status: SUCCESS

```json
{
  "grid": [
    [
      5,
      3,
      4,
      6,
      7,
      8,
      9,
      1,
      2
    ],
    [
      6,
      7,
      2,
      1,
      9,
      5,
      3,
      4,
      8
    ],
    [
      1,
      9,
      8,
      3,
      4,
      2,
      5,
      6,
      7
    ],
    [
      8,
      5,
      9,
      7,
      6,
      1,
      4,
      2,
      3
    ],
    [
      4,
      2,
      6,
      8,
      5,
      3,
      7,
      9,
      1
    ],
    [
      7,
      1,
      3,
      9,
      2,
      4,
      8,
      5,
      6
    ],
    [
      9,
      6,
      1,
      5,
      3,
      7,
      2,
      8,
      4
    ],
    [
      2,
      8,
      7,
      4,
      1,
      9,
      6,
      3,
      5
    ],
    [
      3,
      4,
      5,
      2,
      8,
      6,
      1,
      7,
      9
    ]
  ],
  "is_valid": true,
  "clues_preserved": true
}
```

## PROBLEM 26 - 26_tower_of_hanoi_easy_solution.py

- Runtime: 0.12s
- Status: SUCCESS

```json
{
  "moves": [
    {
      "step": 1,
      "disk": 1,
      "from_peg": "A",
      "to_peg": "B"
    },
    {
      "step": 2,
      "disk": 2,
      "from_peg": "A",
      "to_peg": "C"
    },
    {
      "step": 3,
      "disk": 1,
      "from_peg": "B",
      "to_peg": "C"
    },
    {
      "step": 4,
      "disk": 3,
      "from_peg": "A",
      "to_peg": "B"
    },
    {
      "step": 5,
      "disk": 1,
      "from_peg": "C",
      "to_peg": "A"
    },
    {
      "step": 6,
      "disk": 2,
      "from_peg": "C",
      "to_peg": "B"
    },
    {
      "step": 7,
      "disk": 1,
      "from_peg": "A",
      "to_peg": "B"
    },
    {
      "step": 8,
      "disk": 4,
      "from_peg": "A",
      "to_peg": "C"
    },
    {
      "step": 9,
      "disk": 1,
      "from_peg": "B",
      "to_peg": "C"
    },
    {
      "step": 10,
      "disk": 2,
      "from_peg": "B",
      "to_peg": "A"
    },
    {
      "step": 11,
      "disk": 1,
      "from_peg": "C",
      "to_peg": "A"
    },
    {
      "step": 12,
      "disk": 3,
      "from_peg": "B",
      "to_peg": "C"
    },
    {
      "step": 13,
      "disk": 1,
      "from_peg": "A",
      "to_peg": "B"
    },
    {
      "step": 14,
      "disk": 2,
      "from_peg": "A",
      "to_peg": "C"
    },
    {
      "step": 15,
      "disk": 1,
      "from_peg": "B",
      "to_peg": "C"
    }
  ],
  "total_moves": 15,
  "is_optimal": true
}
```

## PROBLEM 27 - 27_queens_domination_easy_solution.py

- Runtime: 0.09s
- Status: SUCCESS

```json
{
  "queens": [
    [
      0,
      4
    ],
    [
      4,
      3
    ],
    [
      4,
      5
    ],
    [
      6,
      0
    ],
    [
      7,
      7
    ]
  ],
  "num_queens": 5,
  "dominated_squares": [
    [
      0,
      0
    ],
    [
      0,
      1
    ],
    [
      0,
      2
    ],
    [
      0,
      3
    ],
    [
      0,
      4
    ],
    [
      0,
      5
    ],
    [
      0,
      6
    ],
    [
      0,
      7
    ],
    [
      1,
      0
    ],
    [
      1,
      1
    ],
    [
      1,
      2
    ],
    [
      1,
      3
    ],
    [
      1,
      4
    ],
    [
      1,
      5
    ],
    [
      1,
      6
    ],
    [
      1,
      7
    ],
    [
      2,
      0
    ],
    [
      2,
      1
    ],
    [
      2,
      2
    ],
    [
      2,
      3
    ],
    [
      2,
      4
    ],
    [
      2,
      5
    ],
    [
      2,
      6
    ],
    [
      2,
      7
    ],
    [
      3,
      0
    ],
    [
      3,
      1
    ],
    [
      3,
      2
    ],
    [
      3,
      3
    ],
    [
      3,
      4
    ],
    [
      3,
      5
    ],
    [
      3,
      6
    ],
    [
      3,
      7
    ],
    [
      4,
      0
    ],
    [
      4,
      1
    ],
    [
      4,
      2
    ],
    [
      4,
      3
    ],
    [
      4,
      4
    ],
    [
      4,
      5
    ],
    [
      4,
      6
    ],
    [
      4,
      7
    ],
    [
      5,
      0
    ],
    [
      5,
      1
    ],
    [
      5,
      2
    ],
    [
      5,
      3
    ],
    [
      5,
      4
    ],
    [
      5,
      5
    ],
    [
      5,
      6
    ],
    [
      5,
      7
    ],
    [
      6,
      0
    ],
    [
      6,
      1
    ],
    [
      6,
      2
    ],
    [
      6,
      3
    ],
    [
      6,
      4
    ],
    [
      6,
      5
    ],
    [
      6,
      6
    ],
    [
      6,
      7
    ],
    [
      7,
      0
    ],
    [
      7,
      1
    ],
    [
      7,
      2
    ],
    [
      7,
      3
    ],
    [
      7,
      4
    ],
    [
      7,
      5
    ],
    [
      7,
      6
    ],
    [
      7,
      7
    ]
  ]
}
```

## PROBLEM 28 - 28_graph_isomorphism_easy_solution.py

- Runtime: 0.08s
- Status: SUCCESS

```json
{
  "is_isomorphic": true,
  "mapping": {
    "4": "a",
    "3": "b",
    "2": "c",
    "1": "d",
    "0": "e"
  },
  "preserved_edges": [
    [
      "0,1",
      "e,d"
    ],
    [
      "0,2",
      "e,c"
    ],
    [
      "1,3",
      "d,b"
    ],
    [
      "2,4",
      "c,a"
    ],
    [
      "3,4",
      "b,a"
    ]
  ]
}
```

## PROBLEM 29 - 29_logic_grid_puzzle_easy_solution.py

- Runtime: 0.08s
- Status: SUCCESS

```json
{
  "assignments": [
    {
      "person": "Alice",
      "color": "Yellow",
      "pet": "Fish",
      "house": 1
    },
    {
      "person": "Bob",
      "color": "Red",
      "pet": "Cat",
      "house": 2
    },
    {
      "person": "Carol",
      "color": "Blue",
      "pet": "Bird",
      "house": 3
    },
    {
      "person": "Dave",
      "color": "Green",
      "pet": "Dog",
      "house": 4
    }
  ]
}
```

## PROBLEM 30 - 30_team_formation_easy_solution.py

- Runtime: 0.09s
- Status: SUCCESS

```json
{
  "teams": [
    [
      "Eve",
      "Frank",
      "Grace",
      "Henry"
    ],
    [
      "Alice",
      "Bob",
      "Carol",
      "Dave"
    ]
  ]
}
```

## PROBLEM 31 - 31_network_flow_easy_solution.py

- Runtime: 0.10s
- Status: SUCCESS

```json
{
  "max_flow": 14,
  "flows": [
    {
      "from": 1,
      "to": 2,
      "flow": 9
    },
    {
      "from": 1,
      "to": 3,
      "flow": 5
    },
    {
      "from": 2,
      "to": 3,
      "flow": 3
    },
    {
      "from": 2,
      "to": 4,
      "flow": 6
    },
    {
      "from": 3,
      "to": 4,
      "flow": 2
    },
    {
      "from": 3,
      "to": 5,
      "flow": 6
    },
    {
      "from": 4,
      "to": 6,
      "flow": 8
    },
    {
      "from": 5,
      "to": 6,
      "flow": 6
    }
  ]
}
```

## PROBLEM 32 - 32_frequency_assignment_easy_solution.py

- Runtime: 0.08s
- Status: SUCCESS

```json
{
  "assignments": [
    {
      "transmitter": "A",
      "frequency": 1
    },
    {
      "transmitter": "B",
      "frequency": 5
    },
    {
      "transmitter": "C",
      "frequency": 5
    },
    {
      "transmitter": "D",
      "frequency": 1
    },
    {
      "transmitter": "E",
      "frequency": 3
    },
    {
      "transmitter": "F",
      "frequency": 1
    }
  ],
  "frequencies_used": 3
}
```

## PROBLEM 33 - 33_independent_set_easy_solution.py

- Runtime: 0.08s
- Status: SUCCESS

```json
{
  "independent_set": [
    2,
    4,
    7
  ],
  "size": 3
}
```

## PROBLEM 34 - 34_dominating_set_easy_solution.py

- Runtime: 0.08s
- Status: SUCCESS

```json
{
  "dominating_set": [
    1,
    6
  ],
  "size": 2
}
```

## PROBLEM 35 - 35_feedback_vertex_set_easy_solution.py

- Runtime: 0.08s
- Status: SUCCESS

```json
{
  "feedback_set": [
    1,
    4
  ],
  "size": 2,
  "remaining_vertices": [
    2,
    3,
    5,
    6
  ]
}
```

## PROBLEM 36 - 36_latin_square_easy_solution.py

- Runtime: 0.09s
- Status: SUCCESS

```json
{
  "grid": [
    [
      1,
      4,
      2,
      5,
      3
    ],
    [
      4,
      5,
      3,
      1,
      2
    ],
    [
      2,
      3,
      5,
      4,
      1
    ],
    [
      3,
      1,
      4,
      2,
      5
    ],
    [
      5,
      2,
      1,
      3,
      4
    ]
  ],
  "solved": true
}
```

## PROBLEM 37 - 37_car_sequencing_easy_solution.py

- Runtime: 0.08s
- Status: SUCCESS

```json
{
  "sequence": [
    "B",
    "C",
    "C",
    "B",
    "C",
    "A"
  ],
  "length": 6
}
```

## PROBLEM 38 - 38_protein_structure_easy_solution.py

- Runtime: 0.14s
- Status: SUCCESS

```json
{
  "coordinates": [
    [
      3,
      2
    ],
    [
      4,
      2
    ],
    [
      4,
      3
    ],
    [
      3,
      3
    ],
    [
      3,
      4
    ],
    [
      2,
      4
    ],
    [
      2,
      3
    ],
    [
      2,
      2
    ]
  ],
  "sequence": "HPPHPPHH"
}
```

## PROBLEM 39 - 39_byzantine_generals_easy_solution.py

- Runtime: 0.10s
- Status: SUCCESS

```json
{
  "consensus": 1,
  "honest_generals": [
    "G1",
    "G2",
    "G3"
  ],
  "traitor": "G4"
}
```

## PROBLEM 40 - 40_warehouse_location_easy_solution.py

- Runtime: 0.18s
- Status: SUCCESS

```json
{
  "selected_warehouses": [
    "W1",
    "W2",
    "W3"
  ],
  "assignments": {
    "C1": "W1",
    "C6": "W1",
    "C2": "W2",
    "C4": "W2",
    "C5": "W2",
    "C3": "W3"
  },
  "total_cost": 1625
}
```

## PROBLEM 41 - 41_argumentation_framework_easy_solution.py

- Runtime: 0.09s
- Status: SUCCESS

```json
{
  "stable_extensions": [
    [
      "a",
      "c",
      "e"
    ]
  ]
}
```

## PROBLEM 42 - 42_gene_regulatory_network_easy_solution.py

- Runtime: 0.08s
- Status: SUCCESS

```json
{
  "steady_states": [
    {
      "g2": 1,
      "g3": 1,
      "g4": 1,
      "g5": 1,
      "g1": 0
    },
    {
      "g1": 1,
      "g3": 1,
      "g4": 1,
      "g5": 1,
      "g2": 0
    }
  ]
}
```

## PROBLEM 43 - 43_quantum_circuit_easy_solution.py

- Runtime: 0.08s
- Status: SUCCESS

```json
{
  "circuit_depth": 3,
  "gate_schedule": [
    {
      "time": 1,
      "gates": [
        "cnot_q0_q1"
      ]
    },
    {
      "time": 2,
      "gates": [
        "cnot_q0_q3",
        "cnot_q1_q2"
      ]
    },
    {
      "time": 3,
      "gates": [
        "h_q0",
        "h_q1",
        "x_q2"
      ]
    }
  ]
}
```

## PROBLEM 44 - 44_nontransitive_dice_easy_solution.py

- Runtime: 98.37s
- Status: SUCCESS

```json
{
  "dice": {
    "A": [
      3,
      4,
      3,
      3,
      3,
      6
    ],
    "B": [
      2,
      6,
      6,
      5,
      1,
      2
    ],
    "C": [
      0,
      4,
      5,
      5,
      6,
      0
    ]
  },
  "win_probabilities": {
    "A_beats_B": 0.5277777777777778,
    "B_beats_C": 0.5277777777777778,
    "C_beats_A": 0.5277777777777778
  }
}
```

## PROBLEM 45 - 45_prisoners_dilemma_easy_solution.py

- Runtime: 0.11s
- Status: SUCCESS

```json
{
  "tournament_results": [
    {
      "strategy": "TFT",
      "total_score": 1218
    },
    {
      "strategy": "GTFT",
      "total_score": 1189
    },
    {
      "strategy": "RAND",
      "total_score": 1170
    },
    {
      "strategy": "DEFECT",
      "total_score": 1148
    },
    {
      "strategy": "COOP",
      "total_score": 1053
    }
  ],
  "winner": "TFT"
}
```

## PROBLEM 46 - 46_metroidvania_generation_easy_solution.py

- Runtime: 0.10s
- Status: SUCCESS

```json
{
  "rooms": [
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H"
  ],
  "connections": [
    {
      "from": "A",
      "to": "B",
      "requires": "key1"
    },
    {
      "from": "A",
      "to": "D",
      "requires": "key1"
    },
    {
      "from": "A",
      "to": "G",
      "requires": "key1"
    },
    {
      "from": "A",
      "to": "H",
      "requires": "key1"
    },
    {
      "from": "E",
      "to": "A",
      "requires": "key3"
    },
    {
      "from": "A",
      "to": "C",
      "requires": "key3"
    },
    {
      "from": "A",
      "to": "E",
      "requires": "key3"
    },
    {
      "from": "A",
      "to": "F",
      "requires": "key3"
    }
  ],
  "item_locations": {
    "key1": "A",
    "key2": "B",
    "key3": "A"
  },
  "reachability_verified": true
}
```

## PROBLEM 47 - 47_dna_sequence_assembly_easy_solution.py

- Runtime: 0.10s
- Status: SUCCESS

```json
{
  "fragments": [
    "ATCGATCG",
    "CGATCGTA",
    "ATCGTAAC",
    "CGTAACGG",
    "TAACGGCT",
    "ACGGCTGA",
    "GGCTGAAA",
    "CTGAAATC"
  ],
  "consensus_sequence": "ATCGTAACGGCTGAAATCGATCGTA",
  "assembly_path": [
    2,
    3,
    4,
    5,
    6,
    7,
    0,
    1
  ],
  "overlap_details": [
    {
      "fragment1": 2,
      "fragment2": 3,
      "overlap_length": 6,
      "position1": 2,
      "position2": 0
    },
    {
      "fragment1": 3,
      "fragment2": 4,
      "overlap_length": 6,
      "position1": 2,
      "position2": 0
    },
    {
      "fragment1": 4,
      "fragment2": 5,
      "overlap_length": 6,
      "position1": 2,
      "position2": 0
    },
    {
      "fragment1": 5,
      "fragment2": 6,
      "overlap_length": 6,
      "position1": 2,
      "position2": 0
    },
    {
      "fragment1": 6,
      "fragment2": 7,
      "overlap_length": 6,
      "position1": 2,
      "position2": 0
    },
    {
      "fragment1": 7,
      "fragment2": 0,
      "overlap_length": 3,
      "position1": 5,
      "position2": 0
    },
    {
      "fragment1": 0,
      "fragment2": 1,
      "overlap_length": 6,
      "position1": 2,
      "position2": 0
    }
  ]
}
```

## PROBLEM 48 - 48_crossword_generation_easy_solution.py

- Runtime: 0.14s
- Status: SUCCESS

```json
{
  "grid": [
    [
      " ",
      "T",
      "E",
      "C",
      "H"
    ],
    [
      "B",
      "C",
      " ",
      "O",
      "D"
    ],
    [
      "Y",
      "H",
      " ",
      "D",
      "A"
    ],
    [
      "T",
      "I",
      "N",
      "E",
      "T"
    ],
    [
      "E",
      "P",
      " ",
      " ",
      "A"
    ]
  ],
  "words": [
    {
      "word": "CODE",
      "position": [
        0,
        3
      ],
      "direction": "vertical",
      "clue": "Programming instructions"
    },
    {
      "word": "DATA",
      "position": [
        1,
        4
      ],
      "direction": "vertical",
      "clue": "Information"
    },
    {
      "word": "TECH",
      "position": [
        0,
        1
      ],
      "direction": "horizontal",
      "clue": "Technology short"
    },
    {
      "word": "CHIP",
      "position": [
        1,
        1
      ],
      "direction": "vertical",
      "clue": "Computer component"
    },
    {
      "word": "BYTE",
      "position": [
        1,
        0
      ],
      "direction": "vertical",
      "clue": "Data unit"
    },
    {
      "word": "NET",
      "position": [
        3,
        2
      ],
      "direction": "horizontal",
      "clue": "Internet short"
    }
  ],
  "theme": "Technology",
  "intersections": [
    {
      "word1": 0,
      "word2": 2,
      "position1": 0,
      "position2": 2,
      "letter": "C"
    },
    {
      "word1": 0,
      "word2": 5,
      "position1": 3,
      "position2": 1,
      "letter": "E"
    },
    {
      "word1": 1,
      "word2": 5,
      "position1": 2,
      "position2": 2,
      "letter": "T"
    }
  ]
}
```

## PROBLEM 49 - 49_auction_mechanism_easy_solution.py

- Runtime: 0.13s
- Status: SUCCESS

```json
{
  "winning_bids": [
    {
      "bidder": "A",
      "items": [
        "item1",
        "item2"
      ],
      "price": 100
    },
    {
      "bidder": "A",
      "items": [
        "item3"
      ],
      "price": 50
    },
    {
      "bidder": "B",
      "items": [
        "item4",
        "item5"
      ],
      "price": 80
    }
  ],
  "total_revenue": 230,
  "item_allocation": {
    "item1": "A",
    "item2": "A",
    "item3": "A",
    "item4": "B",
    "item5": "B"
  }
}
```

## PROBLEM 50 - 50_cellular_automata_easy_solution.py

- Runtime: 0.17s
- Status: SUCCESS

```json
{
  "stable_patterns": [
    {
      "pattern_id": 1,
      "period": 2,
      "states": [
        [
          [
            0,
            1,
            1,
            1,
            0
          ],
          [
            1,
            0,
            0,
            0,
            1
          ],
          [
            1,
            0,
            0,
            0,
            1
          ],
          [
            1,
            0,
            0,
            0,
            1
          ],
          [
            0,
            1,
            1,
            1,
            0
          ]
        ],
        [
          [
            0,
            1,
            1,
            1,
            0
          ],
          [
            1,
            0,
            1,
            0,
            1
          ],
          [
            1,
            1,
            0,
            1,
            1
          ],
          [
            1,
            0,
            1,
            0,
            1
          ],
          [
            0,
            1,
            1,
            1,
            0
          ]
        ]
      ]
    }
  ]
}
```

## PROBLEM 51 - 51_ricochet_robots_easy_solution.py

- Runtime: 0.65s
- Status: SUCCESS

```json
{
  "solution_found": true,
  "moves": 3,
  "sequence": [
    {
      "robot": "B",
      "from": [
        1,
        1
      ],
      "to": [
        1,
        0
      ]
    },
    {
      "robot": "A",
      "from": [
        0,
        1
      ],
      "to": [
        1,
        1
      ]
    },
    {
      "robot": "A",
      "from": [
        1,
        1
      ],
      "to": [
        2,
        1
      ]
    }
  ],
  "final_positions": {
    "B": [
      1,
      0
    ],
    "A": [
      2,
      1
    ]
  }
}
```

## PROBLEM 52 - 52_nim_game_easy_solution.py

- Runtime: 0.20s
- Status: SUCCESS

```json
{
  "game_state": "winning",
  "optimal_moves": [
    {
      "pile": 1,
      "stones": 2,
      "resulting_piles": [
        1,
        4,
        5
      ]
    }
  ],
  "nim_sum": 2,
  "analysis": {
    "is_winning_position": true,
    "strategy": "From a winning position (nim-sum \u2260 0), the optimal strategy is to make a move that reduces the nim-sum to 0, forcing the opponent into a losing position. The current nim-sum is 2 (binary: 0b10). To achieve nim-sum = 0, we need to remove stones from a pile such that the XOR of all remaining piles equals 0. This is done by removing 2 stones from pile 1, changing it from 3 to 1, resulting in piles [1, 4, 5] with nim-sum = 1 \u2295 4 \u2295 5 = 0.",
    "after_optimal_move": {
      "nim_sum": 0,
      "position": "losing"
    }
  }
}
```

## PROBLEM 53 - 53_steiner_tree_easy_solution.py

- Runtime: 0.21s
- Status: SUCCESS

```json
{
  "total_weight": 10,
  "tree_edges": [
    {
      "from": 0,
      "to": 1,
      "weight": 3
    },
    {
      "from": 1,
      "to": 3,
      "weight": 2
    },
    {
      "from": 3,
      "to": 5,
      "weight": 3
    },
    {
      "from": 3,
      "to": 6,
      "weight": 2
    }
  ],
  "steiner_vertices": [
    1,
    3
  ],
  "terminals": [
    0,
    5,
    6
  ],
  "connected_components": [
    {
      "component": 1,
      "vertices": [
        0,
        1,
        3,
        5,
        6
      ]
    }
  ]
}
```

## PROBLEM 54 - 54_graph_partitioning_easy_solution.py

- Runtime: 0.17s
- Status: SUCCESS

```json
{
  "partition_1": [
    0,
    1,
    4,
    5
  ],
  "partition_2": [
    2,
    3,
    6,
    7
  ],
  "cut_size": 3,
  "cut_edges": [
    {
      "from": 1,
      "to": 2
    },
    {
      "from": 4,
      "to": 6
    },
    {
      "from": 5,
      "to": 7
    }
  ],
  "balance": {
    "partition_1_size": 4,
    "partition_2_size": 4,
    "is_balanced": true
  }
}
```

## PROBLEM 55 - 55_recipe_planning_easy_solution.py

- Runtime: 13.20s
- Status: SUCCESS

```json
{
  "total_time": 35,
  "schedule": [
    {
      "recipe": "pasta",
      "step": "prep",
      "start_time": 0,
      "end_time": 10,
      "resources": [
        "prep_area"
      ]
    },
    {
      "recipe": "bread",
      "step": "bake",
      "start_time": 5,
      "end_time": 35,
      "resources": [
        "oven"
      ]
    },
    {
      "recipe": "salad",
      "step": "chop",
      "start_time": 10,
      "end_time": 25,
      "resources": [
        "prep_area"
      ]
    },
    {
      "recipe": "pasta",
      "step": "boil",
      "start_time": 14,
      "end_time": 29,
      "resources": [
        "stove"
      ]
    },
    {
      "recipe": "salad",
      "step": "mix",
      "start_time": 25,
      "end_time": 30,
      "resources": [
        "prep_area"
      ]
    },
    {
      "recipe": "pasta",
      "step": "serve",
      "start_time": 30,
      "end_time": 35,
      "resources": [
        "prep_area"
      ]
    }
  ],
  "resource_usage": {
    "oven": [
      {
        "start": 5,
        "end": 35,
        "recipe": "bread"
      }
    ],
    "stove": [
      {
        "start": 14,
        "end": 29,
        "recipe": "pasta"
      }
    ],
    "prep_area": [
      {
        "start": 0,
        "end": 10,
        "recipe": "pasta"
      },
      {
        "start": 10,
        "end": 25,
        "recipe": "salad"
      },
      {
        "start": 25,
        "end": 30,
        "recipe": "salad"
      },
      {
        "start": 30,
        "end": 35,
        "recipe": "pasta"
      }
    ]
  }
}
```

## PROBLEM 56 - 56_music_composition_easy_solution.py

- Runtime: 0.08s
- Status: SUCCESS

```json
{
  "melody": [
    "C",
    "C",
    "E",
    "F",
    "G",
    "E",
    "C",
    "C"
  ],
  "intervals": [
    0,
    4,
    1,
    2,
    -3,
    -4,
    0
  ],
  "analysis": {
    "key": "C_major",
    "total_steps": 8,
    "leap_count": 3,
    "direction_changes": 1,
    "final_resolution": true
  }
}
```

## PROBLEM 57 - 57_escape_room_design_easy_solution.py

- Runtime: 0.08s
- Status: SUCCESS

```json
{
  "puzzle_order": [
    1,
    4,
    2,
    3,
    5,
    6
  ],
  "difficulty_progression": [
    1,
    2,
    1,
    2,
    3,
    3
  ],
  "dependencies_satisfied": true,
  "puzzle_details": [
    {
      "puzzle_id": 1,
      "difficulty": 1,
      "prerequisites": []
    },
    {
      "puzzle_id": 2,
      "difficulty": 1,
      "prerequisites": [
        1
      ]
    },
    {
      "puzzle_id": 3,
      "difficulty": 2,
      "prerequisites": [
        2,
        4
      ]
    },
    {
      "puzzle_id": 4,
      "difficulty": 2,
      "prerequisites": [
        1
      ]
    },
    {
      "puzzle_id": 5,
      "difficulty": 3,
      "prerequisites": [
        3
      ]
    },
    {
      "puzzle_id": 6,
      "difficulty": 3,
      "prerequisites": [
        5
      ]
    }
  ]
}
```

## PROBLEM 58 - 58_exam_scheduling_easy_solution.py

- Runtime: 0.08s
- Status: SUCCESS

```json
{
  "schedule": [
    {
      "exam": "E1",
      "day": 1,
      "time_slot": 3,
      "room": "R1",
      "duration": 2
    },
    {
      "exam": "E2",
      "day": 1,
      "time_slot": 3,
      "room": "R1",
      "duration": 2
    },
    {
      "exam": "E3",
      "day": 1,
      "time_slot": 1,
      "room": "R1",
      "duration": 2
    },
    {
      "exam": "E4",
      "day": 1,
      "time_slot": 1,
      "room": "R2",
      "duration": 2
    },
    {
      "exam": "E5",
      "day": 1,
      "time_slot": 2,
      "room": "R2",
      "duration": 2
    },
    {
      "exam": "E6",
      "day": 1,
      "time_slot": 2,
      "room": "R1",
      "duration": 2
    }
  ],
  "conflicts_resolved": true,
  "room_utilization": {
    "R1": 4,
    "R2": 2
  }
}
```

## PROBLEM 59 - 59_strategic_voting_easy_solution.py

- Runtime: 0.08s
- Status: SUCCESS

```json
{
  "election_result": {
    "winner": "A",
    "vote_counts": {
      "A": 2,
      "B": 1,
      "C": 1
    },
    "total_votes": 4
  },
  "strategic_opportunities": [
    {
      "voter": "V3",
      "true_preference": [
        "B",
        "C",
        "A"
      ],
      "strategic_vote": "B",
      "manipulation_detected": true,
      "benefit": "With V1 or V2 cooperation, can elect preferred candidate B over A"
    },
    {
      "voter": "V4",
      "true_preference": [
        "C",
        "B",
        "A"
      ],
      "strategic_vote": "C",
      "manipulation_detected": true,
      "benefit": "With V1 or V2 cooperation, can elect preferred candidate C over A"
    },
    {
      "voter": "V3",
      "true_preference": [
        "B",
        "C",
        "A"
      ],
      "strategic_vote": "C",
      "manipulation_detected": true,
      "benefit": "With V1 or V2 cooperation, can elect second-choice C over A"
    }
  ],
  "is_manipulation_proof": false,
  "analysis": {
    "condorcet_winner": null,
    "strategic_voting_present": true,
    "voting_paradox": null,
    "min_coalition_size": 2
  }
}
```

## PROBLEM 60 - 60_ecosystem_balance_easy_solution.py

- Runtime: 0.70s
- Status: SUCCESS

```json
{
  "stable_populations": {
    "Grass": 100,
    "Rabbits": 30,
    "Foxes": 9,
    "Hawks": 5
  },
  "food_web": [
    {
      "predator": "Rabbits",
      "prey": "Grass",
      "consumption_rate": 0.2
    },
    {
      "predator": "Foxes",
      "prey": "Rabbits",
      "consumption_rate": 0.4
    },
    {
      "predator": "Hawks",
      "prey": "Rabbits",
      "consumption_rate": 0.1
    },
    {
      "predator": "Hawks",
      "prey": "Foxes",
      "consumption_rate": 0.3
    }
  ],
  "ecosystem_health": {
    "biodiversity_index": 0.628,
    "stability_score": 0.747,
    "sustainability": true
  },
  "balance_achieved": true
}
```

## PROBLEM 61 - 61_historical_counterfactual_easy_solution.py

- Runtime: 0.08s
- Status: SUCCESS

```json
{
  "original_timeline": [
    "discovery_of_america",
    "columbian_exchange",
    "spanish_empire",
    "industrial_revolution",
    "world_wars"
  ],
  "alternate_timeline": [],
  "prevented_events": [
    "discovery_of_america",
    "columbian_exchange",
    "spanish_empire",
    "industrial_revolution",
    "world_wars"
  ],
  "causal_analysis": {
    "direct_effects": [
      "columbian_exchange",
      "spanish_empire"
    ],
    "cascade_effects": [
      "industrial_revolution",
      "world_wars"
    ],
    "preserved_events": [],
    "intervention_events": [
      "discovery_of_america"
    ]
  }
}
```

## PROBLEM 62 - 62_drug_interaction_easy_solution.py

- Runtime: 0.08s
- Status: SUCCESS

```json
{
  "prescribed_drugs": [
    {
      "drug_id": "drug4",
      "dose": 1000,
      "frequency": "twice_daily"
    },
    {
      "drug_id": "drug5",
      "dose": 1200,
      "frequency": "twice_daily"
    }
  ],
  "treated_conditions": [
    "diabetes",
    "pain"
  ],
  "untreated_conditions": [
    "hypertension"
  ],
  "safety_analysis": {
    "interactions_detected": [],
    "contraindications_avoided": [
      "bleeding_disorder"
    ],
    "safety_score": 0.83
  }
}
```

## PROBLEM 63 - 63_dungeon_generation_easy_solution.py

- Runtime: 0.09s
- Status: SUCCESS

```json
{
  "room_layout": [
    {
      "room_id": "room1",
      "monsters": [],
      "treasures": [
        "treasure1",
        "treasure2"
      ],
      "danger_level": 0
    },
    {
      "room_id": "room2",
      "monsters": [],
      "treasures": [],
      "danger_level": 0
    },
    {
      "room_id": "room3",
      "monsters": [
        {
          "type": "orc",
          "count": 1
        }
      ],
      "treasures": [],
      "danger_level": 4
    },
    {
      "room_id": "room4",
      "monsters": [],
      "treasures": [],
      "danger_level": 0
    },
    {
      "room_id": "room5",
      "monsters": [],
      "treasures": [],
      "danger_level": 0
    },
    {
      "room_id": "room6",
      "monsters": [
        {
          "type": "goblin",
          "count": 1
        },
        {
          "type": "orc",
          "count": 1
        }
      ],
      "treasures": [
        "treasure3"
      ],
      "danger_level": 6
    },
    {
      "room_id": "room7",
      "monsters": [],
      "treasures": [],
      "danger_level": 0
    }
  ],
  "connectivity": {
    "paths": [
      {
        "from": "room1",
        "to": "room7",
        "route": [
          "room1",
          "room3",
          "room5",
          "room7"
        ],
        "total_danger": 4,
        "treasures_found": [
          "treasure1",
          "treasure2"
        ]
      }
    ],
    "isolated_rooms": []
  },
  "balance_analysis": {
    "total_danger": 10,
    "treasure_distribution": {
      "common": 1,
      "rare": 1,
      "legendary": 1
    },
    "difficulty_progression": "easy"
  }
}
```

## PROBLEM 64 - 64_social_network_influence_easy_solution.py

- Runtime: 0.07s
- Status: SUCCESS

```json
{
  "selected_seeds": [
    {
      "user_id": "user1",
      "cost": 100,
      "expected_reach": 5.0
    },
    {
      "user_id": "user6",
      "cost": 90,
      "expected_reach": 3.0
    }
  ],
  "cascade_analysis": {
    "total_budget_used": 190,
    "direct_influence": [
      "user2",
      "user3",
      "user7"
    ],
    "secondary_influence": [
      "user4",
      "user5",
      "user8"
    ],
    "total_reach": 8,
    "influence_probability": 0.53
  },
  "network_metrics": {
    "coverage_ratio": 1.0,
    "efficiency_score": 0.042,
    "cascade_depth": 3
  }
}
```

---
## Summary

- Total Problems: 64
- Successful: 64
- Failed: 0
- Success Rate: 100.0%
