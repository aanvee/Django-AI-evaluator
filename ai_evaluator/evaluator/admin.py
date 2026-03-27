from django.contrib import admin

# Register your models here.
from .models import Question, Rubric, Submission

admin.site.register(Question)
admin.site.register(Rubric)
admin.site.register(Submission)