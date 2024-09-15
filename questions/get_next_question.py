from datetime import datetime
import os

from dateutil.relativedelta import relativedelta
from django.utils import timezone
import pytz

import questions.forms as forms
from questions.models import Question, Schedule, Tag

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
        self.count_questions_before_now = None
        self.count_questions_tagged = None
        self.schedules_recent_count_30 = None
        self.schedules_recent_count_60 = None
        self.tag_names_for_question = None
        self.tag_names_selected = None

        self._question_queryset = None
        self._get_question()
        self._get_count_questions_before_now()
        self._get_count_recent_schedules()

    def _get_count_questions_before_now(self):
        # Given self._queryset__questions_tagged,
        # count the number of questions that are scheduled before now.
        now = timezone.now()
        count = self._queryset__questions_tagged.filter(schedule__date_show_next__lte=now).count()
        self.count_questions_before_now = count
    
    def _get_count_recent_schedules(self):
        SCHEDULES_SINCE_INTERVAL_30 = { 'minutes': 30 }
        SCHEDULES_SINCE_INTERVAL_60 = { 'minutes': 60 }
        delta_30 = relativedelta(**SCHEDULES_SINCE_INTERVAL_30)  # e.g., (minutes=30)
        delta_60 = relativedelta(**SCHEDULES_SINCE_INTERVAL_60)  # e.g., (minutes=30)
        datetime_now = datetime.now(tz=pytz.utc)
        schedules_since_30 = datetime_now - delta_30
        schedules_since_60 = datetime_now - delta_60
        self.schedules_recent_count_30 = (
            Schedule.objects
            .filter(user=self._user)
            .filter(datetime_added__gte=schedules_since_30)
            .count())
        self.schedules_recent_count_60 = (
            Schedule.objects
            .filter(user=self._user)
            .filter(datetime_added__gte=schedules_since_60)
            .count())
        
    def _get_next_question_unseen(self):
        # Find all questions created by user which have one or more of tag_ids_selected.  Of those questions, find the ones that are unseen, i.e., have no schedules.  Of those, return the one with the oldest datetime_added.
        # tag_ids_selected -- list of tag IDs
        
        # Find questions created by the user with selected tags
        questions_tagged = Question.objects.filter(
            user=self._user,
            questiontag__tag__id__in=self._tag_ids_selected
        )
        self._queryset__questions_tagged = questions_tagged
        self.count_questions_tagged = questions_tagged.count()

        # Filter for unseen questions (no schedules)
        unseen_questions = questions_tagged.filter(schedule__isnull=True)
        self._question_queryset = unseen_questions

        # Get the oldest unseen question based on datetime_added
        oldest_unseen_question = unseen_questions.order_by('datetime_added').first()
        self.question = oldest_unseen_question

    def _get_question(self):
        if self._query_name == forms.QUERY_UNSEEN:
            self._get_next_question_unseen()
        else:
            raise ValueError(f'Invalid query_name: [{self._query_name}]')
        self._get_tag_names()
    
    def _get_tag_names(self):
        self.tag_names_for_question = []
        if self.question:
            self.tag_names_for_question = \
                sorted([
                    str(
                        qtag.tag.name
                    ) for qtag in self.question.questiontag_set.filter(enabled=True)
                ])
        
        # Get the tag names for the selected tags
        self.tag_names_selected = [
            str(tag.name) for tag in Tag.objects.filter(id__in=self._tag_ids_selected)
        ]


def _tags_not_owned_by_user(user, tag_ids):
    """
    Given the list of tag_ids,
    return a list of tag_ids that are not owned by the user.
    """
    ids_not_owned_by_user = Tag.objects.filter(id__in=tag_ids).exclude(user=user).values_list('id', flat=True)
    return [str(tag_id) for tag_id in ids_not_owned_by_user]

def _tag_ids_that_dont_exist(tag_ids):
    """
    Given the list of tag_ids,
    return a list of all tag_ids in that list that do not exist.
    """
    existing_tag_ids = set(Tag.objects.filter(id__in=tag_ids).values_list('id', flat=True))
    non_existent_tag_ids = [str(tag_id) for tag_id in tag_ids if tag_id not in existing_tag_ids]
    return non_existent_tag_ids