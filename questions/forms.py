from django import forms
from django.forms import ModelForm
from .models import Schedule

from pagedown.widgets import PagedownWidget

class FormAttempt(forms.Form):
    # Note that the question is read-only. It only displays the question, so therefore,
    # it is not a form field.
    # TODO: if we include the question_id in the url, can we remove this form and just use a ModelForm for an Attempt?  Or do we need this because we are overriding the widget for "attempt"?   -Rob Bednark 12/21/14
    attempt  = forms.CharField(label="A", required=False, widget=PagedownWidget())
    hidden_question_id = forms.IntegerField(widget=forms.HiddenInput())

class ModelFormSchedule(ModelForm):
    class Meta:
        model = Schedule

