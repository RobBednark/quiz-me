"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
import os

from django.test import LiveServerTestCase, TestCase

from emailusername.models import User
from .models import Attempt, Question, QuestionTag, Schedule, Tag, UserTag
from .views import _next_question, _next_question_new

# By default, LiveServerTestCase uses port 8081.
# If you need a different port, then set this.
# os.environ['DJANGO_LIVE_TEST_SERVER_ADDRESS'] = 'localhost:8000'


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
        #cls.browser = Browser('firefox')

        # Note that in order to use phantomjs, need to "brew install phantomjs"
        browser = os.environ.get('ROB_SELENIUM_BROWSER', 'phantomjs')
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

    def _assert_no_questions(self):
        self.assertTrue(self.browser.is_text_present('(NOTE: there are no questions)'))

    def _login(self, user=None, password=None):
        if user == None:
            user = self.EMAIL_USER1
        if password == None:
            password = self.PASSWORD
        self.browser.visit(self.live_server_url)
        self.assertEquals(self.browser.title, 'Quiz Me!')
        self.browser.find_by_id('id_username')[0].fill(user)
        self.browser.find_by_id('id_password')[0].fill(password)
        self.browser.find_by_value('login').click()

    def test_login_successful_no_questions(self):
        ''' A user can login successfully with correct username and password, and the quiz has no questions. '''
        self._login()
        self.assertEquals(self.browser.title, 'Quiz Me!')
        self._assert_no_questions()

    def test_login_fails_incorrect_password(self):
        ''' A user cannot login with an incorrect password. '''
        self._login(password='')
        self.assertTrue(self.browser.is_text_present("Your username and password didn't match. Please try again."))

    def test_login_fails_incorrect_username(self):
        ''' A user cannot login with an incorrect username. '''
        self._login(user="bad username")
        self.assertTrue(self.browser.is_text_present("Your username and password didn't match. Please try again."))

    def test_tags_created_automatically_for_user(self):
        ''' Assert that a UserTag is created for a user when they hit an endpoint after a Tag has been created. '''
        tag1 = Tag(name='tag1')
        tag2 = Tag(name='tag2')
        tag1.save()
        tag2.save()
        self.assertEquals(UserTag.objects.count(), 0)

        self._login()
        self._assert_no_questions()

        # Assert that QuestionTags were created for this user
        user_tags = UserTag.objects.all()
        self.assertEquals(len(user_tags), 2)
        tag_ids = { user_tag.tag.id for user_tag in user_tags }
        user_ids = { user_tag.user.id for user_tag in user_tags }
        enabled_set = { user_tag.enabled for user_tag in user_tags }
        self.assertEquals(tag_ids, {tag1.id, tag2.id})
        self.assertEquals(user_ids, {self.user1.id})
        self.assertEquals(enabled_set, {False})

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
        self.assertEquals(UserTag.objects.all().count(), 0)

        self._login()
        # Assert no questions, because user doesn't have any tags selected.
        self._assert_no_questions()

        # Now select a tag

        # TODO/LEFTOFF/NEXT:
        # Figure out how to select a tag.
        #import pdb; pdb.set_trace()
        #pass

        # Assert that a question is shown

    def test_confirm_tags_can_be_selected_unselected(self):
        ''' Assert that tags enabled/disabled during questions and answers are saved and carried over.  '''
        tag1 = Tag(name='tag1')
        tag2 = Tag(name='tag2')
        tag1.save()
        tag2.save()

        question1 = Question(question="question1")
        question2 = Question(question="question2")
        question1.save()
        question2.save()

        self._login()
        self._assert_no_questions()

