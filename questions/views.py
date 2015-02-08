from collections import defaultdict, namedtuple, OrderedDict

from dateutil.relativedelta import relativedelta

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db.models import Count, Max, Min
from django.forms.models import modelformset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils import timezone

from .forms import FormAttempt, FormAttemptNew, FormSchedule
from .models import Attempt, Question, QuestionTag, Schedule, Tag, User, UserTag

NextQuestion = namedtuple(typename='NextQuestion',
                          field_names = [
                            'question',
                            'user_tags',
                          ]
)

def _get_next_question_previous_working(user):
    ''' Find and return the next question for the currently logged-in user.
    '''
    '''
        Query for all questions that contain at least one of the UserTags
        Input:
            UserTags with enabled=True
        Output:
            questions that have one or more QuestionTag's 
            WHERE 
                QuestionTag.enabled=True
            AND
                QuestionTag.

    '''

    # Find all the tags that the user has selected
    user_tags = UserTag.objects.select_related('tag').filter(user=user, enabled=True)

    # Find the number of questions for each tag (only used to display the number to the user)
    user_tags = user_tags.annotate(num_questions=Count('tag__questions'))
    tag_ids = [ user_tag.tag.id for user_tag in user_tags ]
    for user_tag in user_tags:
        print "DEBUG: tag=[%s] num_questions=[%s]" % (user_tag.tag.name, user_tag.num_questions)

    # Find all the QuestionTag's associated with the UserTag's
    question_tags = QuestionTag.objects.filter(enabled=True, tag__in=tag_ids)

    # Also get the questions so that we don't need to do additional queries
    question_tags = question_tags.select_related('question')

    # Find the earliest/oldest date_show_next schedule for each question.
    # TODO: this doesn't look correct; what is "question__schedule"?  A question can have multiple schedules associated with it.  We need to find the latest schedule for the user for that question.
    question_tags = question_tags.annotate(schedule_oldest=Min('question__schedule__date_show_next'))

    # First look for questions without any schedules, ordered oldest added first
    question_tags_no_schedule = question_tags.filter(schedule_oldest=None).order_by('question__datetime_added')
    # If there is a question with no schedules, then use that one.
    if question_tags_no_schedule:
        # [0] will be the question with the oldest datetime_added
        question = question_tags_no_schedule[0].question
    else:
        # Assert: there are no questions with no schedules; all questions have at least one schedule
        # Find the newest schedule 
        # order_by defaults to ascending order (oldest to newest dates)
        # Note that this is an additional/second query (the first one is the question_tags_no_schedule)
        question_tags = question_tags.order_by('schedule_oldest')
        question = question_tags[0].question if question_tags else None
    return NextQuestion(
            question=question,
            user_tags=user_tags,
    )

def _get_next_question(user):
    ''' Find and return the next question for the currently logged-in user.
    '''
    # Find all the tags that the user has selected (UserTag's)
    user_tags = UserTag.objects.select_related('tag').filter(user=user, enabled=True)

    # Find the number of questions for each tag (only used to display the number to the user)
    user_tags = user_tags.annotate(num_questions=Count('tag__questions'))

    # Find all the QuestionTag's associated with the UserTag's
    question_tags = QuestionTag.objects.filter(enabled=True, tag__in=user_tags)

    # Find all the questions associated with the QuestionTag's
    questions = Question.objects.filter(questiontag__in=question_tags).all()

    # Can't do an annotate on questions for a schedule, because it returns a value, not the schedule

    # Find the most-recently-added schedule of each question (datetime_added),
    # and among all those schedules, find the oldest schedule that is due (date_show_next).
    oldest_schedule = None
    oldest_question = None

    # first see if there are questions without any schedules.  If there are, then return the one with the oldest datetime_added

    for question in questions:
        # Get the most recently-added schedule for this question
        try:
            schedule = (Schedule.objects
                                .filter(user=user, question=question)
                                .latest(field_name='datetime_added'))
        except ObjectDoesNotExist:
            schedule = None
        if schedule:
            if oldest_question:
                pass
            else:
                if oldest_schedule:
                    if schedule.date_show_next < oldest_schedule.date_show_next:
                        oldest_schedule = schedule
                else:
                    oldest_schedule = schedule
        else:
            if oldest_question:
                if question.datetime_added < oldest_question.datetime_added:
                    oldest_question = question
            else:
                oldest_question = question
    if oldest_question:
        question = oldest_question
    elif oldest_schedule:
        question = oldest_schedule.question
    else:
        question = None

    return NextQuestion(
            question=question,
            user_tags=user_tags,
    )

