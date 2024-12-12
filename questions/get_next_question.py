import os

from django.db.models import F, Max, Min, OuterRef, Q, Subquery
from django.db.models.functions import Coalesce
from django.utils import timezone

from questions.forms import QUERY_OLDEST_DUE, QUERY_FUTURE, QUERY_REINFORCE, QUERY_UNSEEN, QUERY_OLDEST_DUE_OR_UNSEEN, QUERY_OLDEST_DUE_OR_UNSEEN_BY_TAG, QUERY_UNSEEN_BY_OLDEST_VIEWED_TAG, QUERY_UNSEEN_THEN_OLDEST_DUE
from questions.get_tag_hierarchy import expand_all_tag_ids, get_tag_hierarchy
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
        
        self._tag_hierarchy = get_tag_hierarchy(user=user)
        self._tag_ids_selected_expanded = expand_all_tag_ids(hierarchy=self._tag_hierarchy, tag_ids=self._tag_ids_selected)
        self._tag_ids_selected_implicit_descendants = self._tag_ids_selected_expanded - set(self._tag_ids_selected)
        
        self.count_questions_due = None  # questions due (date_show_next < now); does NOT include unseen questions
        self.count_questions_unseen = None  
        self.count_questions_tagged = None  # questions with at least one tag in self._tag_ids_selected_expanded
        self.count_recent_seen_mins_30 = None  # questions seen in the last 30 minutes
        self.count_recent_seen_mins_60 = None  # questions seen in the last 60 minutes
        self.count_times_question_seen = None
        
        self.question = None

        self.tag_names_for_question = None  # list of tag names for the question
        self.tag_names_selected = None  # list of tag names for the tags selected for the query
        self.tag_names_selected_implicit_descendants = None  # list of tag names for the tags selected for the query
        
        self._queryset__questions_tagged = None

        self._get_question()
        self._get_all_counts()

    def _get_all_counts(self):
        # Returns: None
        # Side effects: set the following attributes:
        #   self.count_questions_due
        #   self.count_questions_unseen
        #   self.count_questions_tagged
        #   self.count_recent_seen_mins_30
        #   self.count_recent_seen_mins_60
        #   self.count_times_question_seen
        
        self._get_count_recent_seen()
        self._get_count_questions_due()
        self._get_count_questions_unseen()
        self._get_count_times_question_seen()
        
    def _get_count_questions_due(self):
        # Given self._queryset__questions_tagged,
        # count the number of questions that are scheduled before now (not including unseen questions).
        # Returns: None
        # Side effects: set this attribute:
        #   self.count_questions_due
        if self._queryset__questions_tagged is None:
            self._queryset__questions_tagged = Question.objects.filter(
                user=self._user,
                questiontag__tag__id__in=self._tag_ids_selected_expanded)

        subquery_latest_dateshownext_for_question = Schedule.objects.filter(
            question=OuterRef('pk'),
            user=self._user
        ).order_by('-datetime_added')

        self.count_questions_due = self._queryset__questions_tagged.annotate(
            latest_date_show_next=Subquery(subquery_latest_dateshownext_for_question.values('date_show_next')[:1])
        ).filter(Q(latest_date_show_next__lte=timezone.now())
        ).distinct().count()
    
    def _get_count_questions_unseen(self):
        # Given self._queryset__questions_tagged,
        # count the number of questions that are unseen.
        # Returns: None
        # Side effects: set this attribute:
        #   self.count_questions_unseen
        self.count_questions_unseen = self._queryset__questions_tagged.filter(
            schedule__isnull=True).distinct().count()
        
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
        
        # Find questions created by the user with selected tags
        # Get "tagged_questions" (questions that have one or more tag_ids).
        questions_tagged = Question.objects.filter(
            user=self._user,
            questiontag__tag__id__in=self._tag_ids_selected_expanded
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
        scheduled_questions = scheduled_questions.annotate(sched_date_added=Subquery(schedules_for_question[:1].values('datetime_added')))

        if self._query_name in [QUERY_OLDEST_DUE, QUERY_REINFORCE, QUERY_UNSEEN_THEN_OLDEST_DUE]:
            subquery_by_date_show_next = Q(date_show_next__lte=timezone.now())
        elif self._query_name == QUERY_FUTURE:
            subquery_by_date_show_next = Q(date_show_next__gt=timezone.now())
        else:
            raise ValueError(f"Unknown query name for get_next_question_due: [{self._query_name}]")

        scheduled_questions = scheduled_questions.filter(subquery_by_date_show_next)
        scheduled_questions = scheduled_questions.distinct()

        if self._query_name == QUERY_REINFORCE:
            # Pick the question with the newest Schedule.date_added
            scheduled_questions = scheduled_questions.order_by('-sched_date_added')
            self.question = scheduled_questions.first()
        elif self._query_name in [QUERY_OLDEST_DUE, QUERY_FUTURE, QUERY_UNSEEN_THEN_OLDEST_DUE]:
            # Pick the question with the oldest Schedule.date_show_next
            scheduled_questions = scheduled_questions.order_by('date_show_next')
            self.question = scheduled_questions.first()
        else: 
            raise ValueError(f"Unknown query name for get_next_question_due: [{self._query_name}]")

        self.count_questions_tagged = questions_tagged.distinct().count()

    def _get_next_question_oldest_due_or_unseen(self):
        ####### TODO: naming - what to call this?  
        #######     oldest_due_or_unseen
        #######     due_or_unseen
        #######     due_or_added
        #######     last_seen  (no; misleading; it might be due a year from now)
        #######  It's not really "latest" due or unseen date.  It's just due or unseen date.  


        # Return the question that is the oldest due or unseen for the given self._tag_ids_selected and self._user .
        # This means the question with the older of:
        #   a) the oldest Schedule.date_show_next
        #   -or-, if no Schedules for a question (unseen), then:
        #   b) the oldest Question.datetime_added.

        # Get questions with selected tags
        questions_tagged = Question.objects.filter(
            user=self._user,
            questiontag__tag__id__in=self._tag_ids_selected_expanded
        )
        self._queryset__questions_tagged = questions_tagged
    
        # Get the latest schedule for each question
        subquery_latest_schedule = Schedule.objects.filter(
            question=OuterRef('pk'),
            user=self._user
        ).order_by('-datetime_added')
    
        # Annotate questions with either their latest schedule's date_show_next or their creation date
        # Coalesce() takes the first non-null value from the list of arguments.
        questions = questions_tagged.annotate(
            due_or_unseen_date=Coalesce(
                Subquery(subquery_latest_schedule.values('date_show_next')[:1]),  # due date
                F('datetime_added')  # date the unseen question was added
            )
        ).distinct()
    
        # Order by the oldest due/created date and get the first one
        self.question = questions.order_by('due_or_unseen_date').first()
        
        # Set counts
        self.count_questions_tagged = questions_tagged.distinct().count()

    def _get_next_question_oldest_due_or_unseen_by_tag(self):
        pass

    def _get_next_question_unseen(self):
        # Find all questions created by user which have one or more of tag_ids_selected.  Of those questions, find the ones that are unseen, i.e., have no schedules.  Of those, return the one with the oldest datetime_added.
        # Side effects: set the following attributes:
        #   self.question
        #   self.count_questions_tagged
        
        # Find questions created by the user with selected tags
        questions_tagged = Question.objects.filter(
            user=self._user,
            questiontag__tag__id__in=self._tag_ids_selected_expanded
        )
        self._queryset__questions_tagged = questions_tagged

        # Filter for unseen questions (no schedules)
        unseen_questions = questions_tagged.filter(schedule__isnull=True)

        # Get the oldest unseen question based on datetime_added
        oldest_unseen_question = unseen_questions.order_by('datetime_added').first()
        self.question = oldest_unseen_question
        
        self.count_questions_tagged = questions_tagged.distinct().count()
        
    def _get_next_question_unseen_by_oldest_viewed_tag(self):
        # "oldest-viewed tag" means the tag with the older of the oldest Schedule.datetime_viewed,  or if no Schedules, then the oldest Question.datetime_added.
        # Find all tags that have at least one unseen question.
        # For those tags, get the newest Schedule.datetime_added.  
        # If there are no schedules for a tag, then get the oldest Question.datetime_added.
        # Choose the tag with the oldest of those dates, and use the oldest unseen Question.datetime_added for that tag.
        # Note: we don't want to use only unseen_question.datetime_added, because I don't want to see multiple questions from the same tag in a row.  That could be the same as QUERY_UNSEEN.

        subquery_newest_schedule_dateadded_for_tag = Schedule.objects.filter(
            question__questiontag__tag=OuterRef('pk'),
            user=self._user
        ).order_by('-datetime_added').values('datetime_added')[:1]

        subquery_oldest_unseen_question_dateadded_for_tag = Question.objects.filter(
            questiontag__tag=OuterRef('pk'),
            user=self._user,
            schedule__isnull=True
        ).order_by('datetime_added').values('datetime_added')[:1]

        # oldest_tags may result in multiple matches per tag (multiple unseen questions), with each one of those for the same tag having the same relevant_date.
        # That won't matter, since we're ordering my relevant_date, selecting only the first (oldest) one.
        oldest_tags = Tag.objects.filter(
            questiontag__question__user=self._user,
            questiontag__question__schedule__isnull=True,  # only select tags with unseen questions
            id__in=self._tag_ids_selected_expanded
        ).annotate(
            newest_schedule_dateadded_for_tag=Subquery(subquery_newest_schedule_dateadded_for_tag),
            oldest_unseen_question_dateadded_for_tag=Subquery(subquery_oldest_unseen_question_dateadded_for_tag),
            relevant_date=Coalesce( # use the first non-null value (the newest schedule date if it exists, otherwise the oldest question date)
                F('newest_schedule_dateadded_for_tag'),
                F('oldest_unseen_question_dateadded_for_tag')
            )
        ).order_by('relevant_date')
        oldest_tag = oldest_tags.first()

        # Get the oldest unseen question for the oldest tag
        self.question = None
        if oldest_tag:
            self.question = Question.objects.filter(
                questiontag__tag=oldest_tag,
                user=self._user,
                schedule__isnull=True
            ).order_by('datetime_added').first()

        # Set counts
        self.count_questions_tagged = Question.objects.filter(
            user=self._user,
            questiontag__tag__id__in=self._tag_ids_selected_expanded
        ).distinct().count()
        # Count the number of tags that have at least one unseen question

    def _get_next_question_unseen_then_oldest_due(self):
        self._get_next_question_unseen()
        if not self.question:
            self._get_next_question_due()
        

    def _get_question(self):
        if self._query_name in [QUERY_OLDEST_DUE, QUERY_FUTURE, QUERY_REINFORCE]:
            self._get_next_question_due()
        elif self._query_name == QUERY_UNSEEN:
            self._get_next_question_unseen()
        elif self._query_name == QUERY_UNSEEN_BY_OLDEST_VIEWED_TAG:
            self._get_next_question_unseen_by_oldest_viewed_tag()
        elif self._query_name == QUERY_UNSEEN_THEN_OLDEST_DUE:
            self._get_next_question_unseen_then_oldest_due()
        elif self._query_name == QUERY_OLDEST_DUE_OR_UNSEEN:
            self._get_next_question_oldest_due_or_unseen()
        elif self._query_name == QUERY_OLDEST_DUE_OR_UNSEEN_BY_TAG:
            self._get_next_question_oldest_due_or_unseen_by_tag()
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
                    ) for qtag in self.question.questiontag_set.all()
                ])
        
        self.tag_names_selected = [
            # Note: _tag_ids_selected, not _tag_ids_selected_expanded
            str(tag.name) for tag in Tag.objects.filter(id__in=self._tag_ids_selected)
        ]
        
        self.tag_names_selected_implicit_descendants = [
            str(tag.name) for tag in Tag.objects.filter(id__in=self._tag_ids_selected_implicit_descendants)
        ]