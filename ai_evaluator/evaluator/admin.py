from django.contrib import admin
from .models import Question, Choice, Rubric, Submission

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 3

class RubricInline(admin.StackedInline):
    model = Rubric
    extra = 1

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text_preview', 'question_type')
    list_filter = ('question_type',)
    search_fields = ('text', 'model_answer')
    inlines = [ChoiceInline, RubricInline]

    def text_preview(self, obj):
        return obj.text[:100]
    text_preview.short_description = 'Question Text'

@admin.register(Rubric)
class RubricAdmin(admin.ModelAdmin):
    list_display = ('question', 'criteria')
    search_fields = ('question__text',)

@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ('question', 'text', 'is_correct')
    list_filter = ('is_correct',)
    search_fields = ('text', 'question__text')

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'score', 'letter_grade', 'created_at')
    list_filter = ('question__question_type', 'created_at')
    readonly_fields = ('score', 'criteria_scores', 'feedback', 'created_at')
    
    def letter_grade(self, obj):
        return obj.get_grade
    letter_grade.short_description = 'Grade'