def _get_tag2periods(user, modelformset_usertag=None):
    # IN-PROCESS / TODO:
    INTERVALS = (
            (None, None, "unseen"),
            (0, "minutes", "now"),
            (10, "minutes", "10m"),
            (1, "hour", "1h"),
            (1, "day", "1d"),
            (1, "weeks", "1w"),
            (1, "months", "1mo"),
            (1, "year", "1y"),
    )
    tag2interval2cnt = defaultdict(lambda: defaultdict(int))
    tag2interval_order = defaultdict(list)
    tags = Tag.objects.all()
    for tag in tags:
        # Get all QuestionTag's for this tag
        question_tags = QuestionTag.objects.filter(enabled=True, tag=tag)

        # Also get the questions for each QuestionTag so that we don't need to do additional queries
        question_tags = question_tags.select_related('question')

        for question_tag in question_tags:
            question = question_tag.question
            # for each question, get the most recently-added schedule for that user
            try:
                latest = Schedule.objects.filter(user=user, question=question).latest(field_name='datetime_added')
            except ObjectDoesNotExist:
                latest = None
            if latest == None:
                tag2interval2cnt[tag.name]['unseen'] += 1
                if not 'unseen' in tag2interval_order[tag.name]:
                    tag2interval_order[tag.name].append('unseen')
            else:
                interval_previous = (None, None, '')
                # Find which interval this schedule is in
                for interval in INTERVALS:
                    if interval[0] == None:
                        continue
                    delta = relativedelta(**({interval[1]: interval[0]}))
                    now = timezone.now()
                    if latest.date_show_next <= now + delta:
                        interval_name = '%s-%s' % (interval_previous[2], interval[2])
                        tag2interval2cnt[tag.name][interval_name] += 1
                        if not interval_name in tag2interval_order[tag.name]:
                            tag2interval_order[tag.name].append(interval_name)
                        break
                    interval_previous = interval

    for form in modelformset_usertag:
        # update the corresponding tag in modelformset
        tag_name = form.instance.tag.name
        interval_str = ''
        for interval in tag2interval_order[tag_name]:
            interval_str += '{interval}={count}  '.format(interval=interval, count=tag2interval2cnt[tag_name][interval])
        form.interval_counts = interval_str
    return tag2interval2cnt


