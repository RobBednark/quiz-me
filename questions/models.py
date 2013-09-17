from django.db import models

# Create your models here.

class Question(models.Model):
    datetime_added = models.DateTimeField(auto_now_add=True)
    datetime_updated = models.DateTimeField(auto_now=True)
    question = models.TextField()

class Answer(models.Model):
    datetime_added = models.DateTimeField(auto_now_add=True)
    datetime_updated = models.DateTimeField(auto_now=True)
    question = models.TextField()

class Attempt(models.Model):
    text = models.TextField()
    answer = models.ForeignKey('Answer', null=True)

class Hint(models.Model):
    text - models.TextField()

class Tag(models.Model):
    name = models.CharField(max_len=1000)

class Quiz(models.Model):
    name = models.CharField(max_len=1000)
