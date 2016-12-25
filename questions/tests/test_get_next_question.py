from django.test import TestCase

from django.db import connection
from django.test.utils import override_settings
from emailusername.models import User

from questions import models
from questions.views import _get_next_question
from questions.views import NextQuestion


class TestGetNextQuestion(TestCase):

    def setUp(self):
        # Create a user
        self.PASSWORD = 'p'
        self.USERNAME = 'foo@bar.com'
        self.user = User(email=self.USERNAME)
        self.user.set_password(self.PASSWORD)
        self.user.save()

    def _assign_question_to_user(self, user, question):
        tag = models.Tag.objects.create(name='faketag')

        models.UserTag.objects.create(
            tag=tag,
            user=user,
            enabled=True
        )
        models.QuestionTag.objects.create(
            tag=tag,
            question=question,
            enabled=True
        )

        return tag

    def test_user_with_no_questions(self):
        next_question = _get_next_question(self.user)

        self.assertIsInstance(next_question, NextQuestion)
        self.assertIsNone(next_question.question)

    @override_settings(DEBUG=True)
    def test_user_with_one_question(self):
        question = models.Question.objects.create(
            question='fakebar',
        )
        self._assign_question_to_user(self.user, question)

        next_question = _get_next_question(self.user)

        self.assertIsInstance(next_question, NextQuestion)
        self.assertIsNotNone(next_question.question)
        self.assertEqual(len(connection.queries), 8)

    @override_settings(DEBUG=True)
    def test_user_with_ten_questions(self):
        for i in range(10):
            question = models.Question.objects.create(
                question='fakebar',
            )
            self._assign_question_to_user(self.user, question)

        next_question = _get_next_question(self.user)

        self.assertIsInstance(next_question, NextQuestion)
        self.assertIsNotNone(next_question.question)
        self.assertEqual(len(connection.queries), 53)
        import pdb; pdb.set_trace()
