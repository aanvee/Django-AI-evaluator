from sentence_transformers import SentenceTransformer, util
import os

class SemanticEvaluator:
    _model = None

    @classmethod
    def get_model(cls):
        if cls._model is None:
            # Reusable model loading
            cls._model = SentenceTransformer('all-MiniLM-L6-v2')
        return cls._model

    def evaluate(self, model_answer, student_answer, rubric_criteria=None):
        """
        Evaluates the student answer based on the model answer and optional rubric criteria.
        Returns a tuple: (final_weighted_score, criteria_scores)
        """
        model = self.get_model()
        
        # 1. Calculate Accuracy (Semantic Similarity)
        emb1 = model.encode(model_answer, convert_to_tensor=True)
        emb2 = model.encode(student_answer, convert_to_tensor=True)
        similarity = float(util.cos_sim(emb1, emb2)[0][0])
        accuracy_score = self._calculate_similarity_score(similarity)

        # 2. Calculate Grammar (Heuristic)
        grammar_score = self._calculate_grammar_heuristic(student_answer)

        # 3. Apply Rubric Weighting
        if not rubric_criteria:
            # Default to 100% accuracy if no rubric provided
            return accuracy_score, {"accuracy": accuracy_score * 100}, similarity

        final_score = 0
        per_criteria_results = {}
        
        for criterion, weight in rubric_criteria.items():
            if criterion.lower() == "accuracy":
                final_score += accuracy_score * (weight / 100)
                per_criteria_results["accuracy"] = round(accuracy_score * 100, 2)
            elif criterion.lower() == "grammar":
                final_score += grammar_score * (weight / 100)
                per_criteria_results["grammar"] = round(grammar_score * 100, 2)
            else:
                # Default for unknown criteria: use accuracy as proxy
                final_score += accuracy_score * (weight / 100)
                per_criteria_results[criterion] = round(accuracy_score * 100, 2)

        return round(final_score, 2), per_criteria_results, round(similarity, 4)

    def _calculate_similarity_score(self, similarity):
        if similarity > 0.85: return 1.0
        elif similarity > 0.7: return 0.8
        elif similarity > 0.5: return 0.6
        elif similarity > 0.3: return 0.4
        else: return 0.1

    def _calculate_grammar_heuristic(self, text):
        """Simple heuristic for grammar scoring."""
        if not text: return 0.0
        score = 1.0
        
        # Checklist
        # 1. Starts with capital letter
        if not text[0].isupper(): score -= 0.2
        # 2. Ends with punctuation
        if text[-1] not in ".!?": score -= 0.2
        # 3. Minimum length (at least 3 words)
        words = text.split()
        if len(words) < 3: score -= 0.3
        # 4. Basic capitalization (proper nouns/I) - simplified
        if " i " in text: score -= 0.1 # Should be " I "
        
        return max(0.1, score)