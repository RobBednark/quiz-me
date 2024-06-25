from datetime import datetime, timedelta
import os

from django.test import LiveServerTestCase, TestCase
from selenium.common.exceptions import StaleElementReferenceException
import pytz

from emailusername.models import User
from questions import forms
from questions.models import Answer, Attempt, QueryPreferences, Question, QuestionTag, Schedule, Tag
from questions.views import _get_next_question

# By default, LiveServerTestCase uses port 8081.
# If you need a different port, then set this.
# os.environ['DJANGO_LIVE_TEST_SERVER_ADDRESS'] = 'localhost:8000'

WAIT_TIME = 5


# phantomjs archives for Windows, OSX, and Linux can be found at: http://phantomjs.org/download.html
class BrowserTests(LiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        from splinter import Browser
        # Note that 'firefox' needs to be in your path.
        # On Mac, can do this by:
        #   $ cat << THE_END > /usr/local/bin/firefox
        #   #!/bin/bash
        #   open /Applications/Firefox.app
        #   THE_END
        #   $ chmod a+x /usr/local/bin/firefox
        # cls.browser = Browser('firefox')

        # Note that in order to use phantomjs, need to "brew install phantomjs"
        browser = os.environ.get('SELENIUM_BROWSER', 'phantomjs')
        cls.browser = Browser(browser)

        super(BrowserTests, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()
        super(BrowserTests, cls).tearDownClass()

    def setUp(self):
        # Create users
        self.PASSWORD = 'p'
        self.EMAIL_USER1 = 'rbednark+user1@gmail.com'
        self.EMAIL_USER2 = 'rbednark+user2@gmail.com'
        user1 = User(email=self.EMAIL_USER1)
        user2 = User(email=self.EMAIL_USER2)
        user1.set_password(self.PASSWORD)
        user2.set_password(self.PASSWORD)
        user1.save()
        user2.save()
        self.user1 = user1
        self.user2 = user2

    def _loop_is_text_present(self, text, max_attempts=3):
        attempt = 1
        while attempt < max_attempts:
            try:
                ret = self.browser.is_text_present(text, wait_time=WAIT_TIME)
                return ret
            except StaleElementReferenceException:
                attempt += 1
                if attempt == max_attempts:
                    raise

    def _assert_no_questions(self):
        self.assertTrue(self._loop_is_text_present(
            text='(NOTE: there are no questions)'))

    def _login(self, user=None, password=None):
        if user is None:
            user = self.EMAIL_USER1
        if password is None:
            password = self.PASSWORD
        self.browser.visit(self.live_server_url)
        self.assertEquals(self.browser.title, 'Quiz Me!')
        self.browser.find_by_id('id_username')[0].fill(user)
        self.browser.find_by_id('id_password')[0].fill(password)
        self.browser.find_by_value('login').click()

    def test_login_successful_no_questions(self):
        ''' A user can login successfully with correct username and password,
        and the quiz has no questions. '''
        self._login()

        self.assertEquals(self.browser.title, 'Quiz Me!')
        self._assert_no_questions()

    def test_login_fails_incorrect_password(self):
        ''' A user cannot login with an incorrect password. '''
        self._login(password='')

        self.assertTrue(
            self._loop_is_text_present(
                "Your username and password didn't match. "
                "Please try again."
            )
        )

    def test_login_fails_incorrect_username(self):
        ''' A user cannot login with an incorrect username. '''
        self._login(user="bad username")

        self.assertTrue(
            self._loop_is_text_present(
                "Your username and password didn't match. Please try again.")
        )

    def test_only_show_questions_with_tag_selected(self):
        ''' Assert that only questions with a given tag are shown '''
        tag1 = Tag(name='tag1')
        tag2 = Tag(name='tag2')
        tag1.save()
        tag2.save()

        question1 = Question(question="question1")
        question2 = Question(question="question2")
        question1.save()
        question2.save()

        self.assertEquals(Question.objects.all().count(), 2)
        self.assertEquals(QuestionTag.objects.all().count(), 0)

        self._login()
        # Assert no questions, because user doesn't have any tags selected.
        self._assert_no_questions()

        # Now select a tag

        # TODO/LEFTOFF/NEXT:
        # Figure out how to select a tag.

        # Assert that a question is shown

    def test_confirm_tags_can_be_selected_unselected(self):
        ''' B: tags enabled/disabled during questions and answers are saved
        and carried over'''
        tag1 = Tag(name='tag1')
        tag2 = Tag(name='tag2')
        tag1.save()
        tag2.save()

        question1 = Question(question="question1")
        question2 = Question(question="question2")
        question1.save()
        question2.save()

        self._login()
        # This is currently failing. I need to stop and thing what the
        # expected behavior should be.
        # self._assert_no_questions()


class NonBrowserTests(TestCase):

    def test_schedule_save(self):
        my_datetime = pytz.utc.localize(datetime(year=2017, month=7, day=4))
        question = Question.objects.create()
        schedule1 = Schedule.objects.create(question=question)
        schedule2 = Schedule.objects.create(date_show_next=my_datetime, question=question)

        now = datetime.now(tz=pytz.utc)
        self.assertTrue((now - timedelta(seconds=5)) < schedule1.date_show_next < now)
        self.assertEquals(schedule2.date_show_next, my_datetime)

    def test_get_next_question(self):
        # expected number of queries
        NUM_QUERIES_SCHEDULED_BEFORE_NOW = 3  # scheduled question is due to be shown before now
        NUM_QUERIES_UNSCHEDULED_QUESTION = 3  # there are no scheduled questions, and an unscheduled question is returned
        NUM_QUERIES_SCHEDULED_AFTER_NOW = 5   # no scheduled questions before now, no unscheduled questions, and a scheduled question after now is shown
        NUM_QUERIES_NO_QUESTIONS = 5  # number of queries expected when no questions are found

        # test _get_next_question()
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
        next_question = _get_next_question(user=user1, query_prefs_obj=query_prefs_obj, tags_selected=[])
        self.assertTrue(next_question.question is None)

        # Test: no question when tags_selected but no questions with that tag
        # Given:
        #   a) tags_selected
        #   b) 0 questions with that tag
        # Assert: user1 does not get a question, because there are no questions with that tag
        self.assertTrue(QuestionTag.objects.filter(tag=tag1).count() == 0)

        tag1_queryset = QuestionTag.objects.filter(tag=tag1)
        for _ in range(5):
            next_question = _get_next_question(user=user1, query_prefs_obj=query_prefs_obj, tags_selected=tag1_queryset)
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
            question=question1, tag=tag1, enabled=True
        )
        question2_tag1 = QuestionTag.objects.create(
            question=question2, tag=tag1, enabled=True
        )
        self.assertTrue(question1.datetime_added < question2.datetime_added)
        self.assertTrue(Question.objects.all().count() == 2)
        self.assertTrue(QuestionTag.objects.all().count() == 2)
        self.assertTrue(
            QuestionTag.objects.filter(tag=tag1, enabled=True).count() == 2
        )
        self.assertTrue(Schedule.objects.filter(user=user1).count() == 0)

        for n in range(4):
            next_question = _get_next_question(user=user1, query_prefs_obj=query_prefs_obj, tags_selected=tag1_queryset)
            self.assertTrue(next_question.question == question1)

        # Test: No question returned when tag.enabled == False
        # Given:
        #    a) user1 with tag1
        #    b) question1 and question2 with tag1
        #    c) tag1.enabled == False
        #    d) user has 0 schedules
        # Assert: no question is returned because tag1.enabled == False
        question1_tag1.enabled = False
        question2_tag1.enabled = False
        question1_tag1.save()
        question2_tag1.save()
        tag1_tag2_queryset = QuestionTag.objects.filter(id__in=[question1_tag1.pk, question2_tag1.pk])
        self.assertEqual(
            QuestionTag.objects.filter(tag=tag1, enabled=True).count(), 0
        )
        self.assertEqual(
            QuestionTag.objects.filter(tag=tag1, enabled=False).count(), 2
        )
        for _ in range(4):
            next_question = _get_next_question(user=user1, query_prefs_obj=query_prefs_obj, tags_selected=tag1_queryset)
            self.assertTrue(next_question.question is None)

        # Bucket 2: question with no schedules
        # Test: question with no schedules returned (when another question with schedule.date_show_next > now)
        # Given:
        #       a) question1 and question2 both have tag1
        #       b) question1 has 1 schedule with date_show_now > now
        #       c) question2 has 0 schedules
        # Assert: question2 is returned because question1 is not ready to be shown yet,
        #         and question2 has no schedules
        question1_tag1.enabled = True
        question1_tag1.save()
        question2_tag1.enabled = True
        question2_tag1.save()
        q1_sched1 = Schedule.objects.create(
            user=user1,
            question=question1,
            interval_num=1,
            interval_unit='weeks')
        self.assertTrue(q1_sched1.date_show_next > datetime.now(tz=pytz.utc))
        self.assertTrue(QuestionTag.objects.filter(tag=tag1, enabled=True).count() == 2)
        self.assertTrue(Schedule.objects.all().count() == 1)
        self.assertTrue(Schedule.objects.filter(question=question1).count() == 1)
        self.assertTrue(Schedule.objects.filter(question=question2).count() == 0)
        self.assertTrue(Question.objects.get(id=question1.id).schedule_set.count() == 1)
        for _ in range(5):
            next_question = _get_next_question(user=user1, query_prefs_obj=query_prefs_obj, tags_selected=tag1_queryset)
            self.assertTrue(next_question.question == question2)

        # Bucket 1: question.schedule.date_show_next < now
        # Given 2 questions with date_show_next < now, show the question with the latest date_show_next
        # Given:
        #       a) question1 and question2 both have tag1
        #       b) question1 has 2 schedules, question2 has 1 schedule
        #       c) question1's newest schedule (q1_sched2) has date_show_next > question2's schedule.date_show_next
        #       d) question1's newest schedule (q1_sched2) has date_show_next < now
        #       e) question1's oldest schedule (q1_sched1) has date_show_next < now
        #       f) question2's schedule (q2_sched1) has date_show_next < now
        #       g) question1's newest schedule (q1_sched2).date_show_next > q2_sched1.date_show_next
        # Assert: question1 is returned because it has a later schedule.date_show_next
        q2_sched1 = Schedule.objects.create(
            user=user1,
            question=question2,
            interval_num=1,
            interval_unit='months',
            date_show_next=datetime.now(tz=pytz.utc) - timedelta(days=2))
        q1_sched2 = Schedule.objects.create(
            user=user1,
            question=question1,
            interval_num=1,
            interval_unit='days',
            date_show_next=datetime.now(tz=pytz.utc) - timedelta(days=1))
        q1_sched1.date_show_next = datetime.now(tz=pytz.utc) - timedelta(days=1)
        q1_sched1.save()
        q2_sched1.save()
        self.assertTrue(q1_sched2.datetime_added > q1_sched1.datetime_added)
        self.assertTrue(q1_sched2.date_show_next > q2_sched1.date_show_next)
        self.assertTrue(q1_sched1.date_show_next < datetime.now(tz=pytz.utc))
        self.assertTrue(q1_sched2.date_show_next < datetime.now(tz=pytz.utc))
        self.assertTrue(q2_sched1.date_show_next < datetime.now(tz=pytz.utc))
        self.assertTrue(Schedule.objects.all().count() == 3)
        for _ in range(5):
            next_question = _get_next_question(user=user1, query_prefs_obj=query_prefs_obj, tags_selected=tag1_queryset)
            self.assertEqual(next_question.question, question1)

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
        q2_sched2 = Schedule.objects.create(
            user=user1,
            question=question2,
            interval_num=5,
            interval_unit='minutes',
            date_show_next=datetime.now(tz=pytz.utc) + timedelta(minutes=1)
        )
        q1_sched2.date_show_next = datetime.now(tz=pytz.utc) + timedelta(minutes=2)
        q1_sched2.save()
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
            next_question = _get_next_question(user=user1, query_prefs_obj=query_prefs_obj)
            self.assertEqual(next_question.question, question2)

        # Add a new question with a different tag, and assert that it
        # doesn't affect the question returned
        Question.objects.create(question="question3")
        for _ in range(5):
            next_question = _get_next_question(user=user1, query_prefs_obj=query_prefs_obj)
            self.assertEqual(next_question.question, question2)


class ViewAnswerTests(TestCase):

    def setUp(self):
        # Create a user
        self.PASSWORD = 'p'
        self.USERNAME = 'foo@bar.com'
        self.user = User(email=self.USERNAME)
        self.user.set_password(self.PASSWORD)
        self.user.save()

        # Create 1 answer, 1 question, and 1 attempt
        self.answer = Answer.objects.create(answer='fakefoo')
        self.question = Question.objects.create(
            question='fakebar',
            answer=self.answer
        )
        self.attempt = Attempt.objects.create(
            attempt='fakebaz',
            question=self.question
        )

    def test_viewanswer_get(self):
        # Log in
        logged_in = self.client.login(
            username=self.user.get_username(),
            password=self.PASSWORD
        )
        # GET the answer page
        response = self.client.get('/answer/{}/'.format(self.attempt.pk))

        # Verify that we're logged-in, and that we GET 200'ed
        self.assertTrue(logged_in)
        self.assertEqual(response.status_code, 200)

    def test_viewanswer_post(self):
        tag = Tag.objects.create(name='faketag')
        # Log in
        logged_in = self.client.login(
            username=self.user.get_username(),
            password=self.PASSWORD
        )

        # Make sure there's no preexisting schedule
        self.assertFalse(
            Schedule.objects.filter(question=self.question).exists()
        )

        # POST to the answer page
        data = {
            'percent_correct': 13.45,
            'percent_importance': 23.45,
            'interval_num': 33.45,
            'interval_unit': 'hours',
        }

        response = self.client.post(
            '/answer/{}/'.format(self.attempt.pk), data
        )

        # Verify that we're logged-in, and that we GET 302'ed
        self.assertTrue(logged_in)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            Schedule.objects.filter(
                question=self.question
            ).count(),
            1
        )
