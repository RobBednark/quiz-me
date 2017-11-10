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
        self.user = User(email=self.USERNAME)
        self.user.set_password(self.PASSWORD)
        self.user.save()

    def test_user_with_no_questions(self):
        next_question = _get_next_question(self.user)

        self.assertIsInstance(next_question, NextQuestion)
        self.assertIsNone(next_question.question)

    def test_user_with_one_unassociated_question(self):

        models.Question.objects.create(
            question='fakebar',
        )

        # One untagged question that doesn't get returned because it has
        # no tags.

        with self.assertNumQueries(NUM_QUERIES_NO_QUESTIONS):
            next_question = _get_next_question(self.user)

        self.assertIsInstance(next_question, NextQuestion)
        self.assertIsNone(next_question.question)

        questions = models.Question.objects.get_user_questions(self.user)
        self.assertEqual(questions.count(), 0)

    def test_user_with_one_question(self):
        question = models.Question.objects.create(
            question='fakebar',
        )
        util.assign_question_to_user(self.user, question, 'fake_tag')
        util.schedule_question_for_user(self.user, question)

        with self.assertNumQueries(NUM_QUERIES_SCHEDULED_BEFORE_NOW):
            next_question = _get_next_question(self.user)

        self.assertIsInstance(next_question, NextQuestion)
        self.assertIsNotNone(next_question.question)

        questions = models.Question.objects.get_user_questions(self.user)
        self.assertEqual(questions.count(), 1)

    def test_user_with_ten_questions(self):
        for i in range(10):
            question = models.Question.objects.create(
                question='fakebar',
            )
            util.assign_question_to_user(self.user, question, 'fake_tag')
            util.schedule_question_for_user(self.user, question)

        with self.assertNumQueries(NUM_QUERIES_SCHEDULED_BEFORE_NOW):
            next_question = _get_next_question(self.user)

        self.assertIsInstance(next_question, NextQuestion)
        self.assertIsNotNone(next_question.question)

        questions = models.Question.objects.get_user_questions(self.user)
        self.assertEqual(questions.count(), 10)
