from django.test import TestCase
from questions.models import Question, Answer

class QuestionDeleteTests(TestCase):
    def test_delete_question_deletes_associated_answer(self):
        # Setup
        answer = Answer.objects.create(answer="Test answer")
        question = Question.objects.create(question="Test question", answer=answer)
        answer_id = answer.id

        # Action
        question.delete()

        # Assert
        self.assertEqual(Answer.objects.filter(id=answer_id).count(), 0)

    def test_delete_question_without_answer(self):
        # Setup
        question = Question.objects.create(question="Test question")
        question_id = question.id

        # Action
        question.delete()

        # Assert
        self.assertEqual(Question.objects.filter(id=question_id).count(), 0)