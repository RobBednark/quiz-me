import os

from dateutil.relativedelta import relativedelta
from django.db.models import OuterRef, Q, Subquery
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
        tag_ids_are_disabled = _tag_ids_that_are_disabled(tag_ids=tag_ids_selected)
        if tag_ids_are_disabled:
            raise Exception(tag_ids_are_disabled)
        
        self.question = None
        self.count_times_question_seen = None
        self.count_questions_before_now = None
        self.count_questions_matching = None
        self.count_questions_tagged = None
        self.count_recent_seen_mins_30 = None
        self.count_recent_seen_mins_60 = None
        self.tag_names_for_question = None
        self.tag_names_selected = None

        self._get_question()
        self._get_count_questions_before_now()
        self._get_count_recent_seen()
        self._get_count_times_question_seen()

    def _get_count_times_question_seen(self):
        # Get the count of schedules for the question
        # Precondition: self.question has been set
        # Side effects: set this attribute:
        #   self.count_times_question_seen

        self.count_times_question_seen = 0
        if self.question:
            self.count_times_question_seen = Schedule.objects.filter(question=self.question, user=self._user).count()

    def _get_count_questions_before_now(self):
        # Given self._queryset__questions_tagged,
        # count the number of questions that are scheduled before now.
        # Returns: None
        # Side effects: set this attribute:
        #   self.count_questions_before_now
        now = timezone.now()
        count = self._queryset__questions_tagged.filter(schedule__date_show_next__lte=now).count()
        self.count_questions_before_now = count
    
    def _get_count_recent_seen(self):
        # Side effects: set these attributes:
        #   self.count_recent_seen_mins_30
        #   self.count_recent_seen_mins_60
        now = timezone.now()
        thirty_minutes_ago = now - timezone.timedelta(minutes=30)
        sixty_minutes_ago = now - timezone.timedelta(minutes=60)
        
        schedules = Schedule.objects.filter(user=self._user)
        self.count_recent_seen_mins_30 = schedules.filter(datetime_added__gte=thirty_minutes_ago).count()
        self.count_recent_seen_mins_60 = schedules.filter(datetime_added__gte=sixty_minutes_ago).count()

    def OLD_UNUSED_get_next_question_due(self):
        # Find all questions created by user which have one or more of tag_ids_selected.  Of those questions, find the ones that are due, i.e., have a schedule with a date_show_next in the past.  For each of those questions, find the oldest Schedule.  Of those, return the question with the oldest Schedule.date_show_next.
        # Side effects: set the following attributes:
        #   self.question
        #   self.count_questions_tagged
        #   self.count_questions_matching

        # Find questions created by the user with selected tags
        # Get "tagged_questions" (questions that have one or more tag_ids).
        questions_tagged = Question.objects.filter(
            user=self._user,
            questiontag__tag__id__in=self._tag_ids_selected
        )

        # Get "scheduled_questions" (tagged_questions that have at least one schedule).
        scheduled_questions = questions_tagged.filter(schedule__isnull=False)
        
        # Get the newest schedule.date_added for each of the scheduled_questions ("newest_schedules").

        newest_schedules = Schedule.objects.filter(
            question__in=questions_with_schedules
        ).values('question').Max('datetime_added')
        


        latest_schedules = Schedule.objects.filter(
            question__in=questions_with_schedules
        ).values('question').annotate(
            latest_datetime_added=Max('datetime_added')
        )

        
        # For questions_tagged, annotate each one with the most recently-added Schedule
        questions_tagged = questions_tagged.annotate(
            newest_added_schedule=Subquery(
                Schedule.objects.filter(
                    question=OuterRef('pk'),
                    user=self._user
                ).order_by('-datetime_added')[0:1].values('id')
            )
        )
        
        # Of those schedules, look at the newest Schedule.datetime_added for each
        # question.  Of those newest Schedules,  find the oldest Schedule.date_show_next.
        # For each of the questions_with_schedules, find the newest Schedule.datetime_added for each question
        
        # Find the question with the oldest date_show_next among the latest schedules
        next_question = questions_with_schedules.annotate(
            latest_schedule_date=Subquery(
                latest_schedules.filter(question=OuterRef('pk')).values('latest_datetime_added')[:1]
            )
        ).filter(
            schedule__datetime_added=F('latest_schedule_date')
        ).order_by('schedule__date_show_next').first()
        
        self.question = next_question





        # For each of the questions_with_schedules, find the newest Schedule.datetime_added for each question
        questions_with_schedules = questions_tagged.filter(schedule__isnull=False)

        # For each of the questions_with_schedules, find the newest Schedule.datetime_added for each question

        # Filter for questions that are due (schedules with date_show_next in the past)
        questions_due = questions_tagged.filter(schedule__date_show_next__lte=timezone.now())

        # Get the question with the newest schedule.datetime_added
        oldest_due_question = questions_due.order_by('-schedule__datetime_added').first()
        self.question = oldest_due_question
        self.count_questions_tagged = questions_tagged.count()
        
    def _get_next_question_due(self):
        # Find all questions created by user which have one or more of tag_ids_selected.  Of those questions, find the ones that are due, i.e., with the newest schedule with a date_show_next in the past.  Of those, find the question with the oldest Schedule.date_show_next.
        # Side effects: set the following attributes:
        #   self.question
        #   self.count_questions_tagged
        #   self.count_questions_matching
        
        # Find questions created by the user with selected tags
        # Get "tagged_questions" (questions that have one or more tag_ids).
        questions_tagged = Question.objects.filter(
            user=self._user,
            questiontag__tag__id__in=self._tag_ids_selected
        )
        self._queryset__questions_tagged = questions_tagged

        # Get "scheduled_questions" (tagged_questions that have at least one schedule).
        scheduled_questions = questions_tagged.filter(schedule__isnull=False)
        
        # schedules -- all Schedules for the user for each question, newest first by datetime_added
        # OuterRef('pk') refers to the question.pk for each question
        schedules_for_question = (Schedule.objects
                     .filter(user=self._user, question=OuterRef('pk'))
                     .order_by('-datetime_added'))
        
        # questions_annotated - questions_tagged, annotated with (schedule).date_show_next
        # questions_annotated.date_show_next -- the Schedule.date_show_next for the most recent Schedule for each question
        scheduled_questions = scheduled_questions.annotate(date_show_next=Subquery(schedules_for_question[:1].values('date_show_next')))

        #  # add num_schedules_for_question field  [reference: https://stackoverflow.com/questions/43770118/simple-subquery-with-outerref/43771738]
        #  scheduled_questions = questions_annotated.annotate(num_schedules_for_question=Subquery(
        #      models.Schedule.objects
        #          .filter(question=OuterRef('pk'))
        #          .values('question')
        #          .annotate(count=Count('pk'))
        #          .values('count')))

        # question.schedule_datetime_added -- the datetime_added for the most recent Schedule for that question
        scheduled_questions = scheduled_questions.annotate(schedule_datetime_added=Subquery(schedules_for_question[:1].values('datetime_added')))
        subquery_by_date_show_next = Q(date_show_next__lte=timezone.now())
        scheduled_questions = scheduled_questions.filter(subquery_by_date_show_next)
        scheduled_questions = scheduled_questions.order_by('date_show_next')

        self.question = scheduled_questions.first()
        self.count_questions_tagged = questions_tagged.count()
        self.count_questions_matching = scheduled_questions.count()
            

    def _get_next_question_unseen(self):
        # Find all questions created by user which have one or more of tag_ids_selected.  Of those questions, find the ones that are unseen, i.e., have no schedules.  Of those, return the one with the oldest datetime_added.
        # Side effects: set the following attributes:
        #   self.question
        #   self.count_questions_tagged
        #   self.count_questions_matching
        
        # Find questions created by the user with selected tags
        questions_tagged = Question.objects.filter(
            user=self._user,
            questiontag__tag__id__in=self._tag_ids_selected
        )
        self._queryset__questions_tagged = questions_tagged

        # Filter for unseen questions (no schedules)
        unseen_questions = questions_tagged.filter(schedule__isnull=True)

        # Get the oldest unseen question based on datetime_added
        oldest_unseen_question = unseen_questions.order_by('datetime_added').first()
        self.question = oldest_unseen_question
        
        self.count_questions_tagged = questions_tagged.count()
        self.count_questions_matching = unseen_questions.count()

    def _get_question(self):
        if self._query_name == forms.QUERY_UNSEEN:
            self._get_next_question_unseen()
        elif self._query_name == forms.QUERY_DUE:
            self._get_next_question_due()
        else:
            raise ValueError(f'Invalid query_name: [{self._query_name}]')
        self._get_tag_names()
        self._get_count_times_question_seen()
    
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