#from django.shortcuts import render #used to return HTML structrued response

# Create your views here.
from django.http import JsonResponse
from .models import Question, Submission
from .services.grading_service import grade_objective
from .services.semantic_service import semantic_score
from .services.feedback_service import generate_feedback

import json
def home(request):
    return JsonResponse({
        "message": "Welcome to AI Evaluator 🚀"
    })
from django.views.decorators.csrf import csrf_exempt
#to test api I have written @csrf_exempt
@csrf_exempt
def evaluate(request):
    if request.method == "GET":
        return JsonResponse({
            "message": "Use POST request with JSON data"
        })

    if request.method == "POST":
        data = json.loads(request.body)

        question = Question.objects.get(id=data["question_id"])
        student_answer = data["answer"]

        score = grade_objective(question, student_answer)

        if score is None:
            score = semantic_score(question.model_answer, student_answer)

        feedback = generate_feedback(score)

        Submission.objects.create(
            question=question,
            student_answer=student_answer,
            score=score,
            feedback=feedback
        )

        return JsonResponse({
            "score": score,
            "feedback": feedback
        })