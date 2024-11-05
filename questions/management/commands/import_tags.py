import csv

from django.core.management.base import BaseCommand

from questions.get_tag_hierarchy import get_tag_hierarchy
from emailusername.models import User
from questions.models import Tag, TagLineage
from .export_tags import (
    COLUMN_NAME_TAG_ID,
    COLUMN_NAME_TAG_RENAME,
    COLUMN_NAME_CHILD_TAG_IDS_TO_ADD,
    COLUMN_NAME_CHILD_TAG_IDS_TO_REMOVE,
    COLUMN_NAME_PARENT_TAG_IDS_TO_ADD,
    COLUMN_NAME_PARENT_TAG_IDS_TO_REMOVE
)

class Command(BaseCommand):

    help = 'Import tag changes from a CSV file'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._options = None
        self._main_tag = None
        self._row_num = None
        self._row = None
        self._tag_hierarchy = None

    def add_arguments(self, parser):
        parser.add_argument('--csv-file', type=str, help='Path to the CSV file', required=True)
        parser.add_argument('--dry-run', action='store_true', help='Dry run to validate.  Don\'t make any changes.', required=False)
        parser.add_argument('--user-id', type=int, help='User ID', required=True)

    def handle(self, *args, **options):
        self._options = options
        self._set_user_and_tag_hierarchy()
        with open(options['csv_file'], 'r') as file:
            reader = csv.DictReader(file)
            for self._row_num, self._row in enumerate(reader):
                self.stdout.write(f"Processing row [{self._row_num+1}]: {self._row}")
                if self._is_main_tag_valid():
                    self._process_tag_renames()
                    self._process_add_lineages()
    
    def _set_user_and_tag_hierarchy(self):
        self._user = User.objects.get(id=self._options['user_id'])
        self._tag_hierarchy = get_tag_hierarchy(user=self._user)

    def _is_main_tag_valid(self):
        if COLUMN_NAME_TAG_ID not in self._row:
            self.stdout.write(self.style.ERROR(
                f'ERROR: Row [{self._row_num+1}]: missing the required column: [{COLUMN_NAME_TAG_ID}]\n'
            ))
            return False
        
        if main_tag_id := self._row[COLUMN_NAME_TAG_ID].strip():
            main_tag_id = int(main_tag_id)
        else:
            self.stdout.write(self.style.ERROR(
                f'ERROR: Row [{self._row_num+1}]: no value in column: [{COLUMN_NAME_TAG_ID}]\n'
            ))
            return False

        if main_tag_id not in self._tag_hierarchy:
            self.stdout.write(self.style.ERROR(
                f'ERROR: Row [{self._row_num+1}]: [{COLUMN_NAME_TAG_ID}] id [{self._row[COLUMN_NAME_TAG_ID]}] does not exist.'
            ))
            self._main_tag_id = None
            return False
        self._main_tag = Tag.objects.get(id=main_tag_id)
        return True

    def _is_valid_tag_id(self, tag_id, col_name):
        if tag_id not in self._tag_hierarchy:
            self.stdout.write(self.style.ERROR(
                f'ERROR: id=[{tag_id}] in column=[{col_name}] is not a valid id.'
            ))
            return False
        return True
    
    def _process_add_lineages(self):
        for col_name in [COLUMN_NAME_CHILD_TAG_IDS_TO_ADD, COLUMN_NAME_CHILD_TAG_IDS_TO_REMOVE, COLUMN_NAME_PARENT_TAG_IDS_TO_ADD, COLUMN_NAME_PARENT_TAG_IDS_TO_REMOVE]:
            if (col_name not in self._row) or (not self._row[col_name]):
                continue
            str_ids = self._row[col_name].split(',')
            ids_to_process = [int(id) for id in str_ids if id]
            for tag_id in ids_to_process:
                if not self._is_valid_tag_id(tag_id=tag_id, col_name=col_name):
                    continue
                if col_name in (COLUMN_NAME_CHILD_TAG_IDS_TO_ADD, COLUMN_NAME_CHILD_TAG_IDS_TO_REMOVE):
                    child_tag = Tag.objects.get(id=tag_id)
                    parent_tag = self._main_tag
                else:  # COLUMN_NAME_PARENT_TAG_IDS_TO_ADD, COLUMN_NAME_PARENT_TAG_IDS_TO_REMOVE
                    parent_tag = Tag.objects.get(id=tag_id)
                    child_tag = self._main_tag
                if col_name in (COLUMN_NAME_CHILD_TAG_IDS_TO_ADD, COLUMN_NAME_PARENT_TAG_IDS_TO_ADD):
                    # verify that the lineage doesn't already exist
                    if parent_tag.id in self._tag_hierarchy[child_tag.id]['parents']:
                        self.stdout.write(self.style.ERROR(
                            f'ERROR: relationship to be added already exists:'
                            f' parent_id=[{parent_tag.id}] parent_name=[{parent_tag.name}]'
                            f' child_id=[{child_tag.id}] child_name=[{child_tag.name}]'
                        ))
                        continue
                    self.stdout.write(self.style.SUCCESS(
                        f"Adding relationship:\n"
                        f"  parent_id  =[{parent_tag.id}]\n"
                        f"  parent_name=[{parent_tag.name}]\n"
                        f"  child_id   =[{child_tag.id}]\n"
                        f"  child_name =[{child_tag.name}]\n"
                    ))
                    if self._options['dry_run']:
                        self.stdout.write(self.style.WARNING('DRY RUN: no changes made.\n'))
                        continue
                    TagLineage.objects.create(
                        parent_tag=parent_tag,
                        child_tag=child_tag, 
                        user=self._user)
                    self._tag_hierarchy = get_tag_hierarchy(user=self._user)
                elif col_name in (COLUMN_NAME_CHILD_TAG_IDS_TO_REMOVE, COLUMN_NAME_PARENT_TAG_IDS_TO_REMOVE):
                    # verify that the lineage exists
                    if parent_tag.id not in self._tag_hierarchy[child_tag.id]['parents']:
                        self.stdout.write(self.style.ERROR(
                            f'ERROR: relationship to be removed does not exist:'
                            f' parent_id=[{parent_tag.id}] parent_name=[{parent_tag.name}]'
                            f' child_id=[{child_tag.id}] child_name=[{child_tag.name}]'
                        ))
                        continue
                    self.stdout.write(self.style.SUCCESS(
                        f"Removing relationship:\n"
                        f"  parent_id  =[{parent_tag.id}]\n"
                        f"  parent_name=[{parent_tag.name}]\n"
                        f"  child_id   =[{child_tag.id}]\n"
                        f"  child_name =[{child_tag.name}]\n"
                    ))
                    if self._options['dry_run']:
                        self.stdout.write(self.style.WARNING('DRY RUN: no changes made.\n'))
                        continue
                    TagLineage.objects.filter(
                        user=self._user,
                        parent_tag_id=parent_tag.id,
                        child_tag_id=child_tag.id,
                    ).delete()
                    self._tag_hierarchy = get_tag_hierarchy(user=self._user)

    def _process_tag_renames(self):
        if tag_new_name := self._row.get(COLUMN_NAME_TAG_RENAME):
            old_name = self._main_tag.name
            if old_name == tag_new_name:
                self.stdout.write(self.style.ERROR(
                    f'ERROR: id=[{self._main_tag.id}] already has the name [{tag_new_name}]\n'
                ))
                return
            self.stdout.write(self.style.SUCCESS(
                f"Renaming from:\n"
                f"   id=[{self._main_tag.id}]"
                f" name=[{old_name}]\n"
                f"to:\n"
                f"   id=[{self._main_tag.id}]"
                f" name=[{tag_new_name}]\n"
            ))
            if self._options['dry_run']:
                self.stdout.write(self.style.WARNING(f'DRY RUN: no changes made.\n'))
            else:
                self._main_tag.name = tag_new_name
                self._main_tag.save()
                # A change was made, so update the tag hierarchy
                self._tag_hierarchy = get_tag_hierarchy(user=self._user)