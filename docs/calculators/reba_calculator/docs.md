# reba_calculator module

# TODO add technical docs about REBA calculator

## REBA_calculator

used to have 2 systems seprated by folders:

- Pose to Degree
- Degree to REBA

I choose to merge the 2 classes into one python file for each body parts
So my folder structure is this:

```
└── 📁reba_calculator
    └── 📁body_parts
        ├── __init__.py
        ├── leg_reba.py
        ├── lower_arm_reba.py
        ├── neck_reba.py
        ├── trunk_reba.py
        ├── upper_arm_reba.py
        ├── wrist_reba.py
    ├── __init__.py
    ├── audit.md
    ├── docs.md
    ├── image.png
    ├── info.md
    ├── REBA_calculator.py
    └── reba_score_tables.py
```

the body_part.py contains all the core logic for the REBA calculation from the poses.

While the REBA_calculator contains the "glue" code to connect with the main MoCap module via internal APIs


---
*For development timelines and feature tracking, please refer to the global project roadmap.*