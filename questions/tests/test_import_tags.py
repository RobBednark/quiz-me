import pytest
import csv
import tempfile
from django.contrib.auth import get_user_model
from django.core.management import call_command
from questions.models import Tag, TagLineage
from questions.get_tag_hierarchy import get_tag_hierarchy
from questions.management.commands.export_tags import (
    COLUMN_NAME_TAG_ID,
    COLUMN_NAME_TAG_NAME,
    COLUMN_NAME_TAG_RENAME,
    COLUMN_NAME_CHILD_TAG_NAMES,
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
        # Write the column names to a file and return the file name
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

    def test_no_tag_id_column(self, capsys, user):
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
        csv_file = f.name
        
        with open(csv_file, 'w') as f:
            writer = csv.DictWriter(f, fieldnames=[
                COLUMN_NAME_TAG_RENAME
            ])
            writer.writeheader()
            writer.writerow({
                COLUMN_NAME_TAG_RENAME: 'foo'
            })

        call_command('import_tags', csv_file=csv_file, user_id=user.id)
        expected = '''\
Processing row [1]: {'ACTION: Tag Rename': 'foo'}
ERROR: Row [1]: missing the required column: [Tag ID]
'''
        assert expected == capsys.readouterr().out

    def test_rename_tag(self, user, setup_tags, csv_file):
        tag = setup_tags[0]
        NEW_NAME = "renamed_tag"
        
        with open(csv_file, 'w') as f:
            writer = csv.DictWriter(f, fieldnames=[
                COLUMN_NAME_TAG_ID,
                COLUMN_NAME_TAG_RENAME
            ])
            writer.writeheader()
            writer.writerow({
                COLUMN_NAME_TAG_ID: tag.id,
                COLUMN_NAME_TAG_RENAME: NEW_NAME
            })

        call_command('import_tags', csv_file=csv_file, user_id=user.id)
        tag.refresh_from_db()
        assert tag.name == NEW_NAME

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
        NEW_NAME = "should_not_rename"
        
        with open(csv_file, 'w') as f:
            writer = csv.DictWriter(f, fieldnames=[
                COLUMN_NAME_TAG_ID,
                COLUMN_NAME_TAG_RENAME
            ])
            writer.writeheader()
            writer.writerow({
                COLUMN_NAME_TAG_ID: tag.id,
                COLUMN_NAME_TAG_RENAME: NEW_NAME
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

    def test_import_tags_empty_columns(self, user, setup_tags, csv_file):
        tag = setup_tags[0]
        # Create temporary CSV file with empty columns
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp_file:
            fieldnames = [
                COLUMN_NAME_TAG_ID,
                COLUMN_NAME_TAG_NAME,
                COLUMN_NAME_CHILD_TAG_NAMES,
                COLUMN_NAME_CHILD_TAG_IDS_TO_ADD,
                COLUMN_NAME_CHILD_TAG_IDS_TO_REMOVE,
                COLUMN_NAME_TAG_RENAME,
                COLUMN_NAME_PARENT_TAG_IDS_TO_ADD,
                COLUMN_NAME_PARENT_TAG_IDS_TO_REMOVE
            ]
            writer = csv.DictWriter(tmp_file, fieldnames=fieldnames)
            writer.writeheader()
            
            # Write data row with empty values
            writer.writerow({
                COLUMN_NAME_TAG_ID: tag.id,
                COLUMN_NAME_TAG_NAME: tag.name,
                COLUMN_NAME_CHILD_TAG_NAMES: '',
                COLUMN_NAME_CHILD_TAG_IDS_TO_ADD: '',
                COLUMN_NAME_CHILD_TAG_IDS_TO_REMOVE: '',
                COLUMN_NAME_TAG_RENAME: '',
                COLUMN_NAME_PARENT_TAG_IDS_TO_ADD: '',
                COLUMN_NAME_PARENT_TAG_IDS_TO_REMOVE: ''
            })
            tmp_filepath = tmp_file.name

        # Run import command
        hierarchy_before = get_tag_hierarchy(user)
        call_command('import_tags', 
                    csv_file=tmp_filepath,
                    user_id=user.id)

        # Verify tag remains unchanged
        assert hierarchy_before == get_tag_hierarchy(user)
        updated_tag = Tag.objects.get(id=tag.id)
        assert updated_tag.name == "tag 1"
        assert updated_tag.user == user

    def _csv_write_all_happy_paths(self, writer, tag1, tag2, tag3, tag4):
        writer.writerow({
            COLUMN_NAME_TAG_ID: tag1.id,
            COLUMN_NAME_CHILD_TAG_IDS_TO_ADD: tag4.id,
            COLUMN_NAME_CHILD_TAG_IDS_TO_REMOVE: tag2.id,
            COLUMN_NAME_TAG_RENAME: "renamed_tag_1",
            COLUMN_NAME_PARENT_TAG_IDS_TO_ADD: tag3.id,
        })
        writer.writerow({
            COLUMN_NAME_TAG_ID: tag3.id,
            COLUMN_NAME_PARENT_TAG_IDS_TO_REMOVE: f"{tag1.id}"
        })
            
    def test_import_tags_all_happy_paths(self, user, setup_tags, csv_file, capsys):
        # Start:
        # Parent > Child
        # 1 > 2 (1: remove child 2)
        # 1 > 3 (3: remove parent 1)
        # 1 > 4 (1: add child 4)
        # 3 > 1 (1: add parent 3)
        tag1, tag2, tag3, tag4 = setup_tags[0:4]
        TagLineage.objects.create(parent_tag=tag1, child_tag=tag2, user=user)
        TagLineage.objects.create(parent_tag=tag1, child_tag=tag3, user=user)
        
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp_file:
            fieldnames = [
                COLUMN_NAME_TAG_ID,
                COLUMN_NAME_TAG_NAME,
                COLUMN_NAME_CHILD_TAG_NAMES,
                COLUMN_NAME_CHILD_TAG_IDS_TO_ADD,
                COLUMN_NAME_CHILD_TAG_IDS_TO_REMOVE,
                COLUMN_NAME_TAG_RENAME,
                COLUMN_NAME_PARENT_TAG_IDS_TO_ADD,
                COLUMN_NAME_PARENT_TAG_IDS_TO_REMOVE
            ]
            writer = csv.DictWriter(tmp_file, fieldnames=fieldnames)
            writer.writeheader()
            self._csv_write_all_happy_paths(writer, tag1, tag2, tag3, tag4)
            tmp_filepath = tmp_file.name
    
        
        hier = get_tag_hierarchy(user)
        assert hier[tag1.id]['tag_name'] == 'tag 1'
        assert hier[tag1.id]['children'] == {tag2.id, tag3.id}
        assert hier[tag2.id]['children'] == set()
        assert hier[tag3.id]['children'] == set()
        assert hier[tag4.id]['children'] == set()

        call_command('import_tags', csv_file=tmp_filepath, user_id=user.id)
        expected_stdout = f'''\
Processing row [1]: {{'Tag ID': '{tag1.id}', 'Tag Name': '', 'Child Tag Names': '', 'ACTION: Child Tag IDs to Add': '{tag4.id}', 'ACTION: Child Tag IDs to Remove': '{tag2.id}', 'ACTION: Tag Rename': 'renamed_tag_1', 'ACTION: Parent Tag IDs to Add': '{tag3.id}', 'ACTION: Parent Tag IDs to Remove': ''}}
CHANGE: Rename: [tag 1] ({tag1.id}) => [renamed_tag_1] ({tag1.id})
CHANGE: Adding relationship: [renamed_tag_1] => [tag 4]
CHANGE: Removing relationship: [renamed_tag_1] ({tag1.id}) => [tag 2] ({tag2.id})
CHANGE: Adding relationship: [tag 3] => [renamed_tag_1]
Processing row [2]: {{'Tag ID': '{tag3.id}', 'Tag Name': '', 'Child Tag Names': '', 'ACTION: Child Tag IDs to Add': '', 'ACTION: Child Tag IDs to Remove': '', 'ACTION: Tag Rename': '', 'ACTION: Parent Tag IDs to Add': '', 'ACTION: Parent Tag IDs to Remove': '{tag1.id}'}}
CHANGE: Removing relationship: [renamed_tag_1] ({tag1.id}) => [tag 3] ({tag3.id})
'''
        assert expected_stdout == capsys.readouterr().out
        
        hier = get_tag_hierarchy(user)
        assert hier[tag1.id]['tag_name'] == 'renamed_tag_1'
        assert hier[tag1.id]['children'] == {tag4.id}
        assert hier[tag2.id]['children'] == set()
        assert hier[tag3.id]['children'] == {tag1.id}
        assert hier[tag4.id]['children'] == set()

    def test_import_tags_all_happy_paths_dry_run(self, user, setup_tags, csv_file, capsys):
        # Start:
        # Parent > Child
        # 1 > 2 (1: remove child 2)
        # 1 > 3 (3: remove parent 1)
        # 1 > 4 (1: add child 4)
        # 3 > 1 (1: add parent 3)
        tag1, tag2, tag3, tag4 = setup_tags[0:4]
        TagLineage.objects.create(parent_tag=tag1, child_tag=tag2, user=user)
        TagLineage.objects.create(parent_tag=tag1, child_tag=tag3, user=user)
        
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp_file:
            fieldnames = [
                COLUMN_NAME_TAG_ID,
                COLUMN_NAME_TAG_NAME,
                COLUMN_NAME_CHILD_TAG_NAMES,
                COLUMN_NAME_CHILD_TAG_IDS_TO_ADD,
                COLUMN_NAME_CHILD_TAG_IDS_TO_REMOVE,
                COLUMN_NAME_TAG_RENAME,
                COLUMN_NAME_PARENT_TAG_IDS_TO_ADD,
                COLUMN_NAME_PARENT_TAG_IDS_TO_REMOVE
            ]
            writer = csv.DictWriter(tmp_file, fieldnames=fieldnames)
            writer.writeheader()
            self._csv_write_all_happy_paths(writer, tag1, tag2, tag3, tag4)
            tmp_filepath = tmp_file.name
    
        
        hier = get_tag_hierarchy(user)
        assert hier[tag1.id]['tag_name'] == 'tag 1'
        assert hier[tag1.id]['children'] == {tag2.id, tag3.id}
        assert hier[tag2.id]['children'] == set()
        assert hier[tag3.id]['children'] == set()
        assert hier[tag4.id]['children'] == set()

        call_command('import_tags', csv_file=tmp_filepath, user_id=user.id, dry_run=True)
        expected_stdout = f'''\
DRY RUN: no changes made.
Processing row [1]: {{'Tag ID': '{tag1.id}', 'Tag Name': '', 'Child Tag Names': '', 'ACTION: Child Tag IDs to Add': '{tag4.id}', 'ACTION: Child Tag IDs to Remove': '{tag2.id}', 'ACTION: Tag Rename': 'renamed_tag_1', 'ACTION: Parent Tag IDs to Add': '{tag3.id}', 'ACTION: Parent Tag IDs to Remove': ''}}
CHANGE: Rename: [tag 1] ({tag1.id}) => [renamed_tag_1] ({tag1.id})
CHANGE: Adding relationship: [tag 1] => [tag 4]
CHANGE: Removing relationship: [tag 1] ({tag1.id}) => [tag 2] ({tag2.id})
CHANGE: Adding relationship: [tag 3] => [tag 1]
Processing row [2]: {{'Tag ID': '{tag3.id}', 'Tag Name': '', 'Child Tag Names': '', 'ACTION: Child Tag IDs to Add': '', 'ACTION: Child Tag IDs to Remove': '', 'ACTION: Tag Rename': '', 'ACTION: Parent Tag IDs to Add': '', 'ACTION: Parent Tag IDs to Remove': '{tag1.id}'}}
CHANGE: Removing relationship: [tag 1] ({tag1.id}) => [tag 3] ({tag3.id})
DRY RUN: no changes made.
'''
        assert expected_stdout == capsys.readouterr().out
        
        hier = get_tag_hierarchy(user)
        assert hier[tag1.id]['tag_name'] == 'tag 1'
        assert hier[tag1.id]['children'] == {tag2.id, tag3.id}
        assert hier[tag2.id]['children'] == set()
        assert hier[tag3.id]['children'] == set()
        assert hier[tag4.id]['children'] == set()

    def test_import_tags_all_error_conditions(self, user, setup_tags, csv_file, capsys):
        tag1, tag2, tag3, tag4 = setup_tags[0:4]
        NON_EXISTENT_TAG_ID = 99999
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp_file:
            fieldnames = [
                COLUMN_NAME_TAG_ID,
                COLUMN_NAME_TAG_NAME,
                COLUMN_NAME_CHILD_TAG_NAMES,
                COLUMN_NAME_CHILD_TAG_IDS_TO_ADD,
                COLUMN_NAME_CHILD_TAG_IDS_TO_REMOVE,
                COLUMN_NAME_TAG_RENAME,
                COLUMN_NAME_PARENT_TAG_IDS_TO_ADD,
                COLUMN_NAME_PARENT_TAG_IDS_TO_REMOVE
            ]
            writer = csv.DictWriter(tmp_file, fieldnames=fieldnames)
            writer.writeheader()
            
            # Row 1: Missing tag_id
            writer.writerow({
                COLUMN_NAME_TAG_ID: '',
                COLUMN_NAME_TAG_NAME: 'Test Tag',
                COLUMN_NAME_CHILD_TAG_IDS_TO_ADD: f"{tag2.id}"
            })
            
            # Row 2: Non-existent tag_id
            writer.writerow({
                COLUMN_NAME_TAG_ID: NON_EXISTENT_TAG_ID,
                COLUMN_NAME_TAG_NAME: 'Test Tag',
                COLUMN_NAME_CHILD_TAG_IDS_TO_ADD: f"{tag2.id}"
            })
            
            # Row 3: Try to add non-existent child tag
            writer.writerow({
                COLUMN_NAME_TAG_ID: tag1.id,
                COLUMN_NAME_CHILD_TAG_IDS_TO_ADD: f"{NON_EXISTENT_TAG_ID}"
            })
            
            # Row 4: Try to remove non-existent child relationship
            writer.writerow({
                COLUMN_NAME_TAG_ID: tag1.id,
                COLUMN_NAME_CHILD_TAG_IDS_TO_REMOVE: f"{tag2.id}"
            })
            
            # Row 5: Try to add already existing child relationship
            TagLineage.objects.create(parent_tag=tag3, child_tag=tag4, user=user)
            writer.writerow({
                COLUMN_NAME_TAG_ID: tag3.id,
                COLUMN_NAME_CHILD_TAG_IDS_TO_ADD: f"{tag4.id}"
            })
            
            # Row 6: Try to rename tag to its current name
            writer.writerow({
                COLUMN_NAME_TAG_ID: tag1.id,
                COLUMN_NAME_TAG_RENAME: tag1.name
            })
            
            tmp_filepath = tmp_file.name
    
        # Run import command and capture output
        call_command('import_tags', csv_file=tmp_filepath, user_id=user.id)
        
        expected = f'''\
Processing row [1]: {{'Tag ID': '', 'Tag Name': 'Test Tag', 'Child Tag Names': '', 'ACTION: Child Tag IDs to Add': '{tag2.id}', 'ACTION: Child Tag IDs to Remove': '', 'ACTION: Tag Rename': '', 'ACTION: Parent Tag IDs to Add': '', 'ACTION: Parent Tag IDs to Remove': ''}}
ERROR: Row [1]: no value in column: [Tag ID]
Processing row [2]: {{'Tag ID': '99999', 'Tag Name': 'Test Tag', 'Child Tag Names': '', 'ACTION: Child Tag IDs to Add': '{tag2.id}', 'ACTION: Child Tag IDs to Remove': '', 'ACTION: Tag Rename': '', 'ACTION: Parent Tag IDs to Add': '', 'ACTION: Parent Tag IDs to Remove': ''}}
ERROR: Row [2]: [Tag ID] id [99999] does not exist.
Processing row [3]: {{'Tag ID': '{tag1.id}', 'Tag Name': '', 'Child Tag Names': '', 'ACTION: Child Tag IDs to Add': '99999', 'ACTION: Child Tag IDs to Remove': '', 'ACTION: Tag Rename': '', 'ACTION: Parent Tag IDs to Add': '', 'ACTION: Parent Tag IDs to Remove': ''}}
ERROR: id=[99999] in column=[ACTION: Child Tag IDs to Add] is not a valid id.
Processing row [4]: {{'Tag ID': '{tag1.id}', 'Tag Name': '', 'Child Tag Names': '', 'ACTION: Child Tag IDs to Add': '', 'ACTION: Child Tag IDs to Remove': '{tag2.id}', 'ACTION: Tag Rename': '', 'ACTION: Parent Tag IDs to Add': '', 'ACTION: Parent Tag IDs to Remove': ''}}
ERROR: relationship to be removed does not exist: [tag 1] ({tag1.id}) => [tag 2] ({tag2.id})
Processing row [5]: {{'Tag ID': '{tag3.id}', 'Tag Name': '', 'Child Tag Names': '', 'ACTION: Child Tag IDs to Add': '{tag4.id}', 'ACTION: Child Tag IDs to Remove': '', 'ACTION: Tag Rename': '', 'ACTION: Parent Tag IDs to Add': '', 'ACTION: Parent Tag IDs to Remove': ''}}
ERROR: already exists: [tag 3] ({tag3.id}) => [tag 4] ({tag4.id})
Processing row [6]: {{'Tag ID': '{tag1.id}', 'Tag Name': '', 'Child Tag Names': '', 'ACTION: Child Tag IDs to Add': '', 'ACTION: Child Tag IDs to Remove': '', 'ACTION: Tag Rename': 'tag 1', 'ACTION: Parent Tag IDs to Add': '', 'ACTION: Parent Tag IDs to Remove': ''}}
ERROR: id=[{tag1.id}] already has the name [tag 1]
'''
        assert expected == capsys.readouterr().out

        # Verify no changes were made
        hierarchy = get_tag_hierarchy(user)
        assert tag4.id in hierarchy[tag3.id]['children']
        assert Tag.objects.get(id=tag1.id).name == tag1.name