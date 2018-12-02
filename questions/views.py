from collections import defaultdict, namedtuple
from datetime import datetime

from dateutil.relativedelta import relativedelta
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.db.models import Count, OuterRef, Subquery
from django.forms.models import modelformset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils import timezone
import pytz

from .forms import FormAttemptNew, FormSchedule
from questions import models


NextQuestion = namedtuple(
    typename='NextQuestion',
    field_names=[
        'num_schedules',
        'question',
        'user_tag_names'
    ]
)


def _get_next_question(user):
    # Bucket 1: questions scheduled before now
    # First look for questions with schedule.date_show_next <= now,
    # and return the question with the newest schedule.datetime_added.

    # Bucket 2: unscheduled questions
    # If there are none of those, then look for questions with no schedules,
    # and return the question with the oldest question.datetime_added.

    # Bucket 3: questions scheduled after now
    # If there are no questions without schedules, then return the question
    # with the oldest schedule.date_show_next

    datetime_now = datetime.now(tz=pytz.utc)
    user_tags = models.UserTag.objects.filter(user=user, enabled=True).values_list('tag', flat=True)
    tags = models.Tag.objects.filter(id__in=user_tags)
    tag_names = tags.values_list('name', flat=True)
    question_tags = models.QuestionTag.objects.filter(enabled=True, tag__in=tags)
    questions_tagged = models.Question.objects.filter(questiontag__in=question_tags)
    schedules = (models.Schedule.objects
                 .filter(user=user, question=OuterRef('pk'))
                 .order_by('-datetime_added'))
    questions_annotated = questions_tagged.annotate(date_show_next=Subquery(schedules[:1].values('date_show_next')))
    questions = questions_annotated.annotate(schedule_datetime_added=Subquery(schedules[:1].values('datetime_added')))
    questions = questions.filter(date_show_next__lte=datetime_now)  # will this get questions with no schedules?
    questions = questions.order_by('-schedule_datetime_added')

    # query #1
    if questions:
        question_to_show = questions[0]
    else:
        # assert: no question with schedule.date_show_next <= now
        # Look for questions with no schedules, and show the one with the
        # oldest question.datetime_added
        questions = questions_tagged
        questions = questions.filter(schedule=None)
        questions = questions.order_by('datetime_added')

        # query #2
        if questions:
            question_to_show = questions[0]
        else:
            # assert: no question without a schedule
            # Return the question with the oldest schedule.date_show_next
            # query #3
            questions = questions_annotated
            questions = questions.order_by('date_show_next')
            if questions:
                question_to_show = questions[0]
            else:
                question_to_show = None

    # query #4
    num_schedules = models.Schedule.objects.filter(
        user=user,
        question=question_to_show
    ).count()

    return NextQuestion(
        question=question_to_show,
        user_tag_names=sorted([tag for tag in tag_names]),  # query #5
        num_schedules=num_schedules,
    )


def _get_tag2periods(user, modelformset_usertag=None):
    """For the given :user:, find the number of questions scheduled to be answered in each time
       period (unseen, -now, now-10m, ...).  Assign this as a string to
       the .interval_counts attribute of the corresponding form in :modelformset_usertag:
       e.g.,
        modelformset_usertag[0].interval_counts == '-now=3 1d-1w=8 unseen=22'
    """
    # TODO: also pass in the selected tags and count the questions for those tags
    INTERVALS = (
        # integer, unit, display-name
        (None, None, "unseen"),
        (0, "minutes", "now"),
        (10, "minutes", "10m"),
        (1, "hour", "1h"),
        (1, "day", "1d"),
        (1, "weeks", "1w"),
        (1, "months", "1mo"),
        (1, "year", "1y"))
    tag2interval2cnt = defaultdict(lambda: defaultdict(int))
    tag2interval_order = defaultdict(list)
    tags = models.Tag.objects.all()
    schedules = (models.Schedule.objects
                 .filter(user=user, question=OuterRef('question_id'))
                 .order_by('-datetime_added'))
    for tag in tags:
        # Get all QuestionTag's for this tag
        question_tags = models.QuestionTag.objects.filter(
            enabled=True, tag=tag
        )

        # Also get the questions for each QuestionTag so that we don't need to do additional queries
        question_tags = question_tags.select_related('question')
        # for each question, get the most recently-added schedule for that user
        question_tags = question_tags.annotate(date_show_next=Subquery(schedules[:1].values('date_show_next')))

        for question_tag in question_tags:
            question = question_tag.question
            if question_tag.date_show_next is None:
                tag2interval2cnt[tag.name]['unseen'] += 1
                if 'unseen' not in tag2interval_order[tag.name]:
                    tag2interval_order[tag.name].append('unseen')
            else:
                interval_previous = (None, None, '')
                # Find which interval this schedule is in
                for interval in INTERVALS:
                    if interval[0] is None:
                        continue
                    delta = relativedelta(**({interval[1]: interval[0]}))
                    now = timezone.now()
                    if question_tag.date_show_next <= now + delta:
                        interval_name = '%s-%s' % (
                            interval_previous[2],
                            interval[2]
                        )
                        tag2interval2cnt[tag.name][interval_name] += 1
                        if interval_name not in tag2interval_order[tag.name]:
                            tag2interval_order[tag.name].append(interval_name)
                        break
                    interval_previous = interval

    for form in modelformset_usertag:
        # update the corresponding tag in modelformset
        tag_name = form.instance.tag.name
        interval_str = ''
        for interval in tag2interval_order[tag_name]:
            interval_str += '{interval}={count}  '.format(
                interval=interval, count=tag2interval2cnt[tag_name][interval]
            )
        form.interval_counts = interval_str
    return tag2interval2cnt


