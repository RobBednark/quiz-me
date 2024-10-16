from datetime import datetime, timedelta
import math
import random

from django.test import TestCase
import pytz

from emailusername.models import User
from questions.models import Answer, Attempt,  Question, QuestionTag, Schedule, Tag
from questions.get_next_question import get_next_question

class Tests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super(TestCase, cls).tearDownClass()
        Question.objects.all().delete()
        Schedule.objects.all().delete()

    def test_schedule_save(self):
        my_datetime = pytz.utc.localize(datetime(year=2017, month=7, day=4))
        question = Question.objects.create()
        schedule1 = Schedule.objects.create(question=question)
        schedule2 = Schedule.objects.create(date_show_next=my_datetime, question=question)

        now = datetime.now(tz=pytz.utc)
        self.assertTrue((now - timedelta(seconds=5)) < schedule1.date_show_next < now)
        self.assertEqual(schedule2.date_show_next, my_datetime)

    def test_get_next_question(self):
        # expected number of queries

        # test get_next_question()
        user1 = User.objects.create(email="user1@bednark.com")
        user2 = User.objects.create(email="user2@bednark.com")

        tag1 = Tag.objects.create(name='tag1')
        tag2 = Tag.objects.create(name='tag2')

        query_prefs_obj = QueryPreferences.objects.create()
        question1 = Question.objects.create(question="question1")
        question2 = Question.objects.create(question="question2")

        # Given:
        #   a) no tags_selected
        #   b) 0 questions with any tags
        #   c) 2 questions with 0 tags
        #   d) tag1 and tag2 each have 0 questions
        # Assert: user does not get a question, because there are no tags_selected
        self.assertTrue(Question.objects.all().count() == 2)
        self.assertTrue(QuestionTag.objects.all().count() == 0)
        self.assertTrue(Schedule.objects.all().count() == 0)
        self.assertTrue(Tag.objects.all().count() == 2)
        next_question = get_next_question(user=user1, query_prefs_obj=query_prefs_obj, tags_selected=[])
        self.assertTrue(next_question.question is None)

        # Test: no question when tags_selected but no questions with that tag
        # Given:
        #   a) tags_selected
        #   b) 0 questions with that tag
        # Assert: user1 does not get a question, because there are no questions with that tag
        self.assertTrue(QuestionTag.objects.filter(tag=tag1).count() == 0)

        tag1_queryset = QuestionTag.objects.filter(tag=tag1)
        for _ in range(5):
            next_question = get_next_question(user=user1, query_prefs_obj=query_prefs_obj, tags_selected=tag1_queryset)
            self.assertTrue(next_question.question is None)

        # Bucket 2: question with no schedules
        # Test: No questions with schedules, so returned oldest question.datetime_added
        # Given:
        #    a) user1 with tag user1_tag1
        #    b) question1 and question2 have tag1
        #    c) user has 0 schedules
        #    d) question1.datetime_added < question2.datetime_added
        # Assert: user1 gets question1 because it was added before question2
        question1_tag1 = QuestionTag.objects.create(
            question=question1, tag=tag1
        )
        question2_tag1 = QuestionTag.objects.create(
            question=question2, tag=tag1
        )
        self.assertTrue(question1.datetime_added < question2.datetime_added)
        self.assertTrue(Question.objects.all().count() == 2)
        self.assertTrue(QuestionTag.objects.all().count() == 2)
        self.assertTrue(
            QuestionTag.objects.filter(tag=tag1).count() == 2
        )
        self.assertTrue(Schedule.objects.filter(user=user1).count() == 0)

        for n in range(4):
            next_question = get_next_question(user=user1, query_prefs_obj=query_prefs_obj, tags_selected=tag1_queryset)
            self.assertTrue(next_question.question == question1)

        # Bucket 2: question with no schedules
        # Test: question with no schedules returned (when another question with schedule.date_show_next > now)
        # Given:
        #       a) question1 and question2 both have tag1
        #       b) question1 has 1 schedule with date_show_now > now
        #       c) question2 has 0 schedules
        # Assert: question2 is returned because question1 is not ready to be shown yet,
        #         and question2 has no schedules
        q1_sched1 = Schedule.objects.create(
            user=user1,
            question=question1,
            interval_num=1,
            interval_unit='weeks')
        self.assertTrue(q1_sched1.date_show_next > datetime.now(tz=pytz.utc))
        self.assertTrue(QuestionTag.objects.filter(tag=tag1).count() == 2)
        self.assertTrue(Schedule.objects.all().count() == 1)
        self.assertTrue(Schedule.objects.filter(question=question1).count() == 1)
        self.assertTrue(Schedule.objects.filter(question=question2).count() == 0)
        self.assertTrue(Question.objects.get(id=question1.id).schedule_set.count() == 1)
        for _ in range(5):
            next_question = get_next_question(user=user1, query_prefs_obj=query_prefs_obj, tags_selected=tag1_queryset)
            self.assertTrue(next_question.question == question2)

        # Bucket 3: question.schedule_date_show_next > now
        # Add a 2nd schedule to question2 such that:
        #    now < question2's schedule.date_show_next < question1's schedule.date_show_next
        # and assert that question2 is now returned
        # Given:
        #   a) question1 and question2 both have tag1
        #   b) question1 and question2 each have 2 schedules
        #   c) q2's newest schedule is q2_sched2, q1's newest is q1_sched2
        #   d) q2_sched2.date_show_next > now < q1_sched2.date_show_next
        # Assert that question2 is returned because it's schedule was added later.
        q1_sched2 = Schedule.objects.create(
            user=user1,
            question=question1,
            interval_num=5,
            interval_unit='minutes',
        )
        q2_sched1 = Schedule.objects.create(
            user=user1,
            question=question2,
            interval_num=5,
            interval_unit='minutes',
        )
        q2_sched2 = Schedule.objects.create(
            user=user1,
            question=question2,
            interval_num=5,
            interval_unit='minutes',
        )
        q1_sched2.date_show_next = datetime.now(tz=pytz.utc) + timedelta(minutes=99)
        q1_sched2.save()
        q2_sched2.date_show_next = date_show_next=datetime.now(tz=pytz.utc) + timedelta(minutes=1)
        q2_sched2.save()
        self.assertTrue(q2_sched2.date_show_next > datetime.now(tz=pytz.utc))
        self.assertTrue(q1_sched2.date_show_next > datetime.now(tz=pytz.utc))
        self.assertTrue(q2_sched2.date_show_next < q1_sched2.date_show_next)
        self.assertTrue(q2_sched2.datetime_added > q2_sched1.datetime_added)
        self.assertTrue(q1_sched2.datetime_added > q1_sched1.datetime_added)
        question1.refresh_from_db()
        question2.refresh_from_db()
        self.assertTrue(question1.schedule_set.count() == 2)
        self.assertTrue(question1.schedule_set.count() == 2)
        for _ in range(5):
            if True:
                # trigger the debugger
                pytz.show = False
            next_question = get_next_question(user=user1, query_prefs_obj=query_prefs_obj, tags_selected=tag1_queryset)
            self.assertEqual(next_question.question, question2)

        # Add a new question with a different tag, and assert that it
        # doesn't affect the question returned
        Question.objects.create(question="question3")
        for _ in range(5):
            next_question = get_next_question(user=user1, query_prefs_obj=query_prefs_obj,
                    tags_selected=tag1_queryset)
            self.assertEqual(next_question.question, question2)

    def test_schedule_date_show_next_less_than_now(self):
        # Bucket 1: questions scheduled before now
        # First look for questions with schedule.date_show_next <= now,
        # and return the question with the newest schedule.datetime_added

        # Given 2 questions with date_show_next < now, show the question with the newest-added schedule
        # Given:
        #       *) QueryPrefs.sort_by_newest_answered_first = True
        #       *) QueryPrefs.limit_to_date_show_next_before_now = True
        #       a) question1 and question2 both have tag1
        #       b) question1 has 2 schedules, question2 has 1 schedule
        #       c) question1's newest schedule (q1_sched2) has date_show_next < question2's schedule.date_show_next
        #       d) question1's newest schedule (q1_sched2) has date_show_next < now
        #       e) question1's oldest schedule (q1_sched1) has date_show_next < now
        #       f) question2's schedule (q2_sched1) has date_show_next < now
        #       g) question1's newest schedule (q1_sched2).date_show_next) > q2_sched1.date_show_next
        # Assert: question1 is returned because it has a later schedule.date_show_next
        user1 = User.objects.create(email="user1@bednark.com")
        user2 = User.objects.create(email="user2@bednark.com")

        tag1 = Tag.objects.create(name='tag1')
        tag2 = Tag.objects.create(name='tag2')

        query_prefs_obj = QueryPreferences.objects.create(
            user=user1,
            sort_by_newest_answered_first=True,
            limit_to_date_show_next_before_now=True,
            )
        question1 = Question.objects.create(question="question1")
        question2 = Question.objects.create(question="question2")
        question1_tag1 = QuestionTag.objects.create(
            question=question1, tag=tag1
        )
        question2_tag1 = QuestionTag.objects.create(
            question=question2, tag=tag1
        )
        tag1_queryset = QuestionTag.objects.filter(tag=tag1)
 
        q2_sched1 = Schedule.objects.create(
            user=user1,
            question=question2,
            interval_num=1,
            interval_unit='months',
            date_show_next=datetime.now(tz=pytz.utc) - timedelta(days=55))
        q1_sched1 = Schedule.objects.create(
            user=user1,
            question=question1,
            interval_num=1,
            interval_unit='weeks')
        q1_sched2 = Schedule.objects.create(
            user=user1,
            question=question1,
            interval_num=1,
            interval_unit='days')
        #       c) question1's newest schedule (q1_sched2) has date_show_next > question2's schedule.date_show_next
        #       d) question1's newest schedule (q1_sched2) has date_show_next < now
        #       e) question1's oldest schedule (q1_sched1) has date_show_next < now
        q1_sched1.date_show_next = datetime.now(tz=pytz.utc) - timedelta(days=99)
        q1_sched1.save()
        q1_sched2.date_show_next = datetime.now(tz=pytz.utc) - timedelta(days=1)
        q1_sched2.save()
        #       f) question2's schedule (q2_sched1) has date_show_next < now
        #       g) question1's newest schedule (q1_sched2).date_show_next > q2_sched1.date_show_next
        q2_sched1.date_show_next = datetime.now(tz=pytz.utc) - timedelta(days=2)
        q2_sched1.save()

        self.assertTrue(q1_sched2.datetime_added > q1_sched1.datetime_added)
        self.assertTrue(q1_sched2.date_show_next > q2_sched1.date_show_next)
        self.assertTrue(q1_sched1.date_show_next < datetime.now(tz=pytz.utc))
        self.assertTrue(q1_sched2.date_show_next < datetime.now(tz=pytz.utc))
        self.assertTrue(q2_sched1.date_show_next < datetime.now(tz=pytz.utc))
        self.assertTrue(Schedule.objects.all().count() == 3)
        for _ in range(5):
            next_question = get_next_question(user=user1, query_prefs_obj=query_prefs_obj, tags_selected=tag1_queryset)
            self.assertEqual(next_question.question, question1)

