from django.core.management import call_command
from django.test import TestCase
from django.utils.six import StringIO


class TestManagementCommands(TestCase):
    def test_import_command(self):
        input_data = StringIO('''
Q: this is my question
A: this is my answer
tags: tag2, tag1
Q: my question #2  
line 2 with two spaces on previous line
tags: tag3, tag1
''')
        expected_output = '''\
================================================================================
Question [1]:
================================================================================
this is my question
================================================================================
Answer [1]:
================================================================================
this is my answer
Tags: ['tag1', 'tag2']
================================================================================
Question [2]:
================================================================================
my question #2  
line 2 with two spaces on previous line
================================================================================
Answer [2]: [no answer]
================================================================================
Tags: ['tag1', 'tag3']


Summary:
[2] new tags created: {'tag1', 'tag2', 'tag3'}
[0] existing tags used: set([])
[2] questions added
[1] answer added
'''
        stdout = StringIO()
        call_command('import', stdin=input_data, stdout=stdout)
        self.assertEquals(expected_output, stdout.getvalue())
        # assert no questions, answers, or tags were added
