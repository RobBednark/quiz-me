from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView

from .forms import FormAttempt
from .models import Attempt, Question

def next_question():
    user = 'None'
    last_attempt = Attempt.objects.filter(user=user).latest(field_name='datetime_added')
    last_question = last_attempt.question
    next_question_id = last_question.id + 1
    try:
        # TODO: instead of doing a get() on the id, do a query >= last_attempt.datetime_added and get the next one in the list
        next_question = Question.objects.get(id=next_question_id)
    except ObjectDoesNotExist:
        next_question = Question.objects.earliest(field_name='datetime_added')

    return next_question

def view_quiz(request):
    if request.method == 'GET':
        # This is a GET, 
        if request.GET.get('question'):
        question = next_question()
        form_attempt = FormAttempt()

        return render(request=request, template_name='quiz.html', 
                      dictionary=dict(form_attempt=form_attempt, question=question, question_id=question.id))
    elif request.method == 'POST':
        # ASSERT: this is a POST, so the user answered a question
        form_attempt = FormAttempt(request.POST)
        if form_attempt.is_valid():
            # TODO: Need to figure out which question they are answering
            attempt = Attempt(text=form_attempt.cleaned_data['text'],
                              question=???,
                              correct=True)
            try:
                attempt.save()
            except Exception as exception:
                pass
            return HttpResponseRedirect('/?question=%s' % 0)
    else:
        raise Exception("Unkown request.method=[%s]" % request.method)
