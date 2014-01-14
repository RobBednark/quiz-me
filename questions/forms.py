from django import forms

class FormAttempt(forms.Form):
    text = forms.CharField()
    question_id = forms.IntegerField(hidden=True)
