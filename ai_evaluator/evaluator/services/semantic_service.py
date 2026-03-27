from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer('all-MiniLM-L6-v2')    
def semantic_score(model_answer, student_answer):
    emb1 = model.encode(model_answer, convert_to_tensor=True)
    emb2 = model.encode(student_answer, convert_to_tensor=True)

    similarity = float(util.cos_sim(emb1, emb2)[0][0])
    # Improved thresholds
    if similarity > 0.85:
        return 1.0
    elif similarity > 0.7:
        return 0.8
    elif similarity > 0.5:
        return 0.6
    elif similarity > 0.3:
        return 0.4
    else:
        return 0.1