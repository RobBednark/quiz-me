import os

from django.db.models import OuterRef, Q, Subquery
from django.utils import timezone

import questions.forms as forms
from questions.models import Question, Schedule, Tag
from questions.VerifyTagIds import VerifyTagIds

debug_print = eval(os.environ.get('QM_DEBUG_PRINT', 'False'))
debug_sql = eval(os.environ.get('QM_DEBUG_SQL', 'False'))

class NextQuestion:
    def __init__(self, query_name, tag_ids_selected, user):
        self._query_name = query_name
        self._tag_ids_selected = tag_ids_selected
        self._user = user

        VerifyTagIds(tag_ids=tag_ids_selected, user=user)
        
        self.count_questions_due = None  # questions due (date_show_next < now); does NOT include unseen questions
        self.count_questions_matched_criteria = None  # all criteria, e.g., tags, unseen, due, ...
        self.count_questions_tagged = None
        self.count_recent_seen_mins_30 = None  # questions seen in the last 30 minutes
        self.count_recent_seen_mins_60 = None  # questions seen in the last 60 minutes
        self.count_times_question_seen = None
        
        self.question = None

        self.tag_names_for_question = None  # list of tag names for the question
        self.tag_names_selected = None  # list of tag names for the tags selected for the query

        self._get_question()
        self._get_count_questions_due()
        self._get_count_questions_matched_criteria()
        self._get_count_recent_seen()

    def _get_count_questions_due(self):
        # Given self._queryset__questions_tagged,
        # count the number of questions that are scheduled before now.
        # Returns: None
        # Side effects: set this attribute:
        #   self.count_questions_due
        now = timezone.now()
        
         # Subquery to get the most recent schedule for each question
        question_latest_schedule = Schedule.objects.filter(
            question=OuterRef('pk'),
            user=self._user
        ).order_by('-datetime_added')

        # Annotate questions with their latest schedule's date_show_next
        questions_with_latest_schedule = self._queryset__questions_tagged.annotate(
            latest_date_show_next=Subquery(question_latest_schedule.values('date_show_next')[:1])
        )
    
        # Count questions where the latest schedule's date_show_next is less than or equal to now
        self.count_questions_due = questions_with_latest_schedule.filter(
            latest_date_show_next__lte=now
        ).count()
    
    def _get_count_questions_matched_criteria(self):
        if self._query_name == forms.QUERY_DUE:
            # assert: it was already set in _get_count_questions_due()
            pass
        elif self._query_name == forms.QUERY_UNSEEN:
            # assert: it was already set in _get_count_questions_unseen()
            pass
        elif self._query_name == forms.QUERY_UNSEEN_THEN_DUE:
            self._get_count_questions_matched_criteria_unseen_then_due()

    def _get_count_questions_matched_criteria_unseen_then_due(self):
        now = timezone.now()
        
        # Subquery to get the most recent schedule for each question
        latest_schedule = Schedule.objects.filter(
            question=OuterRef('pk'),
            user=self._user
        ).order_by('-datetime_added')

        # Count of questions that are either unseen or due based on their latest schedule
        self.count_questions_matched_criteria = self._queryset__questions_tagged.annotate(
            latest_date_show_next=Subquery(latest_schedule.values('date_show_next')[:1])
        ).filter(
            Q(schedule__isnull=True) |  # Unseen questions
            Q(latest_date_show_next__lte=now)  # Due questions
        ).distinct().count()
    
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

    def _get_count_times_question_seen(self):
        # Get the count of schedules for the question
        # Precondition: self.question has been set
        # Side effects: set this attribute:
        #   self.count_times_question_seen

        self.count_times_question_seen = 0
        if self.question:
            self.count_times_question_seen = Schedule.objects.filter(question=self.question, user=self._user).count()

    def _get_next_question_due(self):
        # Find all questions created by user which have one or more of tag_ids_selected.  Of those questions, find the ones that are due, i.e., with the newest schedule with a date_show_next in the past.  Of those, find the question with the oldest Schedule.date_show_next.
        # Side effects: set the following attributes:
        #   self.question
        #   self.count_questions_tagged
        #   self.count_questions_matched_criteria
        
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
        # Only use the newest schedule for each question
        scheduled_questions = scheduled_questions.annotate(date_show_next=Subquery(schedules_for_question[:1].values('date_show_next')))
        subquery_by_date_show_next = Q(date_show_next__lte=timezone.now())
        scheduled_questions = scheduled_questions.filter(subquery_by_date_show_next)
        scheduled_questions = scheduled_questions.order_by('date_show_next')

        self.question = scheduled_questions.first()
        self.count_questions_tagged = questions_tagged.count()
        self.count_questions_matched_criteria = scheduled_questions.count()
            
    def _get_next_question_unseen(self):
        # Find all questions created by user which have one or more of tag_ids_selected.  Of those questions, find the ones that are unseen, i.e., have no schedules.  Of those, return the one with the oldest datetime_added.
        # Side effects: set the following attributes:
        #   self.question
        #   self.count_questions_tagged
        #   self.count_questions_matched_criteria
        
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
        self.count_questions_matched_criteria = unseen_questions.count()

    def _get_next_question_unseen_then_due(self):
        # First, try to get an unseen question
        self._get_next_question_unseen()
        if not self.question:
            self._get_next_question_due()
        

    def _get_question(self):
        if self._query_name == forms.QUERY_DUE:
            self._get_next_question_due()
        elif self._query_name == forms.QUERY_UNSEEN:
            self._get_next_question_unseen()
        elif self._query_name == forms.QUERY_UNSEEN_THEN_DUE:
            self._get_next_question_unseen_then_due()
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