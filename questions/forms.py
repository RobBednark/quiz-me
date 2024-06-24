from django import forms
from questions.models import CHOICES_UNITS, QueryPreferences

from pagedown.widgets import PagedownWidget

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
    hidden_query_prefs_id = forms.IntegerField(widget=forms.HiddenInput())
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

    # query_prefs is a ModelChoiceField / dropdown for QueryPrefs, where each value shown is a QueryPrefs.name
    ## query_prefs = forms.ModelChoiceField(
    ##     required=True,
    ##     label="Query Preferences",
    ##     queryset=QueryPreferences.objects.all().order_by('-date_last_used'),
    ## )
class FormSelectTags(forms.Form):
    # query_prefs is a ModelChoiceField / dropdown for QueryPrefs, where each value shown is a QueryPrefs.name
    query_prefs = forms.ModelChoiceField(
        required=True,
        label="Query Preferences",
        queryset=QueryPreferences.objects.all().order_by('-date_last_used'),
    )