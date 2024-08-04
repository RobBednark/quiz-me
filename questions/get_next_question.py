from collections import namedtuple
from datetime import datetime
import os
from pprint import pformat, pprint
import pytz

from dateutil.relativedelta import relativedelta
from django.db import connection
from django.db.models import Count, F, OuterRef, Q, Subquery
from django.forms.models import model_to_dict

from questions import models

debug_print = eval(os.environ.get('QM_DEBUG_PRINT', 'False'))
debug_sql = eval(os.environ.get('QM_DEBUG_SQL', 'False'))

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
        'selected_tag_names'
    ]
)

def _debug_print_questions(questions, msg):
    if not debug_print:
        return
    NUM_QUESTIONS_FIRST = 2
    NUM_QUESTIONS_LAST = 2
    _debug_print_n_questions(questions=questions, msg=msg, num_questions=NUM_QUESTIONS_FIRST)
    _debug_print_n_questions(questions=questions, msg=msg, num_questions= -NUM_QUESTIONS_LAST)
    print()
        
def _debug_print_n_questions(questions, msg, num_questions):
    if not debug_print:
        return
    print("=" * 80)
    LENGTH_QUESTION = 50
    questions_count = questions.count()

    if num_questions == 0:
        first_or_last = '(show none)'
    elif num_questions > 0:
        first_or_last = 'first'
        questions = questions[:num_questions]
    else:
        first_or_last = 'last'
        questions = list(questions)
        questions = questions[num_questions:]
    print(f'[{first_or_last:5}] questions (): {msg}')
    for idx, question in enumerate(questions):
        num_question = idx + 1
        print()
        question_text = question.question
        question_text = question_text.replace('\r','')
        question_text = question_text.replace('\n',' ')
        question_text = question_text.strip()
        question_text = question_text[:LENGTH_QUESTION]
        if num_questions < 0:
            # assert: num_questions is negative (e.g., -5), so adding it to count is really subtraction
            num_of_count = questions_count + num_questions + num_question
        else:
            num_of_count = num_question
        
        # print annotations
        try:
            schedule_datetime_added = question.schedule_datetime_added
        except AttributeError:
            # assert: schedule_datetime_added annotation is not present
            schedule_datetime_added = None

        try:
            date_show_next = question.date_show_next
        except AttributeError:
            # assert: date_show_next annotation is not present
            date_show_next = None

        try:
            num_schedules = question.num_schedules
        except AttributeError:
            # assert: num_schedules annotation is not present
            num_schedules = None

        print(f'question [{num_of_count}/{questions_count}]  [{num_question}/{num_questions}]  pk=[{question.pk}] text=[{question_text}]')
        print(f'schedule.date_show_next: {date_show_next}')
        print(f'question.datetime_added: {question.datetime_added}')
        print(f'schedule_datetime_added: {schedule_datetime_added}')
        print(f'num_schedules: {num_schedules}')
        
        if question.answer:
            answer_text = question.answer.answer
            answer_text = answer_text.replace('\r','')
            answer_text = answer_text.replace('\n',' ')
            answer_text = answer_text.strip()
            answer_text = answer_text[:LENGTH_QUESTION]
            print(f'answer: {question.answer.answer[:LENGTH_QUESTION]}')
        else:
            print('answer: None')

