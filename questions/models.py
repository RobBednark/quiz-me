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
    # attempt_set = ForeignKey(Attempt)
    # questiontag_set = ManyToMany(QuestionTag)
    # tag_set = ManyToMany(Tag) 
    # user_set = ForeignKey(User)

    def __unicode__(self):
        return '<Question question=[%s] datetime_added=[%s]>' % (self.question, self.datetime_added)

class Answer(CreatedBy):
    answer = models.TextField()
    # question_set = ForeignKey(Question)
    # hint_set = ForeignKey(Hint)
    # user_set = ForeignKey(User)

    def __unicode__(self):
        return '<Answer answer=[%s] datetime_added=[%s]>' % (self.answer, self.datetime_added)

class Attempt(CreatedBy):
    attempt = models.TextField()
    correct = models.BooleanField()
    question = models.ForeignKey('Question', null=False)
    # user_set

class Hint(CreatedBy):
    answer = models.ForeignKey('Answer', null=True)
    hint = models.TextField()
    # user_set = ForeignKey(User)

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
    # questiontag_set = ForeignKey(QuestionTag)
    # user_set = ForeignKey(User)

    def __unicode__(self):
        return self.name

class Quiz(CreatedBy):
    # Just a placeholder for now.
    name = models.CharField(max_length=1000)
    # user_set

class QuestionTag(CreatedBy):
    # This is a tag applied to a question.  
    # e.g., ques = Question(text="1 + 1 = ??")
    #       tag_math = Tag(name="math")
    #       QuestionTag(question=ques, tag=tag_math, enabled=True)
    question = models.ForeignKey(Question)
    tag = models.ForeignKey(Tag)
    enabled = models.BooleanField(default=False)
    # questions_set
    # user_set

class UserTag(models.Model):
    # This allows the user to dynamically tell the app which questions they want to see.
    # For each user, they will have a UserTag for each tag, with an enable=True/False
    # Eventually, will have different quizzes where each have their own set of UserTag's.
    user = models.ForeignKey(User)
    tag = models.ForeignKey(Tag)
    enabled = models.BooleanField(default=False)
