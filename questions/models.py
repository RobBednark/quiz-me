from django.db import models

# Create your models here.

class Question(models.Model):
    datetime_added = models.DateTimeField(auto_now_add=True)
    datetime_updated = models.DateTimeField(auto_now=True)
    question = models.TextField()

    def __unicode__(self):
        return '<Question question=[%s] datetime_added=[%s]>' % (self.question, self.datetime_added)

class Answer(models.Model):
    datetime_added = models.DateTimeField(auto_now_add=True)
    datetime_updated = models.DateTimeField(auto_now=True)
    answer = models.TextField()
    question = models.ForeignKey('Question', null=True)

class Attempt(models.Model):
    text = models.TextField()
    question = models.ForeignKey('Question', null=False)
    correct = models.BooleanField()

class Hint(models.Model):
    text = models.TextField()
    answer = models.ForeignKey('Answer', null=True)

class Tag(models.Model):
    name = models.CharField(max_length=1000)

class Quiz(models.Model):
    name = models.CharField(max_length=1000)