def get_next_question(user, query_prefs_obj, tags_selected):
    # query_prefs_obj -- QueryPrefs object
    # tags_selected -- 
    
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
    # 1. schedule.date_show_next (null=unseen)
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
    # 2) Order by schedule.date_show_next, but show unanswered questions first (questions recently-answered that should be seen quickly again will come after unanswered questions)
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

    assert query_prefs_obj is not None
    debug_print and print('\nquery_prefs_obj:\n' + pformat(model_to_dict(query_prefs_obj)))

    datetime_now = datetime.now(tz=pytz.utc)

    # tags -- Tags the user has selected that they want to be quizzed on right now
    tags = models.Tag.objects.filter(id__in=tags_selected)
    tag_names = tags.values_list('name', flat=True)
    
    # question_tags -- QuestionTags matching the tags the user wants to be quizzed on
    # (logical OR -- questions that match any (not all) of the tags)
    question_tags = models.QuestionTag.objects.filter(enabled=True, tag__in=tags)

    # questions_tagged -- Questions matching the question_tags
    questions_tagged = models.Question.objects.filter(questiontag__in=question_tags)
    count_questions_tagged = questions_tagged.count()

    # schedules -- all Schedules for the user for each question, newest first by datetime_added
    # "schedules" will be used as a subquery of Question (questions_tagged), so OuterRef('pk') will refer to the question.pk for each question in questions_tagged
    schedules = (models.Schedule.objects
                 .filter(user=user, question=OuterRef('pk'))
                 .order_by('-datetime_added'))
    
    # questions_annotated - questions_tagged, annotated with earliest (schedule).date_show_next
    # questions_annotated.date_show_next -- the Schedule.date_show_next for the most recent Schedule for each question
    questions_annotated = questions_tagged.annotate(date_show_next=Subquery(schedules[:1].values('date_show_next')))
    # add num_schedules field  [reference: https://stackoverflow.com/questions/43770118/simple-subquery-with-outerref/43771738]
    questions_annotated = questions_annotated.annotate(num_schedules=Subquery(
        models.Schedule.objects
            .filter(question=OuterRef('pk'))  # (OuterRef('pk') refers to the question.pk of the outer query for Question)  TODO: is this correct?  Isn't this a subquery of the Schedule subquery, so it should be OuterRefl(OuterRef()'pk'))?
            .values('question')  # restrict to only selecting the "question" field, and return a dict with just that field  TODO: where is this used?
            .annotate(count=Count('pk')) # TODO: what is this a count of?
            .values('count')))  # restrict to just the 'cound' column, and return a dict with just that field  TODO: where is "count" used?  Isn't the annotate() above already doing this?
    # question.schedule_datetime_added -- the datetime_added for the most recent Schedule for that question
    questions = questions_annotated.annotate(schedule_datetime_added=Subquery(schedules[:1].values('datetime_added')))
    subquery_include_unanswered = None
    if query_prefs_obj.include_unanswered_questions:
        # Include unanswered questions (nulls) in first bucket query.
        # Does not affect order-by.
        subquery_include_unanswered = Q(date_show_next__isnull=True)
    subquery_by_date_show_next = None
    if query_prefs_obj.limit_to_date_show_next_before_now:
        subquery_by_date_show_next = Q(date_show_next__lte=datetime_now)
    if query_prefs_obj.include_questions_with_answers:
        # True  => for questions scheduled before now, only show questions that have answers
        # False => disabled
        questions = questions.filter(answer__isnull=False)
    if query_prefs_obj.include_questions_without_answers:
        # True  => for questions scheduled before now, only show questions that DON'T have answers
        # False => disabled
        questions = questions.filter(answer__isnull=True)

    if subquery_include_unanswered and subquery_by_date_show_next:
        # True  => date_show_next <= now
        # False => don't limit to date_show_next (desirable if want to order by
        #          answered count or when_answered, regardless of schedule)
        # Does not affect order-by.
        questions = questions.filter(subquery_include_unanswered | subquery_by_date_show_next)
    elif subquery_include_unanswered:
        questions = questions.filter(subquery_include_unanswered)
    elif subquery_by_date_show_next:
        questions = questions.filter(subquery_by_date_show_next)
    order_by = []
    
    # sort_by_nulls_first (used for all four order_by's):
    # True => order nulls first (for date_show_next, num_schedules, schedule_datetime_added)

    if query_prefs_obj.sort_by_lowest_answered_count_first:
        # Takes precedence over all other order_by's
        # nulls_first parm must be True or None
        order_by.append(F('num_schedules').asc(nulls_first=query_prefs_obj.sort_by_nulls_first if query_prefs_obj.sort_by_nulls_first else None))

    if query_prefs_obj.sort_by_oldest_answered_first:
        # Takes precedence over all other order_by's, except for option_order_by_answered_count
        # True  => order by when answered,  newest first (schedule_datetime_added DESC NULLS LAST)
        # False => order by date_show_next, oldest first (date_show_next ASC NULLS FIRST)
        # used with
        #   option_limit_to_date_show_next_before_now=True
        # to show questions to reinforce (see again quickly)
        #
        # Order by the time when the user last answered the question, oldest first
        order_by.append(F('schedule_datetime_added').asc(nulls_first=query_prefs_obj.sort_by_nulls_first if query_prefs_obj.sort_by_nulls_first else None))

    if query_prefs_obj.sort_by_newest_answered_first:
        # Order by the time when the user last answered the question, newest first
        order_by.append(F('schedule_datetime_added').desc(nulls_first=query_prefs_obj.sort_by_nulls_first if query_prefs_obj.sort_by_nulls_first else None))
    else:
        # Order by when the question should be shown again
        order_by.append(F('date_show_next').asc(nulls_first=query_prefs_obj.sort_by_nulls_first if query_prefs_obj.sort_by_nulls_first else None))
    # For unanswered questions , order by the time the question was added, oldest first.
    order_by.append(F('datetime_added').asc())
    debug_print and print('order_by:\n' + pformat(order_by))
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
    
    debug_print and _debug_print_questions(questions=questions, msg='query 1')
    # query #1
    if questions:
        # Show questions whose schedule.date_show_next <= now
        # assert: there is a question with schedule.date_show_next <= now
        count_questions_before_now = questions.count()
        debug_print and print('first "if": questions.count() = [%s] questions scheduled before now' % count_questions_before_now)
        debug_sql and pprint(connection.queries[-1], width=100)
        question_to_show = questions[0]
    else:
        # assert: no question with schedule.date_show_next <= now
        # Look for questions with no schedules, and show the one with the
        # oldest question.datetime_added
        
        # TODO: CHECK: using questions_tagged here, but query #3 is using questions_annotated -- is that correct?
        questions = questions_tagged
        questions = questions.filter(schedule=None)
        debug_print and print("order_by('question.datetime_added')")
        questions = questions.order_by('datetime_added')
        debug_print and _debug_print_questions(questions=questions, msg='query 2 (schedule=None, order_by(datetime_added) (AKA unanswered questions / no schedule)')

        # query #2
        if questions:
            debug_print and print('unanswered questions found, count = [%s]' % questions.count())
            debug_sql and pprint(connection.queries[-1], width=100)
            question_to_show = questions[0]
        else:
            debug_sql and pprint(connection.queries[-1], width=100)
            # assert: no question without a schedule
            # Return the question with the oldest schedule.date_show_next
            # query #3
            questions = questions_annotated
            questions = questions.order_by('date_show_next') # ascending
            debug_print and _debug_print_questions(questions=questions, msg='query 3 (order by schedule.date_show_next ASC; use the oldest)')
            if questions:
                debug_print and print('scheduled questions found, count=[%s]' % questions.count())
                question_to_show = questions[0]
            else:
                debug_print and print('No questions whatsoever')
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
        option_limit_to_date_show_next_before_now=query_prefs_obj.limit_to_date_show_next_before_now,
        question=question_to_show,
        schedules_recent_count_30=schedules_recent_count_30,
        schedules_recent_count_60=schedules_recent_count_60,
        selected_tag_names=sorted([tag for tag in tag_names]),  # query #5
        num_schedules=num_schedules,
    )