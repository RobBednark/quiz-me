from django import forms
from django.forms import ModelForm
from questions.models import CHOICES_UNITS, Schedule

from pagedown.widgets import PagedownWidget

class PagedownWidgetAligned(PagedownWidget):
    class Media:
        css = {
                # use css that keeps it from overlapping tags
                'all': ('pagedown/custom.css',)
              }


class FormAttemptNew(forms.Form):
    attempt = forms.CharField(
        label="A",
        required=False,
        widget=PagedownWidgetAligned()
    )
    hidden_question_id = forms.IntegerField(widget=forms.HiddenInput())


class FormSchedule(forms.Form):
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
    interval_unit = forms.ChoiceField(choices=CHOICES_UNITS)

class FormFlashcard(forms.Form):
    attempt = forms.CharField(
        label="A",
        required=False,
        widget=PagedownWidgetAligned()
    )
    hidden_question_id = forms.IntegerField(widget=forms.HiddenInput())

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
    interval_unit = forms.ChoiceField(choices=CHOICES_UNITS)

