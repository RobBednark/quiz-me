from .models import Answer, Attempt, Tag, Question
from django.contrib import admin

class TagQuestionRelationshipInline(admin.TabularInline):
    model = Tag.questions.through

class AnswerAdmin(admin.ModelAdmin):
    list_display = ['answer', 'datetime_added', 'datetime_updated']

class AttemptAdmin(admin.ModelAdmin):
    list_display = ['attempt', 'question', 'correct']

class TagAdmin(admin.ModelAdmin):
    # exclude questions, otherwise questions will be shown as a vertical inline as well as the horizontal inline
    exclude = ('questions',)
    inlines = [TagQuestionRelationshipInline]
    list_display = ['datetime_added', 'datetime_updated', 'name']

class QuestionAdmin(admin.ModelAdmin):
    inlines = [TagQuestionRelationshipInline]
    list_display = ['datetime_added', 'datetime_updated', 'question', 'answer']

admin.site.register(Answer, AnswerAdmin)
admin.site.register(Attempt, AttemptAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Question, QuestionAdmin)
