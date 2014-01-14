from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView

from .forms import FormAttempt
from .models import Attempt, Question

def get_next_question():
    question = Question.objects.all()[0].question
    return question

def view_quiz(request):
    if request.method == 'GET':
        # This is a GET, 
        if request.GET.get('question'):
            # question is in the query parameters
            question = Question.objects.all()[0].question
        else:
            question = Question.objects.all()[0].question
        form_attempt = FormAttempt()

        return render(request=request, template_name='quiz.html', 
                      dictionary=dict(form_attempt=form_attempt, question=question, question_id=question.id))
    elif request.method == 'POST':
        # ASSERT: this is a POST, so the user answered a question
        form_attempt = FormAttempt(request.POST)
        if form_attempt.is_valid():
            # TODO: need to capture question id and use it here.
            attempt = Attempt(text=form_attempt.cleaned_data['text'],
                              question=Question.objects.all()[0],
                              correct=True)
            try:
                attempt.save()
            except Exception as exception:
                pass
            return HttpResponseRedirect('/?question=%s' % 0)
    else:
        raise Exception("Unkown request.method=[%s]" % request.method)
