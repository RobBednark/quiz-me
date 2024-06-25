from __future__ import unicode_literals
from six import python_2_unicode_compatible

from dateutil.relativedelta import relativedelta

from django.db import models
from django.utils import timezone

from emailusername.models import User

CHOICES_UNITS = (
    # db value   human-readable
    # --------   --------------
    ("seconds", "seconds"),
    ("minutes", "minutes"),
    ("hours",   "hours"),
    ("days",    "days"),
    ("weeks",   "weeks"),
    ("months",  "months"),
    ("years",   "years"),
)


class CreatedBy(models.Model):
    datetime_added = models.DateTimeField(auto_now_add=True)
    datetime_updated = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)

    class Meta:
        abstract = True

class QueryPreferences(CreatedBy):
    MAX_LENGTH_NAME = 1000

    name = models.TextField(max_length=MAX_LENGTH_NAME, null=False, default='')
    date_last_used = models.DateTimeField(null=True, default=None)

    ## Remove.  No longer needed.
    is_default = models.BooleanField(default=False)

    # Include unanswered questions (nulls) in first bucket query.
    # Does not affect order-by
    include_unanswered_questions = models.BooleanField(default=True)           # old: option_include_unanswered_questions
    
    # True  => for questions scheduled before now, only show questions that have answers
    # False => disable
    include_questions_with_answers = models.BooleanField(default=True)         # old: option_questions_with_answers_first
    
    
    # True  => for questions scheduled before now, only show questions that DON'T have answers
    # False => disable
    include_questions_without_answers = models.BooleanField(default=True)      # old: option_questions_without_answers_first

    # True  => date_show_next <= now
    # False => don't limit to date_show_next (desirable if want to order by
    #          answered count or when_answered, regardless of schedule)
    # Does not affect order-by
    limit_to_date_show_next_before_now = models.BooleanField(default=False)    # old: option_limit_to_date_show_next_before_now

    # True => order nulls first (for date_show_next, num_schedules, schedule_datetime_added)
    sort_by_nulls_first = models.BooleanField(default=False)                   # old: option_nulls_first

    # Takes precedence over all other order_by's
    sort_by_lowest_answered_count_first = models.BooleanField(default=False)   # old: option_order_by_answered_count
    sort_by_questions_with_answers_first = models.BooleanField(default=False)  # old: option_questions_with_answers_first

    # True  => order by when answered,  newest first (schedule_datetime_added DESC NULLS LAST)
    # False => order by date_show_next, oldest first (date_show_next ASC NULLS FIRST)
    # used with
    #   option_limit_to_date_show_next_before_now=True
    # to show questions to reinforce (see again quickly)
    sort_by_newest_answered_first = models.BooleanField(default=False)         # old: option_order_by_when_answered_newest

    # Takes precedence over all other order_by's, except for option_order_by_answered_count
    sort_by_oldest_answered_first = models.BooleanField(default=True)          # old: option_order_by_when_answered_oldest
 
    def __str__(self):
        return self.name
    

@python_2_unicode_compatible
class Question(CreatedBy):
    question = models.TextField()
    answer = models.ForeignKey('Answer', on_delete=models.SET_NULL, null=True, blank=True)
    # attempt_set
    # questiontag_set
    # schedule_set
    # tag_set
    # user
    # user_set

    def __str__(self):
        return '<Question id=[%s] question=[%s] datetime_added=[%s]>' % (self.id, self.question, self.datetime_added)


@python_2_unicode_compatible
class Answer(CreatedBy):
    answer = models.TextField()
    # question_set
    # user
    # user_set

    def __str__(self):
        return '<Answer id=[%s] answer=[%s] datetime_added=[%s]>' % (self.id, self.answer, self.datetime_added)


class Attempt(CreatedBy):
    attempt = models.TextField()
    question = models.ForeignKey('Question', on_delete=models.CASCADE, null=False)
    # user
    # user_set


@python_2_unicode_compatible
class Tag(CreatedBy):
    '''
        Each tag can be applied to each question for a given user.

        Each user can have many tags applied to many questions, e.g.,
            user_rob
                tag1: question1, question2
                tag2: question1, question3
    '''
    name = models.CharField(max_length=1000)
    questions = models.ManyToManyField('Question', blank=True, through='QuestionTag')
    # questiontag_set
    # user

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class QuestionTag(CreatedBy):
    # This is a tag applied to a question.
    # e.g., question = Question(text="1 + 1 = ??")
    #       tag_math = Tag(name="math")
    #       QuestionTag(question=question, tag=tag_math, enabled=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    enabled = models.BooleanField(default=False)
    # questions_set
    # user
    # user_set

    def __str__(self):
        return 'QuestionTag: tag.name=[%s] question.id=[%s]' % (self.tag.name, self.question.id)


class Schedule(CreatedBy):
    # A record indicating the next time that a question should be shown.
    date_show_next = models.DateTimeField(null=True, default=None)  # when to show the question next
    interval_num = models.DecimalField(max_digits=5, decimal_places=2, null=True, default=None)
    # interval_secs - number of seconds from when record was added until it should be shown again.
    interval_secs = models.IntegerField(null=True, default=None)
    interval_unit = models.TextField(choices=CHOICES_UNITS, null=True, default=None)
    percent_correct = models.DecimalField(max_digits=5, decimal_places=2, null=True, default=None)
    percent_importance = models.DecimalField(max_digits=5, decimal_places=2, null=True, default=None)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    # user

    def save(self, *args, **kwargs):
        # Note that datetime_added and datetime_updated are not set until super() is called.
        # Rather than doing 2 db calls, get a new timezone.now instead, which will be slightly off
        # (maybe a fraction of a second) from datetime_added and datetime_updated.
        time_now = timezone.now()
        if self.interval_num is not None:
            if self.interval_unit in ('months', 'years'):
                interval_num = int(self.interval_num)
            else:
                interval_num = float(self.interval_num)
        else:
            interval_num = 0
            self.interval_unit = 'seconds'
        interval = relativedelta(**({self.interval_unit: interval_num}))
        # TODO: set interval_secs
        if self.date_show_next:
            # It's already set, so don't modify it.  e.g., modifying the
            # schedule in the django admin.
            pass
        else:
            try:
                self.date_show_next = time_now + interval
            except TypeError as exception:
                print("Exception: interval_unit=[%s] interval_num=[%s] type(interval_num)=[%s] "
                      "exception=[%s]" % (
                          self.interval_unit, interval_num, type(interval_num), exception))
                raise
        return super(Schedule, self).save(*args, **kwargs)