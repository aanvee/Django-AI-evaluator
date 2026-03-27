#Later I will replace it with deepseek
def generate_feedback(score):
    if score > 0.8:
        return "Excellent answer."
    elif score > 0.5:
        return "Good, but can improve."
    else:
        return "Needs improvement."