import humanize
import os
import traceback

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode

from .forms import FormFlashcard, FormSelectTags
from .get_next_question import get_next_question
from questions import models

debug_print = eval(os.environ.get('QM_DEBUG_PRINT', 'False'))
debug_sql = eval(os.environ.get('QM_DEBUG_SQL', 'False'))

@login_required(login_url='/login')
def _render_question(request, query_name, select_tags_url, tag_formats):
    MINUTES = 'minutes'
    HOURS = 'hours'
    DAYS = 'days'
    WEEKS = 'weeks'
    MONTHS ='months'
    BUTTONS = [
        [ dict(number=0, unit=MINUTES), dict(number=1, unit=MINUTES), dict(number=5, unit=MINUTES), dict(number=10, unit=MINUTES)],
        [ dict(number=1, unit=HOURS), dict(number=2, unit=HOURS), dict(number=3, unit=HOURS), dict(number=4, unit=HOURS)],
        [ dict(number=1, unit=DAYS), dict(number=2, unit=DAYS), dict(number=3, unit=DAYS), dict(number=4, unit=DAYS)],
        [ dict(number=1, unit=WEEKS), dict(number=2, unit=WEEKS), dict(number=3, unit=WEEKS), dict(number=4, unit=WEEKS)],
        [ dict(number=1, unit=MONTHS), dict(number=2, unit=MONTHS), dict(number=3, unit=MONTHS), dict(number=4, unit=MONTHS)],
    ]
    
    next_question = get_next_question(user=request.user, query_name=query_name, tag_ids_selected=tag_formats.as_id_int_list)
    id_question = next_question.question.id if next_question.question else 0

    form_flashcard = FormFlashcard(data=dict(hidden_query_name=query_name, hidden_tag_ids_selected=tag_formats.as_id_comma_str(), hidden_question_id=id_question))

    if next_question.question:
        question_tag_names = \
            sorted([
                str(
                    qtag.tag.name
                ) for qtag in next_question.question.questiontag_set.filter(enabled=True)
            ])
    else:
        question_tag_names = []

    try:
        last_schedule_added = (
            models.Schedule.objects.filter(
                user=request.user,
                question=next_question.question
            ).latest('datetime_added')
        )
        last_schedule_added.human_datetime_added = humanize.precisedelta(
            timezone.now() - last_schedule_added.datetime_added)
    except ObjectDoesNotExist:
        last_schedule_added = None

    return render(
        request=request,
        template_name='question.html',
        context=dict(
            buttons=BUTTONS,
            count_questions_before_now=next_question.count_questions_before_now,
            count_questions_tagged=next_question.count_questions_tagged,
            form_flashcard=form_flashcard,
            last_schedule_added=last_schedule_added,
            option_limit_to_date_show_next_before_now=next_question.option_limit_to_date_show_next_before_now,
            question=next_question.question,
            question_tag_names=question_tag_names,
            schedules_recent_count_30=next_question.schedules_recent_count_30,
            schedules_recent_count_60=next_question.schedules_recent_count_60,
            selected_tag_names=next_question.selected_tag_names,
            num_schedules=next_question.num_schedules,
            select_tags_url=select_tags_url,
        )
    )

def get_tag_fields(user, selected_tag_formats):
    # selected_tag_formats -- selected tags, as TagFormats instance
    # Get all tags for {user}.  Return a list of dicts, sorted by tag name, where each dict has the fields for one tag,
    # with tag_form_name and tag_form_label to be used in the HTML form.
    # e.g.,
    #  [
    #   { tag_form_name: 'id_form_name_3',  # the form name for the checkbox for this tag, where "3" is tag.id
    #     tag_form_label: 'my tag',  # the label for the checkbox for this tag, corresponding to tag.name
    #     tag_id: 3
    #   }
    #  ]
    tag_fields_list = []
    for tag in models.Tag.objects.filter(user=user):
        tag_form_name = f'id_form_name_{tag.id}'
        # "checked" is the <select type="checkbox"> boolean attribute for whether the checkbox is checked.
        if tag.id in selected_tag_formats.as_int_list():
            checked = 'checked'
        else:
            checked = ''
        tag_fields_list.append(dict(
                tag_form_name=tag_form_name,
                tag_form_label=tag.name,
                tag_id=tag.id,
                checked=checked
                ))
    # sort by tag_form_label
    tag_fields_list.sort(key=lambda x: x['tag_form_label'])
    return tag_fields_list

