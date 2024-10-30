import pytest
import csv
import tempfile
from django.contrib.auth import get_user_model
from django.core.management import call_command
from questions.models import Tag, TagLineage
from questions.get_tag_hierarchy import get_tag_hierarchy
from questions.management.commands.export_tags import (
    COLUMN_NAME_TAG_ID,
    COLUMN_NAME_TAG_RENAME,
    COLUMN_NAME_CHILD_TAG_IDS_TO_ADD,
    COLUMN_NAME_CHILD_TAG_IDS_TO_REMOVE,
    COLUMN_NAME_PARENT_TAG_IDS_TO_ADD,
    COLUMN_NAME_PARENT_TAG_IDS_TO_REMOVE
)

User = get_user_model()

@pytest.mark.django_db
class TestImportTagsCommand:
    @pytest.fixture
    def user(self):
        return User.objects.create(email="test@example.com")
    
    @pytest.fixture
    def setup_tags(self, user):
        tags = []
        for i in range(1, 5):
            tags.append(Tag.objects.create(name=f"tag {i}", user=user))
        return tags

    @pytest.fixture
    def csv_file(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            fieldnames = [
                COLUMN_NAME_TAG_ID,
                COLUMN_NAME_TAG_RENAME,
                COLUMN_NAME_CHILD_TAG_IDS_TO_ADD,
                COLUMN_NAME_CHILD_TAG_IDS_TO_REMOVE,
                COLUMN_NAME_PARENT_TAG_IDS_TO_ADD,
                COLUMN_NAME_PARENT_TAG_IDS_TO_REMOVE
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            return f.name

    def test_rename_tag(self, user, setup_tags, csv_file):
        tag = setup_tags[0]
        new_name = "renamed_tag"
        
        with open(csv_file, 'w') as f:
            writer = csv.DictWriter(f, fieldnames=[
                COLUMN_NAME_TAG_ID,
                COLUMN_NAME_TAG_RENAME
            ])
            writer.writeheader()
            writer.writerow({
                COLUMN_NAME_TAG_ID: tag.id,
                COLUMN_NAME_TAG_RENAME: new_name
            })

        call_command('import_tags', csv_file=csv_file, user_id=user.id)
        tag.refresh_from_db()
        assert tag.name == new_name

    def test_add_child_tags(self, user, setup_tags, csv_file):
        parent_tag, child_tag = setup_tags[0:2]
        
        with open(csv_file, 'w') as f:
            writer = csv.DictWriter(f, fieldnames=[
                COLUMN_NAME_TAG_ID,
                COLUMN_NAME_CHILD_TAG_IDS_TO_ADD
            ])
            writer.writeheader()
            writer.writerow({
                COLUMN_NAME_TAG_ID: parent_tag.id,
                COLUMN_NAME_CHILD_TAG_IDS_TO_ADD: str(child_tag.id)
            })

        call_command('import_tags', csv_file=csv_file, user_id=user.id)
        hierarchy = get_tag_hierarchy(user)
        assert child_tag.id in hierarchy[parent_tag.id]['children']

    def test_remove_child_tags(self, user, setup_tags, csv_file):
        parent_tag, child_tag = setup_tags[0:2]
        TagLineage.objects.create(parent_tag=parent_tag, child_tag=child_tag, user=user)
        
        with open(csv_file, 'w') as f:
            writer = csv.DictWriter(f, fieldnames=[
                COLUMN_NAME_TAG_ID,
                COLUMN_NAME_CHILD_TAG_IDS_TO_REMOVE
            ])
            writer.writeheader()
            writer.writerow({
                COLUMN_NAME_TAG_ID: parent_tag.id,
                COLUMN_NAME_CHILD_TAG_IDS_TO_REMOVE: str(child_tag.id)
            })

        call_command('import_tags', csv_file=csv_file, user_id=user.id)
        hierarchy = get_tag_hierarchy(user)
        assert child_tag.id not in hierarchy[parent_tag.id]['children']

    def test_dry_run_makes_no_changes(self, user, setup_tags, csv_file):
        tag = setup_tags[0]
        original_name = tag.name
        new_name = "should_not_rename"
        
        with open(csv_file, 'w') as f:
            writer = csv.DictWriter(f, fieldnames=[
                COLUMN_NAME_TAG_ID,
                COLUMN_NAME_TAG_RENAME
            ])
            writer.writeheader()
            writer.writerow({
                COLUMN_NAME_TAG_ID: tag.id,
                COLUMN_NAME_TAG_RENAME: new_name
            })

        call_command('import_tags', csv_file=csv_file, user_id=user.id, dry_run=True)
        tag.refresh_from_db()
        assert tag.name == original_name
        
    def test_add_parent_tags(self, user, setup_tags, csv_file):
        child_tag, parent_tag = setup_tags[0:2]
        
        with open(csv_file, 'w') as f:
            writer = csv.DictWriter(f, fieldnames=[
                COLUMN_NAME_TAG_ID,
                COLUMN_NAME_PARENT_TAG_IDS_TO_ADD
            ])
            writer.writeheader()
            writer.writerow({
                COLUMN_NAME_TAG_ID: child_tag.id,
                COLUMN_NAME_PARENT_TAG_IDS_TO_ADD: str(parent_tag.id)
            })
    
        call_command('import_tags', csv_file=csv_file, user_id=user.id)
        hierarchy = get_tag_hierarchy(user)
        assert parent_tag.id in hierarchy[child_tag.id]['parents']

    def test_remove_parent_tags(self, user, setup_tags, csv_file):
        child_tag, parent_tag = setup_tags[0:2]
        TagLineage.objects.create(parent_tag=parent_tag, child_tag=child_tag, user=user)
        
        with open(csv_file, 'w') as f:
            writer = csv.DictWriter(f, fieldnames=[
                COLUMN_NAME_TAG_ID,
                COLUMN_NAME_PARENT_TAG_IDS_TO_REMOVE
            ])
            writer.writeheader()
            writer.writerow({
                COLUMN_NAME_TAG_ID: child_tag.id,
                COLUMN_NAME_PARENT_TAG_IDS_TO_REMOVE: str(parent_tag.id)
            })
    
        call_command('import_tags', csv_file=csv_file, user_id=user.id)
        hierarchy = get_tag_hierarchy(user)
        assert parent_tag.id not in hierarchy[child_tag.id]['parents']