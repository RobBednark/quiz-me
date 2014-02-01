from datetime import datetime

from django.db import models

from user_.models import User

class CreatedBy(models.Model):
    datetime_added = models.DateTimeField(auto_now_add=True, default=datetime.now())
    datetime_updated = models.DateTimeField(auto_now=True, default=datetime.now())
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

class Quiz(CreatedBy):
    name = models.CharField(max_length=1000)