def view_get_select_tags(request, tag_formats):#
    query_name = request.GET.get('query_name', None)
    form_select_tags = FormSelectTags(initial=dict(query_name=query_name))
    return render(
        request=request,
        template_name='select_tags.html',
        context=dict(
            form_select_tags=form_select_tags,
            tag_fields_list=tag_formats.as_form_fields_list()
        )
    )

def _post_select_tags(request, tag_formats):
    form_select_tags = FormSelectTags(data=request.POST)
    if form_select_tags.is_valid():
        # redirect to /question/?tag_ids=...&query_name=...
        query_string = urlencode(dict(
            query_name=form_select_tags.cleaned_data['query_name'],
            tag_ids_selected=tag_formats.as_id_comma_str()
        ))
        redirect_url = reverse(viewname='question')
        redirect_url += f'?{query_string}'
        return redirect(to=redirect_url, permanent=True)
    else:
        # Assert: form is NOT valid
        # Need to return the errors to the template,
        # and have the template show the errors.
        # TODO: redirect instead of _render_question()?  Or will _render_question keep any text that the user inputted?
        return _render_question(request=request, query_name=None, tag_formats=tag_formats)

def get_selected_tag_ids(request):
    # return a list of tag id's that were selected in the form, e.g., given and argument of:
    #    request.POST == { 'id_form_name_2': True }
    # and a precondition of this tag in the database:
    #   { id: 2, name: 'my tag', user: <User: user> }
    # return:
    #   [2]
    tag_fields_list = get_tag_fields(user=request.user, selected_tag_ids=[])
    tag_ids_selected = []
    for tag_fields in tag_fields_list:
        if request.POST.get(tag_fields['tag_form_name'], None):
            tag_ids_selected.append(tag_fields['tag_id'])
    return tag_ids_selected

def _post_flashcard(request):
    # Save the attempt and the schedule.
    form_flashcard = FormFlashcard(data=request.POST)
    tag_ids_selected = get_selected_tag_ids(request=request)
    if form_flashcard.is_valid():
        id_question = form_flashcard.cleaned_data["hidden_question_id"]
        query_name = form_flashcard.cleaned_data["hidden_query_name"]
        tag_ids_selected_str = form_flashcard.cleaned_data["hidden_tag_ids_selected"]
        tag_ids_selected = tag_ids_selected_str.split(',')
        tag_ids_selected = [int(tag) for tag in tag_ids_selected]
        tag_objs_selected = models.Tag.objects.filter(id__in=tag_ids_selected, user=request.user)
        try:
            question = models.Question.objects.get(id=id_question)
        except models.Question.DoesNotExist:
            # There was no question available.  Perhaps the user
            # selected different tags now, so try again.
            debug_print and print("WARNING: No question exists for question.id=[{id_question}]")
            # TODO: print warning to user
            # TODO: redirect instead of _render_question()?  Or will _render_question keep any text that the user inputted?
            return _render_question(request=request, query_name=query_name, tag_ids_selected=tag_ids_selected)
        data = form_flashcard.cleaned_data
        attempt = models.Attempt(
            attempt=data['attempt'],
            question=question,
            user=request.user
        )
        try:
            attempt.save()
        except Exception:
            # TODO: do something here,
            # e.g., log it, show it to the user
            print('EXCEPTION: attempt.save():')
            print(traceback.format_exc())
            raise

        schedule = models.Schedule(
            percent_correct=data['percent_correct'],
            percent_importance=data['percent_importance'],
            interval_num=data['interval_num'],
            interval_unit=data['interval_unit'],
            question=attempt.question,
            user=request.user
        )
        schedule.save()

        # redirect to /question/?tag_ids=...&query_name=...
        query_string = ''
        query_string = urlencode(dict(
            tag_ids_selected=tag_ids_selected_str,
            query_name=query_name))
        redirect_url = reverse(viewname='question')
        redirect_url += f'?{query_string}'
        return redirect(to=redirect_url, permanent=True)
    else:
        # Assert: form is NOT valid
        # Need to return the errors to the template,
        # and have the template show the errors.
        debug_print and print('ERROR: _post_flashcard: form is NOT valid')
        return _render_question(request=request, query_name=query_name, tag_ids_selected=tag_objs_selected)

