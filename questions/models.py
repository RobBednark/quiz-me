from django.db import models

# Create your models here.

class Question(models.Model):
    datetime_added = models.DateTimeField(auto_now_add=True)
    datetime_updated = models.DateTimeField(auto_now=True)
    question = models.TextField()
    answer = models.ForeignKey('Answer', null=True)

    def __unicode__(self):
        return '<Question question=[%s] datetime_added=[%s]>' % (self.question, self.datetime_added)

class Answer(models.Model):
    answer = models.TextField()
    datetime_added = models.DateTimeField(auto_now_add=True)
    datetime_updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return '<Answer answer=[%s] datetime_added=[%s]>' % (self.answer, self.datetime_added)

class User(models.Model):
    name = models.TextField()

class Attempt(models.Model):
    attempt = models.TextField()
    correct = models.BooleanField()
    datetime_added = models.DateTimeField(auto_now_add=True)
    question = models.ForeignKey('Question', null=False)
    user = models.ForeignKey('User', null=True)

class Hint(models.Model):
    answer = models.ForeignKey('Answer', null=True)
    hint = models.TextField()

class Tag(models.Model):
    name = models.CharField(max_length=1000)

class Quiz(models.Model):
    name = models.CharField(max_length=1000)
