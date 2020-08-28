from django.contrib import admin
from django.db import models

from pagedown.widgets import AdminPagedownWidget

from .models import Answer, Attempt, Tag, Question, Schedule, UserTag


class AnswerQuestionRelationshipInline(admin.TabularInline):
    model = Question


class TagQuestionRelationshipInline(admin.TabularInline):
    model = Tag.questions.through


class AnswerAdmin(admin.ModelAdmin):
    # Show questions that are linked with this answer
    inlines = [AnswerQuestionRelationshipInline]
    list_display = ['id', 'datetime_added', 'answer', 'datetime_updated']
    formfield_overrides = {
        models.TextField: {'widget': AdminPagedownWidget},
    }
    # enable searching for Answer's on these two fields
    search_fields = ['answer', 'question__question']


class AttemptAdmin(admin.ModelAdmin):
    list_display = ['id', 'datetime_added', 'attempt', 'question']
    formfield_overrides = {
        models.TextField: {'widget': AdminPagedownWidget},
    }
    # enable searching for Attempt's on these fields
    search_fields = ['attempt', 'question__id', 'question__question']


class TagAdmin(admin.ModelAdmin):
    # exclude questions, otherwise questions will be shown as a vertical inline as well as the horizontal inline
    exclude = ('questions',)
    inlines = [TagQuestionRelationshipInline]
    list_display = ['datetime_added', 'datetime_updated', 'name', 'pk']
    list_per_page = 999  # how many items to show per page
    ordering = ('name',)
    search_fields = ['name']


class QuestionAdmin(admin.ModelAdmin):
    inlines = [TagQuestionRelationshipInline]
    list_display = ['pk', 'datetime_added', 'datetime_updated', 'tags_display', 'question', 'answer']
    # list_filter = ['',]
    formfield_overrides = {
        models.TextField: {'widget': AdminPagedownWidget},
    }
    # enable searching for Question's on these two fields
    search_fields = ['answer__answer', 'pk', 'question', 'tag__name']

    def tags_display(self, obj):
        # Use for list_display to show the names of all the tags (a many-to-many field)
        return ", ".join([
            tag.name for tag in obj.tag_set.all()
        ])
    tags_display.short_description = "Tags"


class ScheduleAdmin(admin.ModelAdmin):
    list_display = [
        'id',
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

class UserTagAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'enabled',
        'tag',
        'user',
        ]

admin.site.register(Answer, AnswerAdmin)
admin.site.register(Attempt, AttemptAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Schedule, ScheduleAdmin)
admin.site.register(UserTag, UserTagAdmin)
