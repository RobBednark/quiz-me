import os

from django.core.management import call_command
from django.test import TestCase
from django.utils.six import StringIO

from questions import models
from questions.test_helpers import FuzzyInt


class TestManagementCommands(TestCase):
    def test_import_command(self):
        input_data = '''\
Q:    
this is my question
'''
        stdout = StringIO()
        with 
        call_command('import', stdin=input_data, stdout=stdout)
        self.assertIn('Expected output', out.getvalue())
