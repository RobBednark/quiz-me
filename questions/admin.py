from django.db import models
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from pagedown.widgets import AdminPagedownWidget

from .models import Answer, Attempt, Tag, Question, QuestionTag, Schedule, TagLineage

class AnswerQuestionRelationshipInline(admin.TabularInline):
    model = Question


class TagQuestionRelationshipInline(admin.TabularInline):
    model = Tag.questions.through
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Only show tags owned by the user
        if db_field.name == "tag":
            kwargs["queryset"] = Tag.objects.filter(user=request.user).order_by('name')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class AnswerAdmin(admin.ModelAdmin):
    # Show questions that are linked with this answer
    inlines = [AnswerQuestionRelationshipInline]
    list_display = ['id', 'datetime_added', 'answer', 'datetime_updated']
    formfield_overrides = {
        models.TextField: {'widget': AdminPagedownWidget},
    }
    # enable searching for Answer's on these two fields
    search_fields = ['answer', 'question__question']

    def get_form(self, request, obj=None, **kwargs):
        '''Default the user field to the current user.'''
        form = super().get_form(request, obj, **kwargs)
        if obj is None:
            form.base_fields['user'].initial = request.user
        return form



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
    list_display = ['datetime_added', 'datetime_updated', 'tag_name', 'link_to_tag', 'link_to_question', 'question']
    list_per_page = 5000  # how many items to show per page
    ordering = ('tag__name', 'question')
    search_fields = ['tag__name', 'question__question']

    def tag_name(self, obj):
        # obj is a QuestionTag object
        return obj.tag.name
    tag_name.admin_order_field = 'tag__name'  # Sort by tag.name rather than default of tag.id
    tag_name.short_description = 'Tag'  # column heading

    def link_to_question(self, obj):
        # Add a column with a link to the question
        # Note that this must be present in the list_display, otherwise it will not be shown.
        # https://stackoverflow.com/a/48950925/875915
        # https://docs.djangoproject.com/en/5.1/ref/contrib/admin/#admin-reverse-urls
        link = reverse("admin:questions_question_change", args=[obj.question_id])
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

    def get_form(self, request, obj=None, **kwargs):
        '''Default the user field to the current user.'''
        form = super().get_form(request, obj, **kwargs)
        if obj is None:
            form.base_fields['user'].initial = request.user
        return form

class TagLineageAdmin(admin.ModelAdmin):
    # I have not found a way to include the links in the ordering, hence two columns each for the parent and the child.
    list_display = ['datetime_added', 'datetime_updated', 'parent_name', 'child_name', 'parent_link', 'child_link']
    list_per_page = 5000  # how many items to show per page
    ordering = ('parent_tag__name', 'child_tag__name')
    search_fields = ['parent_tag__name', 'child_tag__name']

    def child_link(self, obj):
        # Add a column with a link to the child tag
        # Note that this must be present in the list_display, otherwise it will not be shown.
        # https://stackoverflow.com/a/48950925/875915
        # https://docs.djangoproject.com/en/5.1/ref/contrib/admin/#admin-reverse-urls
        link = reverse("admin:questions_tag_change", args=[obj.child_tag.id])
        return format_html('<a href="{}">{}</a>', link, obj.child_tag.name)

    child_link.short_description = 'Child'  # the column heading
    
    def child_name(self, obj):
        # obj is a TagLineage object
        return obj.child_tag.name
    child_name.admin_order_field = 'child_tag__name'  # Sort by child_tag.name rather than default of child_tag.id
    child_name.short_description = 'Child'  # column heading

    def get_form(self, request, obj=None, **kwargs):
        '''Default the user field to the current user.'''
        form = super().get_form(request, obj, **kwargs)
        if obj is None:
            form.base_fields['user'].initial = request.user
        return form
    
    def parent_link(self, obj):
        # Add a column with a link to the parent tag
        # Note that this must be present in the list_display, otherwise it will not be shown.
        # https://stackoverflow.com/a/48950925/875915
        # https://docs.djangoproject.com/en/5.1/ref/contrib/admin/#admin-reverse-urls
        link = reverse("admin:questions_tag_change", args=[obj.parent_tag_id])
        return format_html('<a href="{}">{}</a>', link, obj.parent_tag.name)

    parent_link.short_description = 'Parent'  # the column heading
    
    def parent_name(self, obj):
        # obj is a TagLineage object
        return obj.parent_tag.name
    parent_name.admin_order_field = 'parent__name'  # Sort by parent_tag.name rather than default of parent_tag.id
    parent_name.short_description = 'Parent'  # column heading

class QuestionAdmin(admin.ModelAdmin):
    inlines = [TagQuestionRelationshipInline]
    list_display = ['pk', 'datetime_added', 'datetime_updated', 'tags_display', 'question', 'answer']
    # list_filter = ['',]
    formfield_overrides = {
        models.TextField: {'widget': AdminPagedownWidget},
    }
    # enable searching for Question's on these two fields
    search_fields = ['answer__answer', 'pk', 'question', 'tag__name']

    def get_form(self, request, obj=None, **kwargs):
        '''Default the user field to the current user.'''
        form = super().get_form(request, obj, **kwargs)
        if obj is None:
            form.base_fields['user'].initial = request.user
        return form

    def tags_display(self, obj):
        # Use for list_display to show the names of all the tags (a many-to-many field)
        return ", ".join([
            tag.name for tag in obj.tag_set.all().order_by('name')
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
admin.site.register(TagLineage, TagLineageAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(QuestionTag, QuestionTagAdmin)
admin.site.register(Schedule, ScheduleAdmin)