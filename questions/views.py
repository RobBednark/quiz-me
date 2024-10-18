import humanize
import os
import re
import traceback

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode

from .forms import FormFlashcard, FormSelectTags
from .get_next_question import NextQuestion
from .TagList import TagList
from questions import models

debug_print = eval(os.environ.get('QM_DEBUG_PRINT', 'False'))
debug_sql = eval(os.environ.get('QM_DEBUG_SQL', 'False'))


@login_required(login_url='/login')
def _render_question(request, query_name, select_tags_url, tag_list):
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
    
    # nq stands for "next question"
    nq = NextQuestion(user=request.user, query_name=query_name, tag_ids_selected=tag_list.as_id_int_list())
    id_question = nq.question.id if nq.question else 0

    form_flashcard = FormFlashcard(data=dict(hidden_query_name=query_name, hidden_tag_ids_selected=tag_list.as_id_comma_str(), hidden_question_id=id_question))


    try:
        last_schedule_added = (
            models.Schedule.objects.filter(
                user=request.user,
                question=nq.question
            ).latest('datetime_added')
        )
        last_schedule_added.human_datetime_added = humanize.precisedelta(
            timezone.now() - last_schedule_added.datetime_added)
    except ObjectDoesNotExist:
        last_schedule_added = None

    context = dict(
            buttons=BUTTONS,
            next_question=nq,
            form_flashcard=form_flashcard,
            last_schedule_added=last_schedule_added,
            select_tags_url=select_tags_url,
        )
    return render(
        request=request,
        template_name='question.html',
        context=context
    )

def view_select_tags__get(request):
    query_name = request.GET.get('query_name', None)
    form_select_tags = FormSelectTags(initial=dict(query_name=query_name))
    tag_list = TagList(id_comma_str=request.GET.get('tag_ids_selected', ''))
    query_name = request.GET.get('query_name', None)
    form_select_tags = FormSelectTags(initial=dict(query_name=query_name))
    return render(
        request=request,
        template_name='select_tags.html',
        context=dict(
            form_select_tags=form_select_tags,
            tag_fields_list=tag_list.as_form_fields_list(user=request.user),
        )
    )

def view_select_tags__post(request):
    form_select_tags = FormSelectTags(data=request.POST)
    if form_select_tags.is_valid():
        tag_list = TagList(form_field_names=request.POST)
        # redirect to /question/?tag_ids=...&query_name=...
        query_string = urlencode(dict(
            query_name=form_select_tags.cleaned_data['query_name'],
            tag_ids_selected=tag_list.as_id_comma_str()
        ))
        redirect_url = reverse(viewname='question')
        redirect_url += f'?{query_string}'
        return redirect(to=redirect_url, permanent=True)
    else:
        # Assert: form is NOT valid
        # Need to return the errors to the template,
        # and have the template show the errors.
        # TODO: redirect instead of _render_question()?  Or will _render_question keep any text that the user inputted?
        raise Exception(form_select_tags.errors)

def view_flashcard_post(request):
    # Save the attempt and the schedule.
    form_flashcard = FormFlashcard(data=request.POST)
    if form_flashcard.is_valid():
        id_question = form_flashcard.cleaned_data["hidden_question_id"]
        query_name = form_flashcard.cleaned_data["hidden_query_name"]
        tag_ids_str = form_flashcard.cleaned_data["hidden_tag_ids_selected"]
        tag_list = TagList(id_comma_str=tag_ids_str)
        try:
            question = models.Question.objects.get(id=id_question)
        except models.Question.DoesNotExist:
            # There was no question available.  Perhaps the user
            # selected different tags now, so try again.
            debug_print and print("WARNING: No question exists for question.id=[{id_question}]")
            # TODO: print warning to user
            # TODO: redirect instead of _render_question()?  Or will _render_question keep any text that the user inputted?
            return _render_question(request=request, query_name=query_name, tag_list=tag_list)
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
            raise Exception(form_flashcard.errors)

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
            query_name=query_name,
            tag_ids_selected=tag_list.as_id_comma_str()))
        redirect_url = reverse(viewname='question')
        redirect_url += f'?{query_string}'
        return redirect(to=redirect_url, permanent=True)
    else:
        # Assert: form is NOT valid
        # TODO: Need to return the errors to the template,
        # and have the template show the errors.
        debug_print and print('ERROR: view_flashcard_post: form is NOT valid')
        # TODO: what to do?  
        raise Exception(form_flashcard.errors)

@login_required(login_url='/login')
def view_select_tags(request):
 
    if request.method == 'GET':
        return view_select_tags__get(request=request)
    elif request.method == 'POST':
        return view_select_tags__post(request=request)
    else:
        raise Exception("Unknown request.method=[%s]" % request.method)

@login_required(login_url='/login')
def view_question(request):
    if request.method == 'GET':
        tag_list = TagList(id_comma_str=request.GET.get('tag_ids_selected', ''))
        query_name = request.GET.get('query_name', None)
        
        select_tags_url = reverse(viewname='select_tags')
        query_string = urlencode(dict(
            tag_ids_selected=tag_list.as_id_comma_str(),
            query_name=query_name))
        select_tags_url += f'?{query_string}'
        return _render_question(request=request, tag_list=tag_list, query_name=query_name, select_tags_url=select_tags_url)
    elif request.method == 'POST':
        return view_flashcard_post(request=request)
    else:
        raise Exception("Unknown request.method=[%s]" % request.method)