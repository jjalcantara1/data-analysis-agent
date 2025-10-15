from explain.data_prep import gemini_generate_data_prep_plan

def plan_phase(df_sample):
    """Plan phase: Use Gemini to generate data prep plan and reasoning."""
    plan, confidence = gemini_generate_data_prep_plan(df_sample)
    reasoning = "Planned data preparation based on dataset sample, identifying cleaning steps."
    return plan, reasoning, confidence
