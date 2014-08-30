from django.contrib import admin
from django.db import models

from pagedown.widgets import AdminPagedownWidget

from .models import Answer, Attempt, Tag, Question

class TagQuestionRelationshipInline(admin.TabularInline):
    model = Tag.questions.through

class AnswerAdmin(admin.ModelAdmin):
    list_display = ['answer', 'datetime_added', 'datetime_updated']
    formfield_overrides = {
            models.TextField: {'widget' : AdminPagedownWidget },
    }

class AttemptAdmin(admin.ModelAdmin):
    list_display = ['attempt', 'question']
    formfield_overrides = {
            models.TextField: {'widget' : AdminPagedownWidget },
    }

class TagAdmin(admin.ModelAdmin):
    # exclude questions, otherwise questions will be shown as a vertical inline as well as the horizontal inline
    exclude = ('questions',)
    inlines = [TagQuestionRelationshipInline]
    list_display = ['datetime_added', 'datetime_updated', 'name']
    ordering = ('name',)

class QuestionAdmin(admin.ModelAdmin):
    inlines = [TagQuestionRelationshipInline]
    list_display = ['datetime_added', 'datetime_updated', 'question', 'answer']
    # list_filter = ['',]
    formfield_overrides = {
            models.TextField: {'widget' : AdminPagedownWidget },
    }

admin.site.register(Answer, AnswerAdmin)
admin.site.register(Attempt, AttemptAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Question, QuestionAdmin)
