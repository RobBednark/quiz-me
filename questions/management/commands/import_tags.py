import csv

from django.core.management.base import BaseCommand

from questions.get_tag_hierarchy import get_tag_hierarchy
from emailusername.models import User
from questions.models import Tag, TagLineage
from .export_tags import (
    COLUMN_NAME_CHILD_TAG_IDS_TO_ADD,
    COLUMN_NAME_CHILD_TAG_IDS_TO_REMOVE,
    COLUMN_NAME_PARENT_TAG_ID,
    COLUMN_NAME_PARENT_TAG_RENAME,
)

class Command(BaseCommand):
    help = 'Import tag changes from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('--csv-file', type=str, help='Path to the CSV file', required=True)
        parser.add_argument('--dry-run', action='store_true', help='Dry run to validate.  Don\'t make any changes.', required=False)
        parser.add_argument('--user-id', type=int, help='User ID', required=True)

    def _errors_found(self, parent_tag_id, child_tag_id, tag_hierarchy, _type, row_num):
        errors_found = False

        if (_type == 'validate_parent'):
            if (parent_tag_id not in tag_hierarchy):
                self.stdout.write(self.style.WARNING(f'WARNING: parent tag not found: id=[{parent_tag_id}]'))
                errors_found = True
            return errors_found

        if child_tag_id not in tag_hierarchy:
            self.stdout.write(self.style.WARNING(f'WARNING: child tag not found: id=[{child_tag_id}]'))
            errors_found = True
            return errors_found

        child_name = tag_hierarchy[child_tag_id]['tag_name']
        parent_name = tag_hierarchy[parent_tag_id]['tag_name']

        if (_type == 'add') and (child_tag_id in tag_hierarchy[parent_tag_id]['children']):
            self.stdout.write(self.style.WARNING(
                f'WARNING:\n'
                f'Parent:\n'
                f'  [{parent_tag_id}] [{parent_name}]\n'
                f'already has child to be added:\n'
                f'  [{child_tag_id}] [{child_name}]\n\n'
            ))
            errors_found = True
            return errors_found

        if (_type == 'remove') and (child_tag_id not in tag_hierarchy[parent_tag_id]['children']):
            self.stdout.write(self.style.WARNING(
                f'WARNING:\n'
                f'Parent:\n'
                f'  [{parent_tag_id}] [{parent_name}]\n'
                f'does not have child to remove:\n'
                f'  [{child_tag_id}] [{child_name}]\n\n'
            ))
            errors_found = True
            return errors_found

        if _type == 'add':
            self.stdout.write(self.style.SUCCESS(
                f"To parent:\n"
                f"   [{parent_tag_id}]"
                f" [{parent_name}]\n"
                f"adding child:\n"
                f"   [{child_tag_id}]"
                f" [{child_name}]\n\n"
            ))

        if _type == 'remove':
            self.stdout.write(self.style.SUCCESS(
                f"From parent:\n"
                f"   [{parent_tag_id}]"
                f" [{parent_name}]\n"
                f"removing child:\n"
                f"   [{child_tag_id}]"
                f" [{child_name}]\n\n"
            ))

        return errors_found
    
    def handle(self, *args, **options):
        csv_file = options['csv_file']
        dry_run = options['dry_run']
        user = User.objects.get(id=options['user_id'])
        tag_hierachy = get_tag_hierarchy(user=user)
        with open(csv_file, 'r') as file:
            reader = csv.DictReader(file)
            for row_num, row in enumerate(reader):
                self.stdout.write(f"Processing row [{row_num+1}]: {row}")
                child_tags_to_add = row.get(COLUMN_NAME_CHILD_TAG_IDS_TO_ADD)
                child_tags_to_remove = row.get(COLUMN_NAME_CHILD_TAG_IDS_TO_REMOVE)
                parent_tag_id = int(row.get(COLUMN_NAME_PARENT_TAG_ID).strip())
                parent_tag_rename = row.get(COLUMN_NAME_PARENT_TAG_RENAME)
                if self._errors_found(parent_tag_id=parent_tag_id, child_tag_id=None, tag_hierarchy=tag_hierachy, _type='validate_parent', row_num=row_num):
                    continue

                if child_tags_to_add:
                    # Add the COLUMN_NAME_CHILD_TAG_IDS_TO_ADD to the COLUMN_NAME_PARENT_TAG_ID
                    child_tag_ids = [int(id.strip()) for id in child_tags_to_add.split(',') if id.strip()]

                    for child_tag_id in child_tag_ids:
                        if self._errors_found(parent_tag_id=parent_tag_id, child_tag_id=child_tag_id, tag_hierarchy=tag_hierachy, _type='add', row_num=row_num):
                            continue
                        if dry_run:
                            self.stdout.write(self.style.WARNING(f'DRY RUN: no changes made.'))
                            continue
                        parent_tag = Tag.objects.get(id=parent_tag_id)
                        child_tag = Tag.objects.get(id=child_tag_id)
                        TagLineage.objects.create(
                            parent_tag=parent_tag,
                            child_tag=child_tag,
                            user=user
                        )
                        # Change was made, so update the tag hierarchy
                        tag_hierachy = get_tag_hierarchy(user=user)

                if child_tags_to_remove:
                    # Remove the COLUMN_NAME_CHILD_TAG_IDS_TO_REMOVE from the COLUMN_NAME_PARENT_TAG_ID
                    child_tag_ids = [int(id.strip()) for id in child_tags_to_remove.split(',') if id.strip()]
                    
                    for child_tag_id in child_tag_ids:
                        if self._errors_found(parent_tag_id=parent_tag_id, child_tag_id=child_tag_id, tag_hierarchy=tag_hierachy, _type='remove', row_num=row_num):
                            continue
                        if dry_run:
                            self.stdout.write(self.style.WARNING(f'DRY RUN: no changes made.\n'))
                            continue
                        TagLineage.objects.filter(parent_tag=parent_tag, child_tag=child_tag).delete()
                        # Change was made, so update the tag hierarchy
                        tag_hierachy = get_tag_hierarchy(user=user)

                if parent_tag_rename:
                    # Remove the COLUMN_NAME_CHILD_TAG_IDS_TO_REMOVE from the COLUMN_NAME_PARENT_TAG_ID
                    parent_tag = Tag.objects.get(id=parent_tag_id)
                    old_name = parent_tag.name
                    if old_name == parent_tag_rename:
                        self.stdout.write(self.style.WARNING(
                            f'WARNING:\n'
                            f'Parent:\n'
                            f'  [{parent_tag.id}]'
                            f' [{old_name}]\n'
                            f'already has the same name:\n'
                            f'  [{parent_tag.id}]'
                            f' [{parent_tag_rename}]\n\n'
                        ))
                        continue
                    parent_tag.name = parent_tag_rename
                    self.stdout.write(self.style.SUCCESS(
                        f"Renaming from:\n"
                        f"   [{parent_tag.id}]"
                        f" [{old_name}]\n"
                        f"to:\n"
                        f"   [{parent_tag.id}]"
                        f" [{parent_tag_rename}]"
                    ))
                    if dry_run:
                        self.stdout.write(self.style.WARNING(f'DRY RUN: no changes made.\n'))
                        continue
                    else:
                        self.stdout.write('')
                    
                    parent_tag.save()
                    # Change was made, so update the tag hierarchy
                    tag_hierachy = get_tag_hierarchy(user=user)

        self.stdout.write(self.style.SUCCESS('Successfully imported CSV file'))