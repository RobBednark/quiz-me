from django.contrib import admin
from django.db import models

from pagedown.widgets import AdminPagedownWidget

from .models import Answer, Attempt, Tag, Question, Schedule


class AnswerQuestionRelationshipInline(admin.TabularInline):
    model = Question


class TagQuestionRelationshipInline(admin.TabularInline):
    model = Tag.questions.through


class AnswerAdmin(admin.ModelAdmin):
    # Show questions that are linked with this answer
    inlines = [AnswerQuestionRelationshipInline]
    list_display = ['answer', 'datetime_added', 'datetime_updated']
    formfield_overrides = {
        models.TextField: {'widget': AdminPagedownWidget},
    }
    # enable searching for Answer's on these two fields
    search_fields = ['answer', 'question__question']


class AttemptAdmin(admin.ModelAdmin):
    list_display = ['attempt', 'question']
    formfield_overrides = {
        models.TextField: {'widget': AdminPagedownWidget},
    }


class TagAdmin(admin.ModelAdmin):
    # exclude questions, otherwise questions will be shown as a vertical inline as well as the horizontal inline
    exclude = ('questions',)
    inlines = [TagQuestionRelationshipInline]
    list_display = ['datetime_added', 'datetime_updated', 'name', 'pk']
    list_per_page = 999  # how many items to show per page
    ordering = ('name',)


class QuestionAdmin(admin.ModelAdmin):
    inlines = [TagQuestionRelationshipInline]
    list_display = ['datetime_added', 'datetime_updated', 'question', 'answer', 'pk']
    # list_filter = ['',]
    formfield_overrides = {
        models.TextField: {'widget': AdminPagedownWidget},
    }
    # enable searching for Question's on these two fields
    search_fields = ['answer__answer', 'pk', 'question']


class ScheduleAdmin(admin.ModelAdmin):
    list_display = [
        'datetime_added',
        'percent_correct',
        'percent_importance',
        'date_show_next',
        'interval_num',
        'interval_unit',
        'interval_secs',
        'question',
        'user',
    ]

admin.site.register(Answer, AnswerAdmin)
admin.site.register(Attempt, AttemptAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Schedule, ScheduleAdmin)
