from django import forms
from questions.models import CHOICES_UNITS

from pagedown.widgets import PagedownWidget

QUERY_UNSEEN = 'UNSEEN'
QUERY_REINFORCE = 'REINFORCE'
QUERY_OLDEST_DUE = 'OLDEST DUE'
QUERY_FUTURE = 'FUTURE'
QUERY_ANSWERED_COUNT = 'ANSWERED COUNT'
QUERY_LAST_SEEN_BY_TAG = 'LAST-SEEN BY TAG'
QUERY_OLDEST_DUE_OR_UNSEEN= 'OLDEST DUE OR UNSEEN'
QUERY_OLDEST_DUE_OR_UNSEEN_BY_TAG = 'OLDEST DUE OR UNSEEN BY TAG'
QUERY_UNSEEN_BY_OLDEST_VIEWED_TAG = 'UNSEEN BY OLDEST-VIEWED TAG'
QUERY_REINFORCE_THEN_UNSEEN = 'REINFORCE, UNSEEN'
QUERY_REINFORCE_THEN_UNSEEN_THEN_FUTURE = 'REINFORCE, UNSEEN, FUTURE'
QUERY_UNSEEN_THEN_OLDEST_DUE = 'UNSEEN, OLDEST DUE'
QUERY_UNSEEN_THEN_OLDEST_DUE_THEN_FUTURE = 'UNSEEN, OLDEST DUE, FUTURE'

QUERY_CHOICES = (
    (QUERY_UNSEEN, f'{QUERY_UNSEEN}: ordered by date created ascending'),
    (QUERY_REINFORCE, f'{QUERY_REINFORCE}: notes due before now, ordered by date seen descending'),
    (QUERY_OLDEST_DUE, f'{QUERY_OLDEST_DUE}: notes due before now, ordered by due date ascending'),
    (QUERY_FUTURE, f'{QUERY_FUTURE}: notes due after now, ordered by due date ascending'),
    # (QUERY_ANSWERED_COUNT, f'{QUERY_ANSWERED_COUNT}: ordered by # times seen, ascending (NOTE: this will see all notes)'),
    # (QUERY_LAST_SEEN_BY_TAG, f'{QUERY_LAST_SEEN_BY_TAG}: find the oldest last_seen date for each tag; show note from the oldest tag (tags with notes but no schedules should be shown first)'),
    (QUERY_OLDEST_DUE_OR_UNSEEN, f'{QUERY_OLDEST_DUE_OR_UNSEEN}: for each question, Schedule.date_show_next, or if no Schedules, then Question.datetime_added'),
    # (QUERY_OLDEST_DUE_OR_UNSEEN_BY_TAG, f'{QUERY_OLDEST_DUE_OR_UNSEEN_BY_TAG}: For each question, look at Schedule.datetime_added, or if no Schedules (unseen), then the Question.datetime_added.'),
    (QUERY_UNSEEN_BY_OLDEST_VIEWED_TAG, f'{QUERY_UNSEEN_BY_OLDEST_VIEWED_TAG}: "oldest-viewed tag" is the tag with the oldest Schedule.datetime_added.  Or, if no Schedules, then the oldest Question.datetime_added.'),
    # (QUERY_REINFORCE_THEN_UNSEEN, f'{QUERY_REINFORCE_THEN_UNSEEN}: REINFORCE, then UNSEEN'),
    # (QUERY_REINFORCE_THEN_UNSEEN_THEN_FUTURE, f'{QUERY_REINFORCE_THEN_UNSEEN_THEN_FUTURE}: REINFORCE, then UNSEEN, then FUTURE'),
    (QUERY_UNSEEN_THEN_OLDEST_DUE, f'{QUERY_UNSEEN_THEN_OLDEST_DUE}: UNSEEN, then DUE'),
    # (QUERY_UNSEEN_THEN_OLDEST_DUE_THEN_FUTURE, f'{QUERY_UNSEEN_THEN_OLDEST_DUE_THEN_FUTURE}: UNSEEN, then DUE, then FUTURE'),
)

ALL_QUERY_NAMES = (
    QUERY_UNSEEN,
    QUERY_REINFORCE,
    QUERY_OLDEST_DUE,
    QUERY_FUTURE,
    QUERY_ANSWERED_COUNT,
    QUERY_LAST_SEEN_BY_TAG,
    QUERY_OLDEST_DUE_OR_UNSEEN,
    QUERY_OLDEST_DUE_OR_UNSEEN_BY_TAG,
    QUERY_UNSEEN_BY_OLDEST_VIEWED_TAG,
    QUERY_REINFORCE_THEN_UNSEEN,
    QUERY_REINFORCE_THEN_UNSEEN_THEN_FUTURE,
    QUERY_UNSEEN_THEN_OLDEST_DUE,
    QUERY_UNSEEN_THEN_OLDEST_DUE_THEN_FUTURE
)

class PagedownWidgetAligned(PagedownWidget):
    class Media:
        css = {
                # use css that keeps it from overlapping tags
                'all': ('pagedown/custom.css',)
              }

class FormFlashcard(forms.Form):
    attempt = forms.CharField(
        label="A",
        required=False,
        widget=PagedownWidgetAligned()
    )
    hidden_query_name = forms.CharField(widget=forms.HiddenInput())
    hidden_question_id = forms.IntegerField(widget=forms.HiddenInput())
    hidden_tag_ids_selected = forms.CharField(widget=forms.HiddenInput())

    percent_correct = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False
    )
    percent_importance = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False
    )
    interval_num = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False
    )
    interval_unit = forms.ChoiceField(
        choices=CHOICES_UNITS,
        required=False)

class FormSelectTags(forms.Form):
    query_name = forms.ChoiceField(
        choices=QUERY_CHOICES,
        required=True
    )