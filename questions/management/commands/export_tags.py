import csv, sys

from django.core.management.base import BaseCommand
from questions.models import Tag

COLUMN_NAME_PARENT_TAG_ID = "Parent Tag ID"
COLUMN_NAME_PARENT_TAG_NAME = "Parent Tag Name"
COLUMN_NAME_PARENT_TAG_RENAME = "Parent Tag Rename"
COLUMN_NAME_CHILD_TAG_NAMES = "Child Tag Names"
COLUMN_NAME_CHILD_TAG_IDS_TO_ADD = "Child Tag IDs to Add"
COLUMN_NAME_CHILD_TAG_IDS_TO_REMOVE = "Child Tag IDs to Remove"
class Command(BaseCommand):
    help = 'Export tags (including their child relationships) to a CSV'

    def handle(self, *args, **options):
        writer = csv.writer(sys.stdout)
        writer.writerow([
            COLUMN_NAME_PARENT_TAG_ID,
            COLUMN_NAME_PARENT_TAG_NAME,
            COLUMN_NAME_CHILD_TAG_NAMES,
            COLUMN_NAME_CHILD_TAG_IDS_TO_ADD,
            COLUMN_NAME_CHILD_TAG_IDS_TO_REMOVE,
            COLUMN_NAME_PARENT_TAG_RENAME
            ]
        )
        
        for tag in Tag.objects.all().order_by('name'):
            # e.g.,
            # Parent Tag ID | Parent Tag Name | Child Tag Names   | Child Tag IDs to Add | Child Tag IDs to Remove | Parent Tag Rename |
            # ------------- | --------------- | ----------------- | -------------------- | ----------------------- | ------------------|
            # 2             | My tag name     | My child name (3) | 4,5                  | 3                       | My new name       |
            child_names = ', '.join(sorted(f'{child.child_tag.name} ({child.child_tag.id})' for child in tag.children.all()))
            
            writer.writerow([
                tag.id,
                tag.name,
                child_names
            ])