def _create_and_get_usertags(request):
    """For the given :request:, return a modelformset_usertag that is an
    iterable which a form for each usertag.
    request.user will be used to get the corresponding usertags for that user.
    if request.method == 'GET', then find all the tags and create a form for each tag.
    if request.method == 'POST', then save any changes made by the user to any of the forms.
    Returns modelformset_usertag (an iterable of one form for each usertag).
    """
    ModelFormset_UserTag = modelformset_factory(
        model=models.UserTag, extra=0, fields=('enabled',)
    )

    user = request.user
    queryset = (
        models.UserTag.objects.filter(user=user)
        # annotate the number of questions so it can be displayed to the user
        .annotate(num_questions=Count('tag__questions'))
        .order_by('tag__name')
    )

    if request.method == 'GET':
        # Get the user, find all the tags, and create a form for each tag.
        #        GET:
        #            For each of the tags, show a checkbox.
        #            If there is no UserTag for that tag, then show the tag and default to False.

        # Get all the Tag's
        tags = models.Tag.objects.all()

        # Get all the UserTag's for this user
        qs_user_tags = models.UserTag.objects.filter(user=user)
        user_tags_by_tagname = {
            user_tag.tag.name: user_tag for user_tag in qs_user_tags
        }

        # Create UserTag's for any new tags
        for tag in tags:
            if tag.name not in user_tags_by_tagname:
                # There isn't a tag, so create one
                models.UserTag(user=user, tag=tag, enabled=False).save()

        modelformset_usertag = ModelFormset_UserTag(queryset=queryset)
        for form in modelformset_usertag.forms:
            # For each checkbox, display to the user the tag name
            form.fields['enabled'].label = form.instance.tag.name

        return modelformset_usertag
    elif request.method == 'POST':
        # Save the changes made by the user (selecting/unselecting tags)
        modelformset_usertag = ModelFormset_UserTag(
            queryset=queryset,
            data=request.POST
        )
        for form in modelformset_usertag.forms:
            form.fields['enabled'].label = form.instance.tag.name

        if modelformset_usertag.is_valid():  # All validation rules pass
            modelformset_usertag.save()
        else:
            # ASSERT: modelformset_usertag.is_valid() was called, so modelformset_usertag modified itself to contain
            # any errors, and these errors will be displayed in the form using the form.as_p
            # attribute.
            #  It puts the errors in form._errors and form.errors,
            #   e.g., form.errors['sender'] == 'Enter a valid email address.'
            pass
        return modelformset_usertag


@login_required(login_url='/login')
def question_next(request):
    # get the next question and redirect to it
    next_question = _get_next_question(user=request.user)
    id_question = next_question.question.id if next_question.question else 0
    return HttpResponseRedirect(reverse('question', args=(id_question,)))


