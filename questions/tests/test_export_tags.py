import csv
from io import StringIO

import pytest
from django.core.management import call_command

from questions.management.commands.export_tags import (
    COLUMN_NAME_TAG_ID,
    COLUMN_NAME_TAG_NAME,
    COLUMN_NAME_TAG_RENAME,
    COLUMN_NAME_CHILD_TAG_NAMES,
    COLUMN_NAME_CHILD_TAG_IDS_TO_ADD,
    COLUMN_NAME_CHILD_TAG_IDS_TO_REMOVE,
    COLUMN_NAME_PARENT_TAG_IDS_TO_ADD,
    COLUMN_NAME_PARENT_TAG_IDS_TO_REMOVE,
    COLUMN_NAME_PARENT_TAG_NAMES
)
from questions.models import Tag, TagLineage, User

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

    assert rows[1][COLUMN_NAME_TAG_ID] == f'{tag2.id}'
    assert rows[1][COLUMN_NAME_TAG_NAME] == f'{tag2.name}'
    assert rows[1][COLUMN_NAME_CHILD_TAG_NAMES] == f'{tag3.name} ({tag3.id})'
    assert rows[1][COLUMN_NAME_PARENT_TAG_NAMES] == f'{tag1.name} ({tag1.id})'

    assert rows[2][COLUMN_NAME_TAG_ID] == f'{tag3.id}'
    assert rows[2][COLUMN_NAME_TAG_NAME] == f'{tag3.name}'
    assert rows[2][COLUMN_NAME_CHILD_TAG_NAMES] == ''
    assert rows[2][COLUMN_NAME_PARENT_TAG_NAMES] == f'{tag2.name} ({tag2.id})'

    assert rows[3][COLUMN_NAME_TAG_ID] == f'{tag4.id}'
    assert rows[3][COLUMN_NAME_TAG_NAME] == f'{tag4.name}'
    assert rows[3][COLUMN_NAME_CHILD_TAG_NAMES] == ''
    assert rows[3][COLUMN_NAME_PARENT_TAG_NAMES] == ''

def test_export_tags_empty(user):
    out = StringIO()
    call_command('export_tags', f'--user-id={user.id}', stdout=out)
    
    expected_output = (
        'Tag ID,Tag Name,Child Tag Names,Parent Tag Names,ACTION: Tag Rename,ACTION: Child Tag IDs to Add,'
        'ACTION: Child Tag IDs to Remove,ACTION: Parent Tag IDs to Add,ACTION: Parent Tag IDs to Remove'
    )
    
    assert out.getvalue().strip() == expected_output.strip()

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