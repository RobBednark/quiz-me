import os

from django.utils import timezone

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
        self.tag_names_for_question = None
        self.tag_names_selected = None

        self._question_queryset = None
        self._get_next_question(self)
        self._get_count_questions_before_now()

    def _get_count_questions_before_now(self):
        # Given self._queryset__questions_tagged,
        # count the number of questions that are scheduled before now.
        now = timezone.now()
        count = self._queryset__questions_tagged.filter(schedule__next_time__lte=now).count()
        self.count_questions_before_now = count

        
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
            raise ValueError(f'Invalid query_name: {self._query_name}')
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
    return Tag.objects.filter(id__in=tag_ids).exclude(user=user).values_list('id', flat=True)

def _tag_ids_that_dont_exist(tag_ids):
    """
    Given the list of tag_ids,
    return a list of all tag_ids in that list that do not exist.
    """
    existing_tag_ids = set(Tag.objects.filter(id__in=tag_ids).values_list('id', flat=True))
    non_existent_tag_ids = [tag_id for tag_id in tag_ids if tag_id not in existing_tag_ids]
    return non_existent_tag_ids