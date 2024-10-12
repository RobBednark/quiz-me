from django.db import models
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from pagedown.widgets import AdminPagedownWidget

from .models import Answer, Attempt, Tag, Question, QuestionTag, Schedule


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
    list_display = ['id', 'datetime_added', 'tags_display', 'attempt', 'question']
    formfield_overrides = {
        models.TextField: {'widget': AdminPagedownWidget},
    }
    readonly_fields = ('datetime_added', 'datetime_updated')
    # enable searching for Attempt's on these fields
    search_fields = ['attempt', 'question__id', 'question__question', 'question__tag__name']

    def tags_display(self, obj):
        # Use for list_display to show the names of all the tags (a many-to-many field)
        return ", ".join([
            tag.name for tag in obj.question.tag_set.all()
        ])
    tags_display.short_description = "Tags"


class QuestionTagAdmin(admin.ModelAdmin):
    # exclude questions, otherwise questions will be shown as a vertical inline as well as the horizontal inline
    list_display = ['datetime_added', 'datetime_updated', 'enabled', 'tag', 'link_to_tag', 'link_to_question', 'question']
    list_per_page = 999  # how many items to show per page
    ordering = ('tag', 'question')
    search_fields = ['enabled', 'tag__name', 'question__question']

    def link_to_question(self, obj):
        # Add a column with a link to the question
        # Note that this must be present in the list_display, otherwise it will not be shown.
        # https://stackoverflow.com/a/48950925/875915
        # https://docs.djangoproject.com/en/5.1/ref/contrib/admin/#admin-reverse-urls
        link = reverse("admin:questions_question_change", args=[obj.tag_id])
        return format_html('<a href="{}">question</a>', link)

    link_to_question.short_description = 'Edit question'  # the column heading
    
    def link_to_tag(self, obj):
        # Add a column with a link to the tag.
        # Note that this must be present in the list_display, otherwise it will not be shown.
        # https://stackoverflow.com/a/48950925/875915
        # https://docs.djangoproject.com/en/5.1/ref/contrib/admin/#admin-reverse-urls
        link = reverse("admin:questions_tag_change", args=[obj.tag_id])
        return format_html('<a href="{}">{}</a>', link, obj.tag.name)

    link_to_tag.short_description = 'Edit tag'  # the column heading

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

admin.site.register(Answer, AnswerAdmin)
admin.site.register(Attempt, AttemptAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(QuestionTag, QuestionTagAdmin)
admin.site.register(Schedule, ScheduleAdmin)