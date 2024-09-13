import os

import questions.forms as forms
from questions.models import Question, Tag

debug_print = eval(os.environ.get('QM_DEBUG_PRINT', 'False'))
debug_sql = eval(os.environ.get('QM_DEBUG_SQL', 'False'))

class TagNotOwnedByUserError(Exception):
    def __init__(self, tags):
        self.tags = tags
        message = f"The following tags are not owned by the user: {', '.join(tags)}"
        super().__init__(message)

class TagDoesNotExistError(Exception):
    def __init__(self, tag_ids):
        tag_ids_str = ', '.join(tag_ids)
        message = f"The following tag IDs do not exist: [{tag_ids_str}]"
        super().__init__(message)

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

class NextQuestion:
    def __init__(self, query_name, tag_ids_selected, user):
        self._query_name = query_name
        self._tag_ids_selected = tag_ids_selected
        self._user = user

        # TODO: combine the following exceptions into a single exception
        tags_not_owned = _tags_not_owned_by_user(user=user, tag_ids=tag_ids_selected)
        if tags_not_owned:
            raise TagNotOwnedByUserError(tags_not_owned)
        tag_ids_dont_exist = _tag_ids_that_dont_exist(tag_ids=tag_ids_selected)
        if tag_ids_dont_exist:
            raise TagDoesNotExistError(tag_ids_dont_exist)
        
        self.question = None
        self._get_next_question(self)

    def _get_next_question_unseen(self):
        # Find all questions created by user which have one or more of tag_ids_selected.  Of those questions, find the ones that are unseen, i.e., have no schedules.  Of those, return the one with the oldest datetime_added.
        # tag_ids_selected -- list of tag IDs
        
        # Find questions created by the user with selected tags
        questions = Question.objects.filter(
            user=self._user,
            questiontag__tag__id__in=self._tag_ids_selected
        )

        # Filter for unseen questions (no schedules)
        unseen_questions = questions.filter(schedule__isnull=True)

        # Get the oldest unseen question based on datetime_added
        oldest_unseen_question = unseen_questions.order_by('datetime_added').first()
        self.question = oldest_unseen_question

    def _get_question(self):
        if self._query_name == forms.QUERY_UNSEEN:
            self._get_next_question_unseen()
        else:
            raise ValueError(f'Invalid query_name: {self._query_name}')

def _tags_not_owned_by_user(user, tag_ids):
    """
    Given the list of tag_ids,
    return a list of tag_ids that are not owned by the user.
    """
    return Tag.objects.filter(id__in=tag_ids).exclude(user=user).values_list('id', flat=True)

def _tag_ids_that_dont_exist(tag_ids):
    """
    Given the list of tag_ids,
    return a list of all tag_ids in that list that do not exist.
    """
    existing_tag_ids = set(Tag.objects.filter(id__in=tag_ids).values_list('id', flat=True))
    non_existent_tag_ids = [tag_id for tag_id in tag_ids if tag_id not in existing_tag_ids]
    return non_existent_tag_ids