from collections import namedtuple
from datetime import datetime
import os
from pprint import pformat, pprint
import pytz

from dateutil.relativedelta import relativedelta
from django.db import connection
from django.db.models import Count, F, OuterRef, Q, Subquery
from django.forms.models import model_to_dict

import questions.forms as forms
from questions.models import Question, QuestionTag, Schedule, Tag

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

def get_next_question_unseen(user, tags_selected):
    # Find all questions created by user which have one or more of tags_selected.  Of those questions, find the ones that are unseen, i.e., have no schedules.  Of those, return the one with the oldest datetime_added.
    # tags_selected -- list of tag IDs
    
    # Find questions created by the user with selected tags
    questions = Question.objects.filter(
        created_by=user,
        tags__name__in=tags_selected
    ).distinct()

    # Filter for unseen questions (no schedules)
    unseen_questions = questions.filter(schedules__isnull=True)

    # Get the oldest unseen question based on datetime_added
    oldest_unseen_question = unseen_questions.order_by('datetime_added').first()

    return oldest_unseen_question
def get_next_question(user, query_name, tags_selected):
    if query_name == forms.QUERY_UNSEEN:
        question = get_next_question_unseen(user, tags_selected)
    return question

def OLD_get_next_question(user, query_name, tags_selected):
    debug_print and print(f'\nquery_name: [{query_name}]\n')

    datetime_now = datetime.now(tz=pytz.utc)

    # tags -- Tags the user has selected that they want to be quizzed on right now
    tags = Tag.objects.filter(id__in=tags_selected)
    tag_names = tags.values_list('name', flat=True)
    
    # question_tags -- QuestionTags matching the tags the user wants to be quizzed on
    # (logical OR -- questions that match any (not all) of the tags)
    question_tags = QuestionTag.objects.filter(enabled=True, tag__in=tags)

    # questions_tagged -- Questions matching the question_tags
    questions_tagged = Question.objects.filter(questiontag__in=question_tags)
    count_questions_tagged = questions_tagged.count()

    # schedules -- all Schedules for the user for each question, newest first by datetime_added
    # "schedules" will be used as a subquery of Question (questions_tagged), so OuterRef('pk') will refer to the question.pk for each question in questions_tagged
    schedules = (Schedule.objects
                 .filter(user=user, question=OuterRef('pk'))
                 .order_by('-datetime_added'))
    
    # questions_annotated - questions_tagged, annotated with earliest (schedule).date_show_next
    # questions_annotated.date_show_next -- the Schedule.date_show_next for the most recent Schedule for each question
    questions_annotated = questions_tagged.annotate(date_show_next=Subquery(schedules[:1].values('date_show_next')))
    # add num_schedules field  [reference: https://stackoverflow.com/questions/43770118/simple-subquery-with-outerref/43771738]
    questions_annotated = questions_annotated.annotate(num_schedules=Subquery(
        Schedule.objects
            .filter(question=OuterRef('pk'))  # (OuterRef('pk') refers to the question.pk of the outer query for Question)  TODO: is this correct?  Isn't this a subquery of the Schedule subquery, so it should be OuterRefl(OuterRef()'pk'))?
            .values('question')  # restrict to only selecting the "question" field, and return a dict with just that field  TODO: where is this used?
            .annotate(count=Count('pk')) # TODO: what is this a count of?
            .values('count')))  # restrict to just the 'cound' column, and return a dict with just that field  TODO: where is "count" used?  Isn't the annotate() above already doing this?
    # question.schedule_datetime_added -- the datetime_added for the most recent Schedule for that question
    questions = questions_annotated.annotate(schedule_datetime_added=Subquery(schedules[:1].values('datetime_added')))
    subquery_include_unanswered = None

    SCHEDULES_SINCE_INTERVAL_30 = { 'minutes': 30 }
    SCHEDULES_SINCE_INTERVAL_60 = { 'minutes': 60 }
    delta_30 = relativedelta(**SCHEDULES_SINCE_INTERVAL_30)  # e.g., (minutes=30)
    delta_60 = relativedelta(**SCHEDULES_SINCE_INTERVAL_60)  # e.g., (minutes=30)
    schedules_since_30 = datetime_now - delta_30
    schedules_since_60 = datetime_now - delta_60
    schedules_recent_count_30 = (
        Schedule.objects
        .filter(user=user)
        .filter(datetime_added__gte=schedules_since_30)
        .count())
    schedules_recent_count_60 = (
        Schedule.objects
        .filter(user=user)
        .filter(datetime_added__gte=schedules_since_60)
        .count())

    count_questions_before_now = 0
    
    debug_print and _debug_print_questions(questions=questions, msg='query 1')

    num_schedules = Schedule.objects.filter(
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
