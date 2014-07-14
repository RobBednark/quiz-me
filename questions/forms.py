from django import forms

from pagedown.widgets import PagedownWidget


class FormAttempt(forms.Form):
    # Note that the question is read-only. It only displays the question, so therefore,
    # it is not a form field.
    attempt  = forms.CharField(label="A", required=False, widget=PagedownWidget())
    hidden_question_id = forms.IntegerField(widget=forms.HiddenInput())