@login_required(login_url='/login')
def view_select_tags(request):
    tag_formats = TagFormats(id_comma_str=request.GET.get('tag_ids_selected', ''))
 
    if request.method == 'GET':
        return view_get_select_tags(request=request, tag_formats=tag_formats)
    elif request.method == 'POST':
        return _post_select_tags(request=request, tag_formats=tag_formats)
    else:
        raise Exception("Unknown request.method=[%s]" % request.method)

@login_required(login_url='/login')
def view_question(request):
    if request.method == 'GET':
        tag_ids_selected_str = request.GET.get('tag_ids_selected', None)
        if tag_ids_selected_str:
            tag_ids_selected = tag_ids_selected_str.split(',')
        else:
            tag_ids_selected = []
        tag_ids_selected = [int(tag_id) for tag_id in tag_ids_selected]
        # e.g., tag_ids_selected=[1, 2]
        tag_objs_selected = models.Tag.objects.filter(id__in=tag_ids_selected, user=request.user)
        query_name = request.GET.get('query_name', None)
        
        select_tags_url = reverse(viewname='select_tags')
        query_string = urlencode(dict(
            tag_ids_selected=tag_ids_selected_str,
            query_name=query_name))
        select_tags_url += f'?{query_string}'
        return _render_question(request=request, tag_objs_selected=tag_objs_selected, query_name=query_name, select_tags_url=select_tags_url)
    elif request.method == 'POST':
        return _post_flashcard(request=request)
    else:
        raise Exception("Unknown request.method=[%s]" % request.method)

class TagFormats:
    def __init__(self, id_comma_str=None):
        
        if id_comma_str:
            self.id_comma_str = id_comma_str
            if id_comma_str != '':
                as_str_list = id_comma_str.split(',')
                self.as_id_int_list = [int(tag_id) for tag_id in tag_ids_selected_list]
            else:
                self.as_id_int_list = tag_ids_selected_str.split(',')
        else:
            self.id_comma_str = ''
            self.as_id_int_list = []

    
    def as_id_comma_str(self):
        # e.g., "1,2"
        return self.id_comma_str
    
    def as_id_int_list(self):
        # e.g., [1, 2]
        return self.as_id_int_list
    
    def as_form_fields_list(self, user)
    # Get all tags for {user}.  Return a list of dicts, sorted by tag name, where each dict has the fields for one tag,
    # with tag_form_name and tag_form_label to be used in the HTML form.
    # e.g.,
    #  [
    #   { tag_form_name: 'id_form_name_3',  # the form name for the checkbox for this tag, where "3" is tag.id
    #     tag_form_label: 'my tag',  # the label for the checkbox for this tag, corresponding to tag.name
    #     tag_id: 3
    #   }
    #  ]
        tag_fields_list = []
        for tag in models.Tag.objects.filter(user=user):
            tag_form_name = f'id_form_name_{tag.id}'
            # "checked" is the <select type="checkbox"> boolean attribute for whether the checkbox is checked.
            if tag.id in self.as_int_list():
                checked = 'checked'
            else:
                checked = ''
            tag_fields_list.append(dict(
                    tag_form_name=tag_form_name,
                    tag_form_label=tag.name,
                    tag_id=tag.id,
                    checked=checked
                    ))
        # sort by tag_form_label
        tag_fields_list.sort(key=lambda x: x['tag_form_label'])
        return tag_fields_list