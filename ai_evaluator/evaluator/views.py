from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import Question, Submission
from .services.grading_service import grade_objective
from .services.semantic_service import SemanticEvaluator

import json
def home(request):
    return JsonResponse({
        "message": "Welcome to AI Evaluator "
    })
from django.views.decorators.csrf import csrf_exempt
#to test api I have written @csrf_exempt
@csrf_exempt
def evaluate(request):
    if request.method == "POST":
        data = json.loads(request.body)
        question_id = data.get("question_id")
        student_answer = data.get("answer")

        question = get_object_or_404(Question, id=question_id)
        
        # 1. Fetch Rubric
        from .models import Rubric
        rubric = Rubric.objects.filter(question=question).first()
        rubric_criteria = rubric.criteria if rubric else None

        # 2. Objective Scoring & MCQ Validation
        selected_choice_id = data.get("selected_choice_id")
        
        # Validation: Check if choice belongs to this question
        if selected_choice_id:
            from .models import Choice
            if not Choice.objects.filter(id=selected_choice_id, question=question).exists():
                return JsonResponse({"error": "Invalid choice for this question"}, status=400)

        score = grade_objective(question, student_answer, selected_choice_id=selected_choice_id)
        raw_score = score # Objective score is the raw score
        
        # Determine criteria scores for objective
        if score is not None:
            criteria_scores = {"accuracy": score * 100}
        else:
            criteria_scores = None

        # 3. Semantic Evaluation if not objective
        if score is None:
            evaluator = SemanticEvaluator()
            score, criteria_scores, raw_score = evaluator.evaluate(
                question.model_answer, 
                student_answer, 
                rubric_criteria=rubric_criteria
            )

        # 4. Create Submission (Signals will trigger async feedback)
        submission = Submission.objects.create(
            question=question,
            student_answer=student_answer,
            selected_choice_id=selected_choice_id,
            score=score,
            raw_score=raw_score,
            criteria_scores=criteria_scores
        )

        return JsonResponse({
            "submission_id": submission.id,
            "score": score,
            "status": "Feedback being generated..."
        })
    return JsonResponse({"error": "POST request required"}, status=400)

def student_portal(request):
    questions = Question.objects.all()
    total_time = sum(q.time_limit for q in questions) if questions else 5
    return render(request, 'evaluator/student_portal.html', {'questions': questions, 'total_time': total_time})

def submit_answer(request, question_id):
    if request.method == "POST":
        question = get_object_or_404(Question, id=question_id)
        student_answer = request.POST.get("answer")
        
        # 1. Fetch Rubric
        from .models import Rubric
        rubric = Rubric.objects.filter(question=question).first()
        rubric_criteria = rubric.criteria if rubric else None

        # 2. Grading logic & MCQ Validation
        selected_choice_id = request.POST.get("selected_choice")
        
        # Validation: Check if choice belongs to this question
        if selected_choice_id:
            from .models import Choice
            if not Choice.objects.filter(id=selected_choice_id, question=question).exists():
                return redirect('student_portal')

        score = grade_objective(question, student_answer, selected_choice_id=selected_choice_id)
        raw_score = score # Objective score is its own raw score
        
        if score is not None:
            criteria_scores = {"accuracy": score * 100}
        else:
            criteria_scores = None
        
        if score is None:
            evaluator = SemanticEvaluator()
            score, criteria_scores, raw_score = evaluator.evaluate(
                question.model_answer, 
                student_answer, 
                rubric_criteria=rubric_criteria
            )
            
        submission = Submission.objects.create(
            question=question,
            student_answer=student_answer,
            selected_choice_id=selected_choice_id,
            score=score,
            raw_score=raw_score,
            criteria_scores=criteria_scores
        )
        return redirect('result_view', submission_id=submission.id)
    return redirect('student_portal')

def result_view(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)
    return render(request, 'evaluator/result_view.html', {'submission': submission})

def teacher_dashboard(request):
    submissions = Submission.objects.select_related('question').all().order_by('-created_at')
    
    # Teacher Analytics Enhancement
    from django.db.models import Avg, Count, Max, Min
    
    # Aggregated insights across submissions
    from django.db.models import Q
    performance_by_type = submissions.values('question__question_type').annotate(
        avg_score=Avg('score'),
        avg_raw_score=Avg('raw_score'),
        count=Count('id'),
        pass_rate=Count('id', filter=Q(score__gte=0.5)) * 100.0 / Count('id'),
        needs_review=Count('id', filter=Q(score__lt=0.3))
    )

    stats_raw = submissions.aggregate(
        overall_avg=Avg('score'),
        raw_avg=Avg('raw_score', filter=Q(question__question_type='SUB'))
    )

    #stats = {
    #    'avg_score': stats_raw['overall_avg'] if stats_raw['overall_avg'] is not None else 0.0,
    #    'avg_raw_similarity': stats_raw['raw_avg'] if stats_raw['raw_avg'] is not None else 0.0,
    #    'total_submissions': submissions.count(),
    #    'by_type': performance_by_type,
    #    'needs_review_total': submissions.filter(score__lt=0.3).count(),}
    stats = {
    'avg_score': (stats_raw['overall_avg'] or 0.0) * 100,
    'avg_raw_similarity': (stats_raw['raw_avg'] or 0.0) * 100,
    'total_submissions': submissions.count(),
    'by_type': performance_by_type,
    'needs_review_total': submissions.filter(score__lt=0.3).count(),
    }
    return render(request, 'evaluator/teacher_dashboard.html', {
        'submissions': submissions,
        'stats': stats
    })