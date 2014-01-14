from .models import Answer, Attempt, Question
from django.contrib import admin

class AnswerAdmin(admin.ModelAdmin):
    list_display = ['answer', 'question', 'datetime_added', 'datetime_updated']

class AttemptAdmin(admin.ModelAdmin):
    list_display = ['text', 'question', 'correct']

class QuestionAdmin(admin.ModelAdmin):
    list_display = ['datetime_added', 'datetime_updated', 'question']

admin.site.register(Answer, AnswerAdmin)
admin.site.register(Attempt, AttemptAdmin)
admin.site.register(Question, QuestionAdmin)