class NonBrowserTests(TestCase):
    def test_next_question(self):
        ''' Assert that views.next_question() works correctly. '''
        user1 = User(email="user1@bednark.com")
        user2 = User(email="user2@bednark.com")
        user1.save()
        user2.save()

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
        self.assertEquals(UserTag.objects.all().count(), 0)

        # Assert that:
        #   a) a user with no tags 
        #   b) no questions with any tags
        # does not get a question
        with self.assertNumQueries(2):
            question = _next_question(user=user1)
            self.assertIsNone(question)

        # Assert that:
        #   a) user with a UserTag 
        #   b) no questions with that UserTag 
        # does not get a question
        user1_tag1 = UserTag(user=user1, tag=tag1, enabled=True)
        user1_tag1.save()

        for _ in range(3):
            with self.assertNumQueries(2):
                question = _next_question(user=user1)
                self.assertIsNone(question)

        # Assert that 
        #    a) user with a tag 
        #    b) user has no attempts 
        # gets the question
        question1_tag1 = QuestionTag(question=question1, tag=tag1, enabled=True)
        question1_tag1.save()
        with self.assertNumQueries(1):
            question = _next_question(user=user1)
            self.assertEquals(question, question1)

        # Given:
        #       a) QuestionTag.enabled=False 
        # Assert: no question is returned
        question1_tag1.enabled = False
        question1_tag1.save()
        with self.assertNumQueries(2):
            question = _next_question(user=user1)
            self.assertIsNone(question)

        # Given:
        #       a) two questions exist for a given tag
        #       b) question1 has an older attempt
        # Assert that question1 is returned because it's attempt is older
        question1_tag1.enabled = True
        question1_tag1.save()
        question2_tag1 = QuestionTag(question=question2, tag=tag1, enabled=True)
        question2_tag1.save()
        attempt1_question1 = Attempt(question=question1)
        attempt1_question2 = Attempt(question=question2)
        attempt1_question1.save()
        attempt1_question2.save()
        self.assertTrue(attempt1_question2.datetime_added > attempt1_question1.datetime_added)
        with self.assertNumQueries(2):
            question = _next_question(user=user1)
            self.assertEquals(question, question1)

        # Now add a 2nd attempt to question1, and assert that question2 is returned
        # Given:
        #       a) two questions exist for a given tag
        #       b) question1 has two attempts, with the newest attempt newer than question2's newest attempt
        # Assert that question2 is returned because it's attempt is older
        attempt2_question1 = Attempt(question=question1)
        attempt2_question1.save()

        with self.assertNumQueries(2):
            question = _next_question(user=user1)
            self.assertEquals(question, question2)

        # Not add a 3rd attempt to question1, and assert that question2 is still returned
        # Given:
        #       a) two questions exist for a given tag
        #       b) question1 has 3 attempts, with the newest attempt newer than question2's newest attempt
        # Assert that question2 is returned because it's attempt is older
        attempt3_question1 = Attempt(question=question1)
        attempt3_question1.save()

        with self.assertNumQueries(2):
            question = _next_question(user=user1)
            self.assertEquals(question, question2)

        # Now add question3, and assert that question3 is returned, because it doesn't have any attempts yet
        # Given:
        #       a) three questions exist for a given tag
        #       b) question1 has 3 attempts, question2 has 2 attempts, question3 has no attempts
        # Assert that question3 is returned because it has no attempts
        question3 = Question(question="question3")
        question3.save()
        question3_tag1 = QuestionTag(question=question3, tag=tag1, enabled=True)
        question3_tag1.save()
        with self.assertNumQueries(1):
            question = _next_question(user=user1)
            self.assertEquals(question, question3)

    def test_next_question_new(self):
        ''' Assert that views.next_question_new() works correctly. '''
        user1 = User(email="user1@bednark.com")
        user2 = User(email="user2@bednark.com")
        user1.save()
        user2.save()

        tag1 = Tag(name='tag1')
        tag2 = Tag(name='tag2')
        tag1.save()
        tag2.save()

        question1 = Question(question="question1")
        question2 = Question(question="question2")
        question1.save()
        question2.save()

        # Asserts: 2 questions
        #          0 QuestionTag's
        #          0 UserTag's
        self.assertEquals(Question.objects.all().count(), 2)
        self.assertEquals(QuestionTag.objects.all().count(), 0)
        self.assertEquals(UserTag.objects.all().count(), 0)

        # Assert that:
        #   a) a user with no tags 
        #   b) no questions with any tags
        # does not get a question
        with self.assertNumQueries(1):
            question = _next_question_new(user=user1)
            self.assertIsNone(question)

        # Assert that:
        #   a) user with a UserTag 
        #   b) no questions with that UserTag 
        # does not get a question
        user1_tag1 = UserTag(user=user1, tag=tag1, enabled=True)
        user1_tag1.save()
        self.assertEquals(UserTag.objects.filter(user=user1).count(), 1)
        self.assertEquals(QuestionTag.objects.filter(tag=tag1).count(), 0)

        for _ in range(3):
            with self.assertNumQueries(3):
                question = _next_question_new(user=user1)
                self.assertIsNone(question)


        # Assert that 
        #    a) user with a tag 
        #    b) question with that tag
        #    c) user has no schedules
        # gets question1 because it was added before question2
        question1_tag1 = QuestionTag(question=question1, tag=tag1, enabled=True)
        question1_tag1.save()
        self.assertEquals(question1.datetime_added < question2.datetime_added, True)
        self.assertEquals(Question.objects.all().count(), 2)
        self.assertEquals(UserTag.objects.filter(user=user1).count(), 1)
        self.assertEquals(QuestionTag.objects.all().count(), 1)
        self.assertEquals(QuestionTag.objects.filter(tag=tag1, enabled=True).count(), 1)
        self.assertEquals(Schedule.objects.filter(user=user1).count(), 0)

        for n in range(4):
            with self.assertNumQueries(2):
                question = _next_question_new(user=user1)
                self.assertEquals(question, question1, msg="iteration=[%s]" % n)

        # Given:
        #       a) QuestionTag.enabled=False 
        # Assert: no question is returned
        question1_tag1.enabled = False
        question1_tag1.save()
        self.assertEquals(QuestionTag.objects.filter(tag=tag1, enabled=True).count(), 0)
        self.assertEquals(QuestionTag.objects.filter(tag=tag1, enabled=False).count(), 1)
        for _ in range(4):
            with self.assertNumQueries(3):
                question = _next_question_new(user=user1)
                self.assertIsNone(question)

        # Given:
        #       a) question1 and question2 exist for a given tag
        #       b) question1 has a schedule and question2 does not
        # Assert that question2 is returned because it has no schedule
        question1_tag1.enabled = True
        question1_tag1.save()
        question2_tag1 = QuestionTag(question=question2, tag=tag1, enabled=True)
        question2_tag1.save()
        q1_sched1 = Schedule(user=user1, question=question1, interval_num=1, interval_unit='weeks')
        q1_sched1.save()
        self.assertEquals(QuestionTag.objects.filter(tag=tag1, enabled=True).count(), 2)
        self.assertEquals(Schedule.objects.all().count(), 1)
        self.assertEquals(Question.objects.get(id=question1.id).schedule_set.count(), 1)
        for _ in range(5):
            with self.assertNumQueries(2):
                question = _next_question_new(user=user1)
                self.assertEquals(question, question2)

        # Now add a schedule to question2 with an older scheduled date, and assert that question1 is returned
        # Given:
        #       a) two questions exist for a given tag
        #       b) question1 has two schedules, with question1's newest schedule earlier than question2's schedule
        q2_sched1 = Schedule(user=user1, question=question2, interval_num=1, interval_unit='months')
        q1_sched2 = Schedule(user=user1, question=question1, interval_num=1, interval_unit='days')
        q1_sched2.save()
        q2_sched1.save()
        self.assertEquals(q2_sched1.date_show_next > q1_sched2.date_show_next, True)
        for _ in range(5):
            with self.assertNumQueries(3):
                question = _next_question_new(user=user1)
                self.assertEquals(question, question1)

        # Now add a 2nd earlier schedule to question2, and assert that question2 is now returned
        # Given:
        #       a) two questions exist for a given tag
        #       b) question1 and question2 each have 2 schedules
        #       c) question2's newest schedule is earlier than question1's newest schedule
        # Assert that question2 is returned because it's schedule is older
        q2_sched2 = Schedule(user=user1, question=question2, interval_num=5, interval_unit='minutes')
        q2_sched2.save()
        self.assertEquals(q2_sched2.date_show_next < q1_sched1.date_show_next, True)
        for _ in range(5):
            with self.assertNumQueries(3):
                question = _next_question_new(user=user1)
                self.assertEquals(question, question2)
