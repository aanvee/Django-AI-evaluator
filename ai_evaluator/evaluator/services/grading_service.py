def grade_objective(question, student_answer, selected_choice_id=None):
    if question.question_type == "MCQ":
        if selected_choice_id:
            from evaluator.models import Choice
            try:
                choice = Choice.objects.get(id=selected_choice_id)
                return 1.0 if choice.is_correct else 0.0
            except Choice.DoesNotExist:
                return 0.0
        return 1.0 if student_answer == question.model_answer else 0.0

    elif question.question_type == "FIB":
        if not student_answer:
            return 0.0
        correct = question.model_answer.strip().lower()
        student = student_answer.strip().lower()
        return 1.0 if correct == student else 0.0

    return None