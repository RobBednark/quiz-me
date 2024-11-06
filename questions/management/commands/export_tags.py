import csv, sys

from django.core.management.base import BaseCommand
from questions.get_tag_hierarchy import get_tag_hierarchy
from questions.models import Tag, User

COLUMN_NAME_TAG_ID = "Tag ID"
COLUMN_NAME_TAG_NAME = "Tag Name"
COLUMN_NAME_TAG_RENAME = "ACTION: Tag Rename"
COLUMN_NAME_CHILD_TAG_NAMES = "Child Tag Names"
COLUMN_NAME_PARENT_TAG_NAMES = "Parent Tag Names"
COLUMN_NAME_CHILD_TAG_IDS_TO_ADD = "ACTION: Child Tag IDs to Add"
COLUMN_NAME_CHILD_TAG_IDS_TO_REMOVE = "ACTION: Child Tag IDs to Remove"
COLUMN_NAME_PARENT_TAG_IDS_TO_ADD = "ACTION: Parent Tag IDs to Add"
COLUMN_NAME_PARENT_TAG_IDS_TO_REMOVE = "ACTION: Parent Tag IDs to Remove"
fieldnames = [
    COLUMN_NAME_TAG_ID,
    COLUMN_NAME_TAG_NAME,
    COLUMN_NAME_CHILD_TAG_NAMES,
    COLUMN_NAME_PARENT_TAG_NAMES,
    COLUMN_NAME_TAG_RENAME,
    COLUMN_NAME_CHILD_TAG_IDS_TO_ADD,
    COLUMN_NAME_CHILD_TAG_IDS_TO_REMOVE,
    COLUMN_NAME_PARENT_TAG_IDS_TO_ADD,
    COLUMN_NAME_PARENT_TAG_IDS_TO_REMOVE,
]
class Command(BaseCommand):
    help = 'Export tags (including their child relationships) to a CSV'
    def add_arguments(self, parser):
        parser.add_argument('--user-id', type=int, help='User ID', required=True)

    def handle(self, *args, **options):
        writer = csv.DictWriter(self.stdout, fieldnames=fieldnames)
        writer.writeheader()
        self.tag_hierarchy = get_tag_hierarchy(user=User.objects.get(id=options['user_id']))
        
        for tag in Tag.objects.all().order_by('name'):
            # e.g.,
            # Tag ID | Tag Name | Child Tag Names   | Child Tag IDs to Add | Child Tag IDs to Remove | Tag Rename |
            # ------------- | --------------- | ----------------- | -------------------- | ----------------------- | ------------------|
            # 2             | My tag name     | My child name (3) | 4,5                  | 3                       | My new name       |
            writer.writerow({
                COLUMN_NAME_TAG_ID: tag.id,
                COLUMN_NAME_TAG_NAME: tag.name,
                COLUMN_NAME_PARENT_TAG_NAMES: self._get_names_and_ids(tag_id=tag.id, type_='parents'),
                COLUMN_NAME_CHILD_TAG_NAMES: self._get_names_and_ids(tag_id=tag.id, type_='children'),
            })

    def _get_names_and_ids(self, tag_id, type_):
        '''
        Return a comma-separated string (in alphabetical order) of tag names and ids for the given type_, where type_ is one of the tag_hierarchy keys ('children', 'parents', 'ancestors', 'descendants', 'descendants_and_self').
        e.g.,
          self._get_names_and_ids(tag_id=1, type_='children') == 'my tag 1 (2), my tag 2 (3)'
        '''
        list = []
        for item in self.tag_hierarchy[tag_id][type_]:
            # e.g., "my tag name (1)"
            list.append(f'{self.tag_hierarchy[item]["tag_name"]} ({item})')
        return ', '.join(sorted(list))