def _create_and_get_usertags(request):
    ModelFormset_UserTag = modelformset_factory(model=UserTag,
                                                extra=0,
                                                fields=('enabled',))
    user = request.user
    queryset = (UserTag.objects
                       .filter(user=user)
                       # annotate the number of questions so it can be displayed to the user
                       .annotate(num_questions=Count('tag__questions'))
                       .order_by('tag__name'))

    if request.method == 'GET':
        # Get the user, find all the tags, and create a form for each tag.
        #        GET:
        #            For each of the tags, show a checkbox.
        #            If there is no UserTag for that tag, then show the tag and default to False.

        # Get all the Tag's
        tags = Tag.objects.all()

        # Get all the UserTag's for this user
        qs_user_tags = UserTag.objects.filter(user=user)
        user_tags_by_tagname = { user_tag.tag.name : user_tag for user_tag in qs_user_tags }

        # Create UserTag's for any new tags
        for tag in tags:
            if not tag.name in user_tags_by_tagname:
                # There isn't a tag, so create one
                UserTag(user=user, tag=tag, enabled=False).save()

        modelformset_usertag = ModelFormset_UserTag(queryset=queryset)
        for form in modelformset_usertag.forms:
            # For each checkbox, display to the user the tag name
            form.fields['enabled'].label = form.instance.tag.name

        return modelformset_usertag
    elif request.method == 'POST':
        # Save the changes made by the user (selecting/unselecting tags)
        modelformset_usertag = ModelFormset_UserTag(queryset=queryset, data=request.POST)
        for form in modelformset_usertag.forms:
            form.fields['enabled'].label = form.instance.tag.name

        if modelformset_usertag.is_valid(): # All validation rules pass
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

    modelformset_usertag = _create_and_get_usertags(request=request)
    if request.method == 'GET':
        # For a GET, show the next question
        next_question = _get_next_question(user=request.user)
        _get_tag2periods(user=request.user, modelformset_usertag=modelformset_usertag)
        form_attempt = FormAttemptNew()
        # TODO: get total number of questions for all tags
        return render(request=request, 
                      template_name='question.html', 
                      dictionary=dict(form_attempt=form_attempt, 
                                      modelformset_usertag=modelformset_usertag,
                                      question=next_question.question
                                      ))
    elif request.method == 'POST':
        # ASSERT: this is a POST, so the user answered a question
        # Show the question, the attempt, and the correct answer.
        # Show a NEXT button to do a GET and get the next question
        form_attempt = FormAttemptNew(request.POST)
        if form_attempt.is_valid():
            question = Question.objects.get(id=id_question)
            attempt = Attempt(attempt=form_attempt.cleaned_data['attempt'],
                              question=question,
                              user=request.user)
            try:
                attempt.save()
            except Exception as exception:
                # TODO: do something else here, e.g., log it, show it to the user  -Rob Bednark 12/21/14
                pass
            # Redirect to the answer page
            return HttpResponseRedirect(reverse('answer', args=(attempt.id,)))
        else:
            # Assert: form is NOT valid
            # Need to return the errors to the template, and have the template show the errors.
            return render(request=request, 
                          template_name='question.html', 
                          dictionary=dict(form_attempt=form_attempt, 
                                         ))
    else:
        raise Exception("Unknown request.method=[%s]" % request.method)

@login_required(login_url='/login')
def answer(request, id_attempt):
    attempt = Attempt.objects.get(id=id_attempt)
    modelformset_usertag = _create_and_get_usertags(request=request)
    if request.method == 'GET':
        _get_tag2periods(user=request.user, modelformset_usertag=modelformset_usertag)
        form_schedule = FormSchedule()
        return render(request=request, 
                      template_name='answer.html', 
                      dictionary=dict(form_schedule=form_schedule, 
                                      modelformset_usertag=modelformset_usertag,
                                      question=attempt.question,
                                      answer=attempt.question.answer,
                                      attempt=attempt),
        )
    elif request.method == 'POST':
        # ASSERT: this is a POST, so the user answered a question
        # Show the correct answer, the user's attempt, and the question
        # Show a NEXT button to do a GET and get the next question
        form_schedule = FormSchedule(request.POST)
        if form_schedule.is_valid():
            schedule = Schedule(
                                interval_num=form_schedule.cleaned_data['interval_num'],
                                interval_unit=form_schedule.cleaned_data['interval_unit'],
                                question=attempt.question,
                                user=request.user)
            schedule.save()
            return HttpResponseRedirect(reverse('question_next'))
        else:
            # Assert: form is NOT valid
            # Need to return the errors to the template, and have the template show the errors.
            _get_tag2periods(user=request.user, modelformset_usertag=modelformset_usertag)
            return render(request=request, 
                          template_name='answer.html', 
                          dictionary=dict(form_schedule=form_schedule, 
                                          modelformset_usertag=modelformset_usertag,
                                          question=attempt.question,
                                          answer=attempt.question.answer,
                                          attempt=attempt),
        )
    else:
        raise Exception("Unknown request.method=[%s]" % request.method)
