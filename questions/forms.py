from django import forms

class FormAttempt(forms.Form):
    # The question is just for displaying the question.  There should not be any input.
    #question = forms.CharField(label="Question")
    #answer   = forms.CharField(label="Answer", required=False)
    attempt  = forms.CharField(label="A", required=False, widget=forms.Textarea())
    hidden_question_id = forms.IntegerField(widget=forms.HiddenInput())
