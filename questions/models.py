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
    answer = models.ForeignKey('Answer', null=True)

    def __unicode__(self):
        return '<Question question=[%s] datetime_added=[%s]>' % (self.question, self.datetime_added)

class Answer(CreatedBy):
    answer = models.TextField()

    def __unicode__(self):
        return '<Answer answer=[%s] datetime_added=[%s]>' % (self.answer, self.datetime_added)

class Attempt(CreatedBy):
    attempt = models.TextField()
    correct = models.BooleanField()
    question = models.ForeignKey('Question', null=False)

class Hint(CreatedBy):
    answer = models.ForeignKey('Answer', null=True)
    hint = models.TextField()

class Tag(CreatedBy):
    '''
        Each user can have many tags applied to many questions, e.g.,
            user_rob
                tag1: question1, question2
                tag2: question1, question3
    '''
    name = models.CharField(max_length=1000)
    questions = models.ManyToManyField('Question', blank=True, through='UserTag')
    users = models.ManyToManyField(User, blank=True, through='UserTag')

    def __unicode__(self):
        return self.name

class Quiz(CreatedBy):
    name = models.CharField(max_length=1000)

class UserTag(models.Model):
    user = models.ForeignKey(User)
    tag = models.ForeignKey(Tag)
    enabled = models.BooleanField(default=False)

