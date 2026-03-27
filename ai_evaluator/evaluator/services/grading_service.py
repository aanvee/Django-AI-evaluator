def grade_objective(question, student_answer):
    if question.question_type == "MCQ":
        return 1.0 if student_answer == question.model_answer else 0.0

    elif question.question_type == "FIB":
        correct = question.model_answer.strip().lower()
        student = student_answer.strip().lower()

        return 1.0 if correct == student else 0.0

    return None