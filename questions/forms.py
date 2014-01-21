from django import forms

class FormAttempt(forms.Form):
    text = forms.CharField()
    # Note that HiddenInput is a callable!
    #question_id = forms.IntegerField(widget=forms.HiddenInput)
    question_id = forms.CharField(widget=forms.HiddenInput())
