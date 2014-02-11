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
    name = models.CharField(max_length=1000)
    questions = models.ManyToManyField('Question', related_name='tags')
    users = models.ManyToManyField('User', related_name='user_tags')

    def __unicode__(self):
        return self.name

class Quiz(CreatedBy):
    name = models.CharField(max_length=1000)
