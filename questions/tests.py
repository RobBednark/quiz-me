"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
import os

from django.test import LiveServerTestCase

from emailusername.models import User
from .models import Tag, UserTag

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

    def test_login_successful_no_questions(self):
        ''' A user can login successfully with correct username and password, and the quiz has no questions. '''
        self.browser.visit(self.live_server_url)
        self.assertEquals(self.browser.title, 'Quiz Me!')
        self.browser.find_by_id('id_username')[0].fill(self.EMAIL_USER1)
        self.browser.find_by_id('id_password')[0].fill(self.PASSWORD)
        self.browser.find_by_value('login').click()
        self.assertEquals(self.browser.title, 'Quiz Me!')
        self.assertTrue(self.browser.is_text_present('(NOTE: there are no questions)'))

    def test_login_fails_incorrect_password(self):
        ''' A user cannot login with an incorrect password. '''
        self.browser.visit(self.live_server_url)
        self.assertEquals(self.browser.title, 'Quiz Me!')
        self.browser.find_by_id('id_username')[0].fill(self.EMAIL_USER1)
        self.browser.find_by_id('id_password')[0].fill("") # No password
        self.browser.find_by_value('login').click()
        self.assertTrue(self.browser.is_text_present("Your username and password didn't match. Please try again."))

    def test_login_fails_incorrect_username(self):
        ''' A user cannot login with an incorrect username. '''
        self.browser.visit(self.live_server_url)
        self.assertEquals(self.browser.title, 'Quiz Me!')
        self.browser.find_by_id('id_username')[0].fill("bad username") # incorrect username
        self.browser.find_by_id('id_password')[0].fill(self.PASSWORD) # correct password
        self.browser.find_by_value('login').click()
        self.assertTrue(self.browser.is_text_present("Your username and password didn't match. Please try again."))

    def test_tags_created_automatically_for_user(self):
        ''' Assert that a UserTag is created for a user when they hit an endpoint after a Tag has been created. '''
        tag1 = Tag(name='tag1')
        tag2 = Tag(name='tag2')
        tag1.save()
        tag2.save()
        self.assertEquals(UserTag.object.count(), 0)

        self.browser.visit(self.live_server_url)
        self.assertEquals(self.browser.title, 'Quiz Me!')
        self.browser.find_by_id('id_username')[0].fill(self.EMAIL_USER1) # incorrect username
        self.browser.find_by_id('id_password')[0].fill(self.PASSWORD) # correct password
        self.browser.find_by_value('login').click()

        self.assertTrue(self.browser.is_text_present('(NOTE: there are no questions)'))

        # Assert there are QuestionTags for this user
