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

def get_next_question_unseen(user, tag_ids_selected):
    # Find all questions created by user which have one or more of tag_ids_selected.  Of those questions, find the ones that are unseen, i.e., have no schedules.  Of those, return the one with the oldest datetime_added.
    # tag_ids_selected -- list of tag IDs
    
    # Find questions created by the user with selected tags
    questions = Question.objects.filter(
        user=user,
        questiontag__tag__id__in=tag_ids_selected
    )

    # Filter for unseen questions (no schedules)
    unseen_questions = questions.filter(schedule__isnull=True)

    # Get the oldest unseen question based on datetime_added
    oldest_unseen_question = unseen_questions.order_by('datetime_added').first()

    return oldest_unseen_question

def get_next_question(user, query_name, tag_ids_selected):
    if tags_not_owned_by_user(user=user, tag_ids=tag_ids_selected):
        raise forms.TagNotOwnedByUserError(tag_ids_selected)
    if query_name == forms.QUERY_UNSEEN:
        question = get_next_question_unseen(user, tag_ids_selected)
    return question

def tags_not_owned_by_user(user, tag_ids):
    """
    Given the list of tag_ids,
    return a list of tag_ids that are not owned by the user.
    """
    return Tag.objects.filter(id__in=tag_ids).exclude(user=user).values_list('id', flat=True)