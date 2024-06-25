from django.test import TestCase

from emailusername.models import User

from questions import models, util
from questions.views import _get_next_question
from questions.views import NextQuestion

NUM_QUERIES_SCHEDULED_BEFORE_NOW = 3  # scheduled question is due to be shown before now
NUM_QUERIES_NO_QUESTIONS = 5  # number of queries expected when no questions are found


class TestGetNextQuestion(TestCase):

    def setUp(self):
        # Create a user
        self.PASSWORD = 'p'
        self.USERNAME = 'foo@bar.com'
        self.query_prefs_obj = models.QueryPreferences.objects.create()
        self.user = User(email=self.USERNAME)
        self.user.set_password(self.PASSWORD)
        self.user.save()

    def test_user_with_no_questions(self):
        next_question = _get_next_question(user=self.user, query_prefs_obj=self.query_prefs_obj, tags_selected=[])

        self.assertIsInstance(next_question, NextQuestion)
        self.assertIsNone(next_question.question)

    def test_user_with_one_unassociated_question(self):

        models.Question.objects.create(
            question='question #1',
        )

        # One untagged question that doesn't get returned because it has
        # no tags.

        next_question = _get_next_question(self.user, query_prefs_obj=self.query_prefs_obj, tags_selected=[])

        self.assertIsInstance(next_question, NextQuestion)
        self.assertIsNone(next_question.question)

        questions = models.Question.objects.filter(user=self.user)
        self.assertEqual(questions.count(), 0)

    def test_user_with_one_question(self):
        question = models.Question.objects.create(
            question='question #1',
            user=self.user
        )
        tag = util.assign_question_to_user(user=self.user, question=question, tag_name='tag #1')
        util.schedule_question_for_user(self.user, question)

        next_question = _get_next_question(self.user, query_prefs_obj=self.query_prefs_obj, tags_selected=models.Tag.objects.filter(pk=tag.pk))

        self.assertIsInstance(next_question, NextQuestion)
        self.assertIsNotNone(next_question.question)

        questions = models.Question.objects.filter(user=self.user)
        self.assertEqual(questions.count(), 1)

    def test_user_with_ten_questions(self):
        tag = models.Tag.objects.create(name='tag #1')
        for i in range(10):
            question = models.Question.objects.create(
                question=f'question {i}',
                user=self.user,
            )
            models.QuestionTag.objects.create(tag=tag, question=question, enabled=True)

        next_question = _get_next_question(self.user, query_prefs_obj=self.query_prefs_obj, tags_selected=models.Tag.objects.filter(pk=tag.pk))

        self.assertIsInstance(next_question, NextQuestion)
        self.assertIsNotNone(next_question.question)

        questions = models.Question.objects.filter(user=self.user)
        self.assertEqual(questions.count(), 10)