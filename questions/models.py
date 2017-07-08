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
    user = models.ForeignKey(User, null=True)

    class Meta:
        abstract = True


class QuestionManager(models.Manager):

    def get_user_questions(self, user):

        questions = self.filter(
            tag__usertag__user=user,
            tag__usertag__enabled=True
        )

        return questions


class Question(CreatedBy):
    question = models.TextField()
    answer = models.ForeignKey('Answer', null=True, blank=True)
    # attempt_set
    # questiontag_set
    # schedule_set
    # tag_set
    # user
    # user_set
    objects = QuestionManager()

    def __unicode__(self):
        return '<Question id=[%s] question=[%s] datetime_added=[%s]>' % (self.id, self.question, self.datetime_added)


class Answer(CreatedBy):
    answer = models.TextField()
    # hint_set
    # question_set
    # user
    # user_set

    def __unicode__(self):
        return '<Answer id=[%s] answer=[%s] datetime_added=[%s]>' % (self.id, self.answer, self.datetime_added)


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
    questions = models.ManyToManyField('Question', blank=True, through='QuestionTag')
    users = models.ManyToManyField(User, blank=True, through='UserTag', related_name='users')
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

    def __unicode__(self):
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
    question = models.ForeignKey(Question)
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
        if not self.date_show_next:
            try:
                self.date_show_next = time_now + interval
            except TypeError as exception:
                print("Exception: interval_unit=[%s] interval_num=[%s] type(interval_num)=[%s] "
                      "exception=[%s]" % (
                          self.interval_unit, interval_num, type(interval_num), exception))
                raise
        return super(Schedule, self).save(*args, **kwargs)


class UserTagManager(models.Manager):

    def tags_available_for_user(self, user):
        return self.filter(user=user).exists()


class UserTag(models.Model):
    # This allows the user to dynamically tell the app which questions
    # they want to see.
    # Maybe it would be better to be called QuizTag.
    # For each user, they will have a UserTag for each tag,
    # with an enable=True/False
    # Eventually, will have different quizzes where each quiz has its
    # own set of UserTag's.
    user = models.ForeignKey(User)
    tag = models.ForeignKey(Tag)
    enabled = models.BooleanField(default=False)

    objects = UserTagManager()
