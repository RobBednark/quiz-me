# -*- coding: utf-8 -*-
import sys
from django.core.management.base import NoArgsCommand


class Command(NoArgsCommand):
    help = "run this script"
    stdin = sys.stdin

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            '--commit',
            action='store_true',
            dest='commit',
            default=False,
            help='Commit the data instead of just doing a dry-run.',
        )

    def handle_noargs(self, **options):
        # read the entire file

        # split by "^\S*Q:\*S$" (case-insensitive)

        # grab the tags if there are any
        # '^\S*TAGS:\s' (case-insensitive)
        # remove the TAGS: line from the string

        # query for each tag, and create each tag that doesn't already exist

        # split the question and answer on '^\S*A:\S*'

        stdin = options.get('stdin', sys.stdin)
        stdin.read()


        # if --commit, then commit the data, else just show what would be done (a dry-run)
        if options['commit']:
            pass
        else:
            self.stdout.write("NOTE: --commit not present, so data is not being committed to the database.")
