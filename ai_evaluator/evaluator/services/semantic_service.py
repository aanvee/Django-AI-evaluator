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
        if not student_answer or not student_answer.strip():
            return 0.0, {"accuracy": 0}, 0.0
        model = self.get_model()
        student_answer = student_answer.strip()
        model_answer=model_answer.strip()
        # 1. Calculate Accuracy (Semantic Similarity)
        emb1 = model.encode(model_answer, convert_to_tensor=True)
        emb2 = model.encode(student_answer, convert_to_tensor=True)
        similarity = float(util.cos_sim(emb1, emb2)[0][0])
        accuracy_score = self._calculate_similarity_score(similarity)
        # HARD FAIL: keyword / incomplete answers
        words = student_answer.split()
        if len(words) < 5:
            accuracy_score = 0.05
        if ("," in student_answer or ";" in student_answer) and len(words) < 8:
            accuracy_score *= 0.3
        # 2. Calculate Grammar (Heuristic)
        grammar_score = self._calculate_grammar_heuristic(student_answer)

        # Dynamic grammar weighting
        if accuracy_score <= 0.2:
            grammar_weight = 0.1   # almost ignored
        elif accuracy_score <= 0.4:
            grammar_weight = 0.3
        elif accuracy_score <= 0.7:
            grammar_weight = 0.6
        else:
            grammar_weight = 1.0   # full importance
        grammar_score *= grammar_weight
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
        if accuracy_score <= 0.2:
            final_score = min(final_score, 0.3)
        return round(final_score, 2), per_criteria_results, round(similarity, 4)

    def _calculate_similarity_score(self, similarity):
        if similarity >= 0.92:
            return 1.0   # Excellent answer
        elif similarity >= 0.80:
            return 0.7   # Good but not perfect
        elif similarity >= 0.65:
            return 0.4   # Partial understanding
        elif similarity >= 0.50:
            return 0.2   # Weak answer (keywords / incomplete)
        elif similarity >= 0.35:
            return 0.1   # Very poor
        else:
            return 0.0   # Completely wrong

    def _calculate_grammar_heuristic(self, text):
        
        """Simple heuristic for grammar scoring."""
        if not text: return 0.0
        score = 1.0
        
        # Checklist
        # 1. Starts with capital letter
        if not text[0].isupper(): score -= 0.2
        # 2. Ends with punctuation
        if text[-1] not in ".!?": score -= 0.2
        # 3. Minimum length
        words = text.split()
        if len(words) < 5: score -= 0.3
        # 4. Basic capitalization (proper nouns/I) - simplified
        if " i " in text: score -= 0.1 # Should be " I "
        # 5. Check for structural/stop words to penalize keyword lists
        structural_words = {"is", "are", "was", "were", "the", "a", "an", "of", "and", "in", "to", "by", "for", "with", "it", "they", "this", "that"}
        text_words = set(w.strip('.,?!').lower() for w in words)
        if not structural_words.intersection(text_words):
            # No structural words means it's highly likely just a list of keywords
            score -= 0.4
            
        return max(0.0, round(score, 2))