@login_required(login_url='/login')
def question(request, id_question):
    # Display the question, with a form to put in the attempted answer

    modelformset_usertag = _create_and_get_usertags(request=request)
    if request.method == 'GET':
        # For a GET, show the next question
        next_question = _get_next_question(user=request.user)
        _get_tag2periods(
            user=request.user,
            modelformset_usertag=modelformset_usertag
        )
        form_attempt = FormAttemptNew()
        if next_question.question:
            question_tag_names = ", ".join(
                sorted([
                    str(
                        qtag.tag.name
                    ) for qtag in next_question.question.questiontag_set.all()
                ])
            )
        else:
            question_tag_names = []

        # TODO: get the number of questions answered (scheduled) in the last hour

        # TODO: get the number of questions answered (scheduled) since midnight

        try:
            last_schedule_added = (
                models.Schedule.objects .filter(
                    user=request.user,
                    question=next_question.question
                ).latest(field_name='datetime_added')
            )
        except ObjectDoesNotExist:
            last_schedule_added = None

        # TODO: get total number of questions for all tags

        return render(
            request=request,
            template_name='question.html',
            context=dict(
                form_attempt=form_attempt,
                last_schedule_added=last_schedule_added,
                modelformset_usertag=modelformset_usertag,
                question=next_question.question,
                question_tag_names=question_tag_names,
                user_tag_names=next_question.user_tag_names,
                num_schedules=next_question.num_schedules
            )
        )
    elif request.method == 'POST':
        # ASSERT: this is a POST, so the user answered a question
        # Show the question, the attempt, and the correct answer.
        # Show a NEXT button to do a GET and get the next question
        form_attempt = FormAttemptNew(request.POST)
        if form_attempt.is_valid():
            question = models.Question.objects.get(id=id_question)
            attempt = models.Attempt(
                attempt=form_attempt.cleaned_data['attempt'],
                question=question,
                user=request.user
            )
            try:
                attempt.save()
            except Exception:
                # TODO: do something else here,
                # e.g., log it, show it to the user  -Rob Bednark 12/21/14
                pass
            # Redirect to the answer page
            return HttpResponseRedirect(reverse('answer', args=(attempt.id,)))
        else:
            # Assert: form is NOT valid
            # Need to return the errors to the template,
            # and have the template show the errors.
            return render(
                request=request,
                template_name='question.html',
                context=dict(form_attempt=form_attempt)
            )
    else:
        raise Exception("Unknown request.method=[%s]" % request.method)


@login_required(login_url='/login')
def answer(request, id_attempt):
    # Display the question, the attempt, and the answer
    attempt = models.Attempt.objects.get(id=id_attempt)
    modelformset_usertag = _create_and_get_usertags(request=request)

    if request.method == 'GET':
        _get_tag2periods(
            user=request.user, modelformset_usertag=modelformset_usertag
        )

        form_schedule = FormSchedule()

        if attempt.question:
            question_tag_names = ", ".join(
                sorted([
                    str(
                        qtag.tag.name
                    ) for qtag in attempt.question.questiontag_set.all()
                ])
            )
        else:
            question_tag_names = []

        context_dict = {
            'form_schedule': form_schedule,
            'modelformset_usertag': modelformset_usertag,
            'question': attempt.question,
            'question_tag_names': question_tag_names,
            'answer': attempt.question.answer,
            'attempt': attempt,
        }

        return render(
            request=request,
            template_name='answer.html',
            context=context_dict,
        )

    elif request.method == 'POST':
        # ASSERT: this is a POST, so the user answered a question, and inputted
        # when they want to see the question again.
        # Redirect the user to the next question.
        form_schedule = FormSchedule(request.POST)

        if form_schedule.is_valid():
            data = form_schedule.cleaned_data
            schedule = models.Schedule(
                percent_correct=data['percent_correct'],
                percent_importance=data['percent_importance'],
                interval_num=data['interval_num'],
                interval_unit=data['interval_unit'],
                question=attempt.question,
                user=request.user
            )
            schedule.save()

            return HttpResponseRedirect(reverse('question_next'))
        else:
            # Assert: form is NOT valid
            # Need to return the errors to the template, and have the template show the errors.
            _get_tag2periods(
                user=request.user,
                modelformset_usertag=modelformset_usertag
            )

            context_dict = {
                'form_schedule': form_schedule,
                'modelformset_usertag': modelformset_usertag,
                'question': attempt.question,
                'answer': attempt.question.answer,
                'attempt': attempt
            }

            return render(
                request=request,
                template_name='answer.html',
                context=context_dict,
            )
    else:
        raise Exception("Unknown request.method=[%s]" % request.method)
