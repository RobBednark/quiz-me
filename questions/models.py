#from datetime import timedelta
from dateutil.relativedelta import relativedelta

from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone

from emailusername.models import User

CHOICES_UNITS = (
    #  db value   human-readable
    #  --------   --------------
      ("immediately", "immediately"),
      ("seconds", "seconds"),
      ("minutes", "minutes"),
      ("hours",   "hours"),
      ("days",    "days"),
      ("weeks",   "weeks"),
      ("months",  "months"),
      ("years",   "years"),
      ("never",   "never"),
)

class CreatedBy(models.Model):
    datetime_added = models.DateTimeField(auto_now_add=True)
    datetime_updated = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, null=True)

    class Meta:
        abstract = True


class Question(CreatedBy):
    question = models.TextField()
    answer = models.ForeignKey('Answer', null=True, blank=True)
    # attempt_set
    # questiontag_set
    # schedule_set
    # tag_set
    # user
    # user_set

    def __unicode__(self):
        return '<Question question=[%s] datetime_added=[%s]>' % (self.question, self.datetime_added)


class Answer(CreatedBy):
    answer = models.TextField()
    # hint_set
    # question_set
    # user
    # user_set

    def __unicode__(self):
        return '<Answer answer=[%s] datetime_added=[%s]>' % (self.answer, self.datetime_added)


class Attempt(CreatedBy):
    attempt = models.TextField()
    question = models.ForeignKey('Question', null=False)
    # user
    # user_set


class Hint(CreatedBy):
    answer = models.ForeignKey('Answer', null=True)
    hint = models.TextField()
    # user
    # user_set


class Tag(CreatedBy):
    '''
        Each tag can be applied to each question for a given user.

        Each user can have many tags applied to many questions, e.g.,
            user_rob
                tag1: question1, question2
                tag2: question1, question3
    '''
    name = models.CharField(max_length=1000)
    questions = models.ManyToManyField('Question', blank=True, through='QuestionTag', null=True)
    users = models.ManyToManyField(User, blank=True, through='UserTag', related_name='users', null=True)
    # questiontag_set
    # user
    # user_set

    def __unicode__(self):
        return self.name


class Quiz(CreatedBy):
    # Just a placeholder for now.
    name = models.CharField(max_length=1000)
    # user
    # user_set


class QuestionTag(CreatedBy):
    # This is a tag applied to a question.  
    # e.g., question = Question(text="1 + 1 = ??")
    #       tag_math = Tag(name="math")
    #       QuestionTag(question=question, tag=tag_math, enabled=True)
    question = models.ForeignKey(Question)
    tag = models.ForeignKey(Tag)
    enabled = models.BooleanField(default=False)
    # questions_set
    # user
    # user_set


class Schedule(CreatedBy):
    date_show_next = models.DateTimeField(null=True, default=None)  # when to show the question next
    interval_num = models.DecimalField(max_digits=5, decimal_places=2, null=True, default=None)
    interval_secs = models.IntegerField(null=True, default=None)  # Number of seconds from when record was added until it should be shown again.  When is this useful?  Not sure.  Maybe to aid in showing history of intervals.
    interval_unit = models.TextField(choices=CHOICES_UNITS, null=True, default=None)
    question = models.ForeignKey(Question)
    # user

    def save(self, *args, **kwargs):
        # Note that datetime_added and datetime_updated are not set until super() is called.
        # Rather than doing 2 db calls, get a new timezone.now instead, which will be slightly off
        # (maybe a fraction of a second) from datetime_added and datetime_updated.
        time_now = timezone.now()
        if self.interval_num != None:
            if self.interval_unit in ('months', 'years'):
                interval_num = int(self.interval_num)
            else:
                interval_num = float(self.interval_num)
        else:
            interval_num = 0
        interval = relativedelta(**({self.interval_unit: interval_num}))
        # TODO: set interval_secs
        try:
            self.date_show_next = time_now + interval
        except TypeError as exception:
            print "Exception: interval_unit=[%s] interval_num=[%s] type(interval_num)=[%s]" % (self.interval_unit, interval_num, type(interval_num))
            raise
        return super(Schedule, self).save(*args, **kwargs)


class UserTag(models.Model):
    # This allows the user to dynamically tell the app which questions they want to see.
    # Maybe it would be better to be called QuizTag.
    # For each user, they will have a UserTag for each tag, with an enable=True/False
    # Eventually, will have different quizzes where each quiz has its own set of UserTag's.
    user = models.ForeignKey(User)
    tag = models.ForeignKey(Tag)
    enabled = models.BooleanField(default=False)
