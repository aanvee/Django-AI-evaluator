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
#Controls how object appears in admin panel Shows first 50 characters of question ,Makes admin readable
    def __str__(self):
        return self.text[:50]

#Used to define grading rules
class Rubric(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE) #Relationship: MANY rubrics → ONE question , foreign key = Link between table  , on_delete = if question gets deleted than rubrics also gets deleted
    criteria = models.JSONField()  # e.g. {"grammar": 20, "accuracy": 80} Stores structured data (dictionary)

#stored student answer + result
class Submission(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)    #each submission belongs to a question 
    student_answer = models.TextField() #student answer

    score = models.FloatField(null=True, blank=True) #Stores marks
    feedback = models.TextField(null=True, blank=True) #AI-generated feedback

    created_at = models.DateTimeField(auto_now_add=True) #Automatically stores submission time ,No need to set manually Example: 2026-03-27 14:30