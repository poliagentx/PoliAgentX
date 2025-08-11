import pandas as pd

SDG_ALLOCATION = [
    {"goal": "No Poverty", "percent": 0},
    {"goal": "Zero Hunger", "percent": 0},
    {"goal": "Good Health and Well-being", "percent": 0},
    {"goal": "Quality Education", "percent": 0},
    {"goal": "Gender Equality", "percent": 0},
    {"goal": "Clean Water and Sanitation", "percent": 0},
    {"goal": "Affordable and Clean Energy", "percent": 0},
    {"goal": "Decent Work and Economic Growth", "percent": 0},
    {"goal": "Industry, Innovation, and Infrastructure", "percent": 0},
    {"goal": "Reduced Inequality", "percent": 0},
    {"goal": "Sustainable Cities and Communities", "percent": 0},
    {"goal": "Responsible Consumption and Production", "percent": 0},
    {"goal": "Climate Action", "percent": 0},
    {"goal": "Life Below Water", "percent": 0},
    {"goal": "Life on Land", "percent": 0},
    {"goal": "Peace, Justice, and Strong Institutions", "percent": 0},
    {"goal": "Partnerships for the Goals", "percent": 0},
]


# Run the update
def get_sdg_allocation_from_file(indicators_path):
    df = pd.read_excel(indicators_path)
    df_instr = df[df["instrumental"] == 1]
    sdg_counts = df_instr["sdg"].value_counts().sort_index()
    total = sdg_counts.sum()

    allocation = [
        {"goal": goal["goal"], "percent": round((sdg_counts.get(i+1, 0) / total) * 100, 2) if total > 0 else 0}
        for i, goal in enumerate(SDG_ALLOCATION)
    ]
    return allocation

 
