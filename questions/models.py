from datetime import datetime

from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models

from emailusername.models import User

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
    # tag_set
    # user_set

    def __unicode__(self):
        return '<Question question=[%s] datetime_added=[%s]>' % (self.question, self.datetime_added)

class Answer(CreatedBy):
    answer = models.TextField()
    # hint_set
    # question_set
    # user_set

    def __unicode__(self):
        return '<Answer answer=[%s] datetime_added=[%s]>' % (self.answer, self.datetime_added)

class Attempt(CreatedBy):
    attempt = models.TextField()
    question = models.ForeignKey('Question', null=False)
    # user_set

class Hint(CreatedBy):
    answer = models.ForeignKey('Answer', null=True)
    hint = models.TextField()
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
    # user_set

    def __unicode__(self):
        return self.name

class Quiz(CreatedBy):
    # Just a placeholder for now.
    name = models.CharField(max_length=1000)
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
    # user_set

class UserTag(models.Model):
    # This allows the user to dynamically tell the app which questions they want to see.
    # Maybe it would be better to be called QuizTag.
    # For each user, they will have a UserTag for each tag, with an enable=True/False
    # Eventually, will have different quizzes where each quiz has its own set of UserTag's.
    user = models.ForeignKey(User)
    tag = models.ForeignKey(Tag)
    enabled = models.BooleanField(default=False)

#class Schedule(models.Model):
#    CHOICES_UNITS = ("seconds",
#                     "minutes",
#                     "hours",
#                     "days",
#                     "weeks",
#                     "months",
#                     "years")
#    date_added = models.DateTimeField(auto_now=True)
#    date_show = models.DateTimeField()  # when to show the question next
#    interval_num = models.DecimalField(max_digits=5, decimal_places=2)
#    interval_unit = models.TextField(choices=CHOICES_UNITS)
#    interval_secs = models.IntegerField()
#    question = models.ForeignKey(Question)
#    user = models.ForeignKey(User)
