from django import forms
from django.forms import ModelForm
from .models import CHOICES_UNITS, Attempt, Schedule

from pagedown.widgets import PagedownWidget

class FormAttempt(forms.Form):
    # Note that the question is read-only. It only displays the question, so therefore,
    # it is not a form field.
    # TODO: if we include the question_id in the url, can we remove this form and just use a ModelForm for an Attempt?  Or do we need this because we are overriding the widget for "attempt"?   -Rob Bednark 12/21/14  A: The Attempt model also has question, user, datetime_added, ..., which are all fields that we don't want to display.  So don't bother using a ModelForm.
    attempt  = forms.CharField(label="A", required=False, widget=PagedownWidget())
    hidden_question_id = forms.IntegerField(widget=forms.HiddenInput())

class FormAttemptNew(forms.Form):
    attempt  = forms.CharField(label="A", required=False, widget=PagedownWidget())

class ModelFormSchedule(ModelForm):
    class Meta:
        model = Schedule
        fields = ('date_show_next', 'interval_num', 'interval_unit')

class FormSchedule(forms.Form):
    interval_num = forms.DecimalField(max_digits=5, decimal_places=2)
    interval_unit = forms.ChoiceField(choices=CHOICES_UNITS)
