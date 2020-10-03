from collections import defaultdict, namedtuple
from datetime import datetime
import os

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from django.db.models import Count, F, OuterRef, Q, Subquery
from django.forms.models import modelformset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
import humanize
import pytz

from .forms import FormAttemptNew, FormSchedule, FormFlashcard
from questions import models


NextQuestion = namedtuple(
    typename='NextQuestion',
    field_names=[
        'count_questions_before_now',
        'count_questions_tagged',
        'num_schedules',
        'option_limit_to_date_show_next_before_now',
        'question',
        'schedules_recent_count_30',
        'schedules_recent_count_60',
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

    # Fields to sort on:
    # 1. date_show_next (null=unseen)
    # 2. when last answered (schedule_datetime_added)
    # 3. answered count (num_schedules)

    # Types of questions:
    #   1. unanswered questions
    #   2. questions scheduled before now that were just recently answered (e.g., today); want the option to see them as soon as possible to learn them
    #   3. questions scheduled before now that were not recently answered (e.g., before today)
    #   4. questions scheduled after now

    # Desired questioning scenarios:
    # 1) Order by answered_count
    #    option_include_unanswered_questions = True
    #    option_limit_to_date_show_next_before_now = ??
    #    option_order_by_when_answered_newest = False
    #    option_order_by_answered_count = True
    # 2) Order by date_show_next, but show unanswered questions first (questions recently-answered that should be seen quickly again won't necessarily be seen quickly)
    #    Reinforce older questions.
    #    option_include_unanswered_questions = True
    #    option_limit_to_date_show_next_before_now = False
    #    option_order_by_when_answered_newest = False
    #    option_order_by_answered_count = False
    # 3) Order by when answered (schedule_datetime_added), newest first, show questions before now that were just answered first, show unanswered questions last
    #    Reinforce recently-answered questions.
    #    option_include_unanswered_questions = False
    #    option_limit_to_date_show_next_before_now = True
    #    option_order_by_when_answered_newest = True
    #    option_order_by_answered_count = False

    debug_print = eval(os.environ.get('QM_DEBUG_PRINT', 'False'))
    debug_sql = eval(os.environ.get('QM_DEBUG_SQL', 'False'))

    # True  => for questions scheduled before now, only show questions that have answers
    # False => disabled
    option_questions_with_answers_first = eval(os.environ.get('QM_WITH_ANSWERS_FIRST', 'False'))

    # True  => for questions scheduled before now, only show questions that DON'T have answers
    # False => disabled
    option_questions_without_answers_first = eval(os.environ.get('QM_WITHOUT_ANSWERS_FIRST', 'False'))

    # Include unanswered questions (nulls) in first bucket query.
    # Does not affect order-by.
    option_include_unanswered_questions = eval(os.environ.get('QM_INCLUDE_UNANSWERED', 'True'))

    # True  => date_show_next <= now
    # False => don't limit to date_show_next (desirable if want to order by
    #          answered count or when_answered, regardless of schedule)
    # Does not affect order-by.
    option_limit_to_date_show_next_before_now = eval(os.environ.get('QM_LIMIT_TO_DATE_SHOW_NEXT_BEFORE_NOW', 'True'))

    # True => order nulls first (for date_show_next, num_schedules, schedule_datetime_added)
    option_nulls_first = eval(os.environ.get('QM_NULLS_FIRST', 'True'))

    # True  => order by when answered,  newest first (schedule_datetime_added DESC NULLS LAST)
    # False => order by date_show_next, oldest first (date_show_next ASC NULLS FIRST)
    # used with
    #   option_limit_to_date_show_next_before_now=True
    # to show questions to reinforce (see again quickly)
    option_order_by_when_answered_newest = eval(os.environ.get('QM_SORT_BY_WHEN_ANSWERED_NEWEST', 'True'))

    # Takes precedence over all other order_by's
    option_order_by_answered_count = eval(os.environ.get('QM_SORT_BY_ANSWERED_COUNT', 'False'))

    # Takes precedence over all other order_by's, except for option_order_by_answered_count
    option_order_by_when_answered_oldest = eval(os.environ.get('QM_SORT_BY_WHEN_ANSWERED_OLDEST', 'False'))

    debug_print and print('')
    # Print out the values for each of the option_* variables
    for var_name in sorted([var_name for var_name in locals().keys() if var_name.startswith('option_')]):
        debug_print and print('%s: [%s]' % (var_name, locals()[var_name]))

    datetime_now = datetime.now(tz=pytz.utc)

    # user_tags -- UserTags the user has selected that they want to be quizzed on right now
    user_tags = models.UserTag.objects.filter(user=user, enabled=True).values_list('tag', flat=True)
    # tags -- Tags the user has selected that they want to be quizzed on right now
    tags = models.Tag.objects.filter(id__in=user_tags)
    tag_names = tags.values_list('name', flat=True)
    # question_tags -- QuestionTags matching the tags the user wants to be quizzed on
    # (logical OR -- questions that match any (not all) of the tags)
    question_tags = models.QuestionTag.objects.filter(enabled=True, tag__in=tags)

    # questions_tagged -- Questions matching the question_tags
    questions_tagged = models.Question.objects.filter(questiontag__in=question_tags)
    count_questions_tagged = questions_tagged.count()
    # schedules -- all Schedules for the user for each question, newest first by datetime_added
    # OuterRef('pk') refers to the question.pk for each question
    schedules = (models.Schedule.objects
                 .filter(user=user, question=OuterRef('pk'))
                 .order_by('-datetime_added'))
    # questions_annotated - questions_tagged, annotated with .date_show_next
    # questions_annotated.date_show_next -- the Schedule.date_show_next for the most recent Schedule for each question
    questions_annotated = questions_tagged.annotate(date_show_next=Subquery(schedules[:1].values('date_show_next')))
    # add num_schedules field  [reference: https://stackoverflow.com/questions/43770118/simple-subquery-with-outerref/43771738]
    questions_annotated = questions_annotated.annotate(num_schedules=Subquery(
        models.Schedule.objects
            .filter(question=OuterRef('pk'))
            .values('question')
            .annotate(count=Count('pk'))
            .values('count')))
    # question.schedule_datetime_added -- the datetime_added for the most recent Schedule for that question
    questions = questions_annotated.annotate(schedule_datetime_added=Subquery(schedules[:1].values('datetime_added')))
    subquery_include_unanswered = None
    if option_include_unanswered_questions:
        debug_print and print('looking for unanswered questions')
        subquery_include_unanswered = Q(date_show_next__isnull=True)
    subquery_by_date_show_next = None
    if option_limit_to_date_show_next_before_now:
        debug_print and print('looking for questions scheduled before now')
        subquery_by_date_show_next = Q(date_show_next__lte=datetime_now)
    if option_questions_with_answers_first:
        questions = questions.filter(answer__isnull=False)
    if option_questions_without_answers_first:
        questions = questions.filter(answer__isnull=True)

    if subquery_include_unanswered and subquery_by_date_show_next:
        questions = questions.filter(subquery_include_unanswered | subquery_by_date_show_next)
    elif subquery_include_unanswered:
        questions = questions.filter(subquery_include_unanswered)
    elif subquery_by_date_show_next:
        questions = questions.filter(subquery_by_date_show_next)
    order_by = []
    if option_order_by_answered_count:
        order_by.append(F('num_schedules').asc(nulls_first=option_nulls_first))

    if option_order_by_when_answered_oldest:
        # Order by the time when the user last answered the question, oldest first
        order_by.append(F('schedule_datetime_added').asc(nulls_first=option_nulls_first))

    if option_order_by_when_answered_newest:
        # Order by the time when the user last answered the question, newest first
        order_by.append(F('schedule_datetime_added').desc(nulls_first=option_nulls_first))
    else:
        # Order by when the question should be shown again
        order_by.append(F('date_show_next').asc(nulls_first=option_nulls_first))
    # For unanswered questions , order by the time the question was added, oldest first.
    order_by.append(F('datetime_added').asc())
    debug_print and print('order_by = %s' % order_by)
    questions = questions.order_by(*order_by)

    SCHEDULES_SINCE_INTERVAL_30 = { 'minutes': 30 }
    SCHEDULES_SINCE_INTERVAL_60 = { 'minutes': 60 }
    delta_30 = relativedelta(**SCHEDULES_SINCE_INTERVAL_30)  # e.g., (minutes=30)
    delta_60 = relativedelta(**SCHEDULES_SINCE_INTERVAL_60)  # e.g., (minutes=30)
    schedules_since_30 = datetime_now - delta_30
    schedules_since_60 = datetime_now - delta_60
    schedules_recent_count_30 = (
        models.Schedule.objects
        .filter(user=user)
        .filter(datetime_added__gte=schedules_since_30)
        .count())
    schedules_recent_count_60 = (
        models.Schedule.objects
        .filter(user=user)
        .filter(datetime_added__gte=schedules_since_60)
        .count())

    count_questions_before_now = 0
    # query #1
    if questions:
        # Show questions whose schedule.date_show_next <= now
        # assert: there is a question with schedule.date_show_next <= now
        count_questions_before_now = questions.count()
        debug_print and print('first "if": questions.count() = [%s] questions scheduled before now' % count_questions_before_now)
        debug_sql and print(connection.queries[-1])
        question_to_show = questions[0]
    else:
        debug_sql and print(connection.queries[-1])
        debug_print and print('No questions scheduled before now.  Look for unanswered questions.')
        # assert: no question with schedule.date_show_next <= now
        # Look for questions with no schedules, and show the one with the
        # oldest question.datetime_added
        questions = questions_tagged
        questions = questions.filter(schedule=None)
        debug_print and print("order_by('question.datetime_added')")
        questions = questions.order_by('datetime_added')

        # query #2
        if questions:
            debug_print and print('unanswered questions found, count = [%s]' % questions.count())
            debug_sql and print(connection.queries[-1])
            question_to_show = questions[0]
        else:
            debug_print and print('No unanswered questions found, so look for schedules in the future')
            debug_sql and print(connection.queries[-1])
            # assert: no question without a schedule
            # Return the question with the oldest schedule.date_show_next
            # query #3
            questions = questions_annotated
            debug_print and print('order_by(question.date_show_next)')
            questions = questions.order_by('date_show_next')
            if questions:
                debug_print and print('future scheduled questions found, count=[%s]' % questions.count())
                question_to_show = questions[0]
            else:
                debug_print and print('No answers whatsoever')
                question_to_show = None

    # query #4
    num_schedules = models.Schedule.objects.filter(
        user=user,
        question=question_to_show
    ).count()

    debug_print and print('returning question.id = [%s]' % (question_to_show.id if question_to_show else None))
    debug_print and print('')
    return NextQuestion(
        count_questions_before_now=count_questions_before_now,
        count_questions_tagged=count_questions_tagged,
        option_limit_to_date_show_next_before_now=option_limit_to_date_show_next_before_now,
        question=question_to_show,
        schedules_recent_count_30=schedules_recent_count_30,
        schedules_recent_count_60=schedules_recent_count_60,
        user_tag_names=','.join(sorted([tag for tag in tag_names])),  # query #5
        num_schedules=num_schedules,
    )


def _get_tag2periods(user, modelformset_usertag=None):
    """For the given :user:, find the number of questions scheduled to be answered in each time
       period (unseen, -now, now-10m, ...).  Assign this as a string to
       the .interval_counts attribute of the corresponding form in :modelformset_usertag:
       e.g.,
        modelformset_usertag[0].interval_counts == '-now=3 1d-1w=8 unseen=22'
       SIDE EFFECT: modifies modelformset_usertag (adds the ".interval_counts" property on to each form)
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
    # OuterRef('question_id') refers to the QuestionTag field
    subquery_schedules = (models.Schedule.objects
                 .filter(user=user,
                         question=OuterRef('question_id'))
                 .order_by('-datetime_added'))
    # Get all QuestionTag's that are enabled
    question_tags = (models
                        .QuestionTag.objects
                        .filter(enabled=True)
                        # for each question, get the most recently-added schedule for that user
                        .annotate(date_show_next=Subquery(subquery_schedules[:1].values('date_show_next')))
                        .select_related('tag')
    )

    for question_tag in question_tags:
        tag_name = question_tag.tag.name
        if question_tag.date_show_next is None:
            tag2interval2cnt[tag_name]['unseen'] += 1
            if 'unseen' not in tag2interval_order[tag_name]:
                tag2interval_order[tag_name].append('unseen')
        else:
            interval_previous = (None, None, '')
            # Find which interval this schedule is in
            for interval in INTERVALS:
                if interval[0] is None:
                    continue
                # e.g., delta = relativedelta(minutes=4)
                delta = relativedelta(**({interval[1]: interval[0]}))
                now = timezone.now()
                if question_tag.date_show_next <= now + delta:
                    interval_name = '%s-%s' % (
                        interval_previous[2],
                        interval[2]
                    )
                    tag2interval2cnt[tag_name][interval_name] += 1
                    if interval_name not in tag2interval_order[tag_name]:
                        tag2interval_order[tag_name].append(interval_name)
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


@login_required(login_url='/login')
def _get_flashcard(request, form_flashcard=None):
    # Note: make sure to call _create_and_get_usertags() *before* _get_next_question(),
    # because _create_and_get_usertags might create new usertags, which are used
    # by _get_next_question().
    modelformset_usertag = _NEW_create_and_get_usertags(request=request)

    next_question = _get_next_question(user=request.user)
    id_question = next_question.question.id if next_question.question else 0

    _get_tag2periods(
        user=request.user,
        modelformset_usertag=modelformset_usertag
    )
    if not form_flashcard:
        form_flashcard = FormFlashcard(initial=dict(hidden_question_id=id_question))
    if next_question.question:
        question_tag_names = ", ".join(
            sorted([
                str(
                    qtag.tag.name
                ) for qtag in next_question.question.questiontag_set.filter(enabled=True)
            ])
        )
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
        template_name='flashcard.html',
        context=dict(
            count_questions_before_now=next_question.count_questions_before_now,
            count_questions_tagged=next_question.count_questions_tagged,
            form_flashcard=form_flashcard,
            last_schedule_added=last_schedule_added,
            modelformset_usertag=modelformset_usertag,
            modelformset_usertag__total_error_count=modelformset_usertag.total_error_count(),
            modelformset_usertag__non_form_errors=modelformset_usertag.non_form_errors(),
            option_limit_to_date_show_next_before_now=next_question.option_limit_to_date_show_next_before_now,
            question=next_question.question,
            question_tag_names=question_tag_names,
            schedules_recent_count_30=next_question.schedules_recent_count_30,
            schedules_recent_count_60=next_question.schedules_recent_count_60,
            settings = settings,
            user_tag_names=next_question.user_tag_names,
            num_schedules=next_question.num_schedules
        )
    )

def _post_flashcard(request):
    # Save the attempt and the schedule.
    form_flashcard = FormFlashcard(request.POST)
    if form_flashcard.is_valid():
        id_question = form_flashcard.cleaned_data["hidden_question_id"]
        try:
            question = models.Question.objects.get(id=id_question)
        except models.Question.DoesNotExist:
            # There was no question available.  Perhaps the user
            # selected different tags now, so try again.
            return _get_flashcard(request)
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
            pass
        schedule = models.Schedule(
            percent_correct=data['percent_correct'],
            percent_importance=data['percent_importance'],
            interval_num=data['interval_num'],
            interval_unit=data['interval_unit'],
            question=attempt.question,
            user=request.user
        )
        schedule.save()
        return _get_flashcard(request)
    else:
        # Assert: form is NOT valid
        # Need to return the errors to the template,
        # and have the template show the errors.
        return _get_flashcard(request=request, form_flashcard=form_flashcard)

def flashcard(request):
    if request.method == 'GET':
        return _get_flashcard(request=request)
    elif request.method == 'POST':
        return _post_flashcard(request=request)
    else:
        raise Exception("Unknown request.method=[%s]" % request.method)

def _NEW_create_and_get_usertags(request):
    """For the given :request:, return a modelformset_usertag that is an
    iterable with a form for each usertag.
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
        .prefetch_related('tag')
        .order_by('tag__name')
    )

    # Get the user, find all the tags, and create a form for each tag.
    #        GET:
    #            For each of the tags, show a checkbox.
    #            If there is no UserTag for that tag, then show the tag and default to False.

    # Get all the Tag's
    tags = models.Tag.objects.all()

    # Get all the UserTag's for this user
    qs_user_tags = models.UserTag.objects.filter(user=user).prefetch_related('tag')
    user_tags_by_tagname = {
        user_tag.tag.name: user_tag for user_tag in qs_user_tags
    }

    # Create UserTag's for any new tags
    for tag in tags:
        if tag.name not in user_tags_by_tagname:
            # There isn't a tag, so create one
            models.UserTag(user=user, tag=tag, enabled=False).save()

    if request.method == 'GET':
        modelformset_usertag = ModelFormset_UserTag(queryset=queryset)
        for form in modelformset_usertag.forms:
            # For each checkbox, display to the user the tag name
            form.fields['enabled'].label = form.instance.tag.name
        return modelformset_usertag
    elif request.method == 'POST':
        modelformset_usertag = ModelFormset_UserTag(
            queryset=queryset,
            data=request.POST
        )
        for form in modelformset_usertag.forms:
            # For each checkbox, display to the user the tag name
            form.fields['enabled'].label = form.instance.tag.name

        # Save the changes made by the user (selecting/unselecting tags)
        if modelformset_usertag.is_valid():  # All validation rules pass
            modelformset_usertag.save()

            # Create a new modelformset without the POST data, because there might be new tags
            # that have been added after the page was displayed and before the Submit button was
            # clicked.
            modelformset_usertag = ModelFormset_UserTag(queryset=queryset)
            for form in modelformset_usertag.forms:
                # For each checkbox, display to the user the tag name
                form.fields['enabled'].label = form.instance.tag.name
            return modelformset_usertag
        else:
            # ASSERT: modelformset_usertag.is_valid() was called, so modelformset_usertag modified itself to contain
            # any errors, and these errors will be displayed in the form using the form.as_p
            # attribute.
            #  It puts the errors in form._errors and form.errors,
            #   e.g., form.errors['sender'] == 'Enter a valid email address.'
            pass
        return modelformset_usertag
