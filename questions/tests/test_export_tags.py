import csv
from io import StringIO

import pytest
from django.core.management import call_command

from questions.management.commands.export_tags import (
    COLUMN_NAME_TAG_ID,
    COLUMN_NAME_TAG_NAME,
    COLUMN_NAME_CHILD_TAG_NAMES,
    COLUMN_NAME_PARENT_TAG_NAMES,
    COLUMN_NAME_COUNT_QUESTIONS_ALL,
    COLUMN_NAME_COUNT_QUESTIONS_TAG,
)
from questions.models import Question, QuestionTag, Tag, TagLineage, User

# Use the Django database for all the tests
pytestmark = pytest.mark.django_db

@pytest.fixture
def user():
    return User.objects.create(email='user@domain.com')

@pytest.fixture
def setup_tags(user):
    tags = []
    for i in range(1, 5):
        tags.append(Tag.objects.create(name=f"tag {i}", user=user))
    tag1, tag2, tag3, tag4 = tags
    
    TagLineage.objects.create(parent_tag=tag1, child_tag=tag2, user=user)
    TagLineage.objects.create(parent_tag=tag2, child_tag=tag3, user=user)
    
    return tags

def test_export_tags_command(user, setup_tags):
    tag1, tag2, tag3, tag4 = setup_tags

    q1 = Question.objects.create(question="Q1", user=user)
    q2 = Question.objects.create(question="Q2", user=user)
    q3 = Question.objects.create(question="Q3", user=user)
    
    QuestionTag.objects.create(question=q1, tag=tag1, user=user)
    QuestionTag.objects.create(question=q2, tag=tag2, user=user)
    QuestionTag.objects.create(question=q3, tag=tag3, user=user)

    file = StringIO()
    call_command('export_tags', f'--user-id={user.id}', stdout=file)
    
    file.seek(0)
    reader = csv.DictReader(file)
    rows = list(reader)

    assert len(rows) == 4

    assert rows[0][COLUMN_NAME_TAG_ID] == f'{tag1.id}'
    assert rows[0][COLUMN_NAME_TAG_NAME] == f'{tag1.name}'
    assert rows[0][COLUMN_NAME_CHILD_TAG_NAMES] == f'{tag2.name} ({tag2.id})'
    assert rows[0][COLUMN_NAME_PARENT_TAG_NAMES] == ''
    assert rows[0][COLUMN_NAME_COUNT_QUESTIONS_ALL] == '3'
    assert rows[0][COLUMN_NAME_COUNT_QUESTIONS_TAG] == '1'

    assert rows[1][COLUMN_NAME_TAG_ID] == f'{tag2.id}'
    assert rows[1][COLUMN_NAME_TAG_NAME] == f'{tag2.name}'
    assert rows[1][COLUMN_NAME_CHILD_TAG_NAMES] == f'{tag3.name} ({tag3.id})'
    assert rows[1][COLUMN_NAME_PARENT_TAG_NAMES] == f'{tag1.name} ({tag1.id})'
    assert rows[1][COLUMN_NAME_COUNT_QUESTIONS_ALL] == '2'
    assert rows[1][COLUMN_NAME_COUNT_QUESTIONS_TAG] == '1'

    assert rows[2][COLUMN_NAME_TAG_ID] == f'{tag3.id}'
    assert rows[2][COLUMN_NAME_TAG_NAME] == f'{tag3.name}'
    assert rows[2][COLUMN_NAME_CHILD_TAG_NAMES] == ''
    assert rows[2][COLUMN_NAME_PARENT_TAG_NAMES] == f'{tag2.name} ({tag2.id})'
    assert rows[2][COLUMN_NAME_COUNT_QUESTIONS_ALL] == '1'
    assert rows[2][COLUMN_NAME_COUNT_QUESTIONS_TAG] == '1'

    assert rows[3][COLUMN_NAME_TAG_ID] == f'{tag4.id}'
    assert rows[3][COLUMN_NAME_TAG_NAME] == f'{tag4.name}'
    assert rows[3][COLUMN_NAME_CHILD_TAG_NAMES] == ''
    assert rows[3][COLUMN_NAME_PARENT_TAG_NAMES] == ''
    assert rows[3][COLUMN_NAME_COUNT_QUESTIONS_ALL] == '0'
    assert rows[3][COLUMN_NAME_COUNT_QUESTIONS_TAG] == '0'

def test_export_tags_ordering(user):
    Tag.objects.create(name='zebra', user=user)
    Tag.objects.create(name='apple', user=user)
    Tag.objects.create(name='monkey', user=user)
    
    file = StringIO()
    call_command('export_tags', f'--user-id={user.id}', stdout=file)
    file.seek(0)
    reader = csv.DictReader(file)
    rows = list(reader)
    assert len(rows) == 3
    assert rows[0][COLUMN_NAME_TAG_NAME] == 'apple'
    assert rows[1][COLUMN_NAME_TAG_NAME] == 'monkey'
    assert rows[2][COLUMN_NAME_TAG_NAME] == 'zebra'