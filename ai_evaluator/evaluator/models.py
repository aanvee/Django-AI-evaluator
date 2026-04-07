from django.db import models    #let python interact with DB

# Defined 1 db table

class Question(models.Model):
    QUESTION_TYPES = [
        ('MCQ', 'Multiple Choice'),
        ('FIB', 'Fill in the Blank'),
        ('SUB', 'Subjective'),
    ]

    text = models.TextField()   #store question + no  character limit
    question_type = models.CharField(max_length=3, choices=QUESTION_TYPES)  #stores type of question.
    model_answer = models.TextField()   #Stores model answer
    time_limit = models.IntegerField(default=5, help_text="Time limit in minutes")
    #Controls how object appears in admin panel Shows first 50 characters of question ,Makes admin readable
    def __str__(self):
        return self.text[:50]

class Choice(models.Model):
    question = models.ForeignKey(Question, related_name='choices', on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.question.text[:20]}... - {self.text}"

#Used to define grading rules
class Rubric(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE) #Relationship: MANY rubrics → ONE question , foreign key = Link between table  , on_delete = if question gets deleted than rubrics also gets deleted
    criteria = models.JSONField()  # e.g. {"grammar": 20, "accuracy": 80} Stores structured data (dictionary)

#stored student answer + result
class Submission(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)    #each submission belongs to a question 
    student_answer = models.TextField(null=True, blank=True) #student answer (for FIB/SUB)
    selected_choice = models.ForeignKey(Choice, null=True, blank=True, on_delete=models.SET_NULL) # for MCQ

    score = models.FloatField(null=True, blank=True) # Thresholded score (0.0-1.0)
    raw_score = models.FloatField(null=True, blank=True) # Raw similarity/exact match score (0.0-1.0)
    criteria_scores = models.JSONField(null=True, blank=True) # Per-rubric scores {"accuracy": 80, "grammar": 70}
    feedback = models.JSONField(null=True, blank=True) #Structured AI-generated feedback

    created_at = models.DateTimeField(auto_now_add=True) #Automatically stores submission time ,No need to set manually Example: 2026-03-27 14:30

    @property
    def scoring_type(self):
        """Derives scoring type: SEMANTIC for subjective, OBJECTIVE for MCQ/FIB."""
        if self.question.question_type == 'SUB':
            return 'SEMANTIC'
        return 'OBJECTIVE'

    @property
    def get_grade(self):
        if self.score is None:
            return "N/A"
        
        if self.score >= 0.85: return "A"
        elif self.score >= 0.7: return "B"
        elif self.score >= 0.5: return "C"
        elif self.score >= 0.3: return "D"
        else: return "F"

    @property
    def score_percentage(self):
        if self.score is None:
            return 0
        return round(self.score * 100, 0)

    def __str__(self):
        return f"Submission {self.id} - {self.question.question_type}"