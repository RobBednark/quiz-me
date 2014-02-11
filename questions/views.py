from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView

from .forms import FormAttempt
from .models import Attempt, Question, User

def next_question(request):
    ''' Find and return the next question for the currently logged-in user.
    '''
    try:
        last_attempt = Attempt.objects.filter(user=request.user).latest(field_name='datetime_added')
    except ObjectDoesNotExist:
        last_attempt = None

    if last_attempt:
        last_question = last_attempt.question
        next_question_id = last_question.id + 1
        try:
            # TODO: instead of doing a get() on the id, do a query >= last_attempt.datetime_added and get the next one in the list
            next_question = Question.objects.get(id=next_question_id)
        except ObjectDoesNotExist:
            next_question = Question.objects.earliest(field_name='datetime_added')
    else:
        # User has never answered a question
        try:
            next_question = Question.objects.earliest(field_name='datetime_added')
        except ObjectDoesNotExist:
            next_question = None
    return next_question


@login_required(login_url='/login')
def view_quiz(request):
    if request.method == 'GET':
        # For a GET, show the next question
        question = next_question(request=request)
        form_attempt = FormAttempt()
        if question:
            form_attempt.fields['hidden_question_id'].initial = question.id
        else:
            form_attempt.fields['hidden_question_id'].initial = None
        return render(request=request, 
                      template_name='show_question.html', 
                      dictionary=dict(form_attempt=form_attempt, 
                                      question=question))
    elif request.method == 'POST':
        # ASSERT: this is a POST, so the user answered a question
        # Show the correct answer, the user's attempt, and the question
        # Show a NEXT button to do a GET and get the next question
        form_attempt = FormAttempt(request.POST)
        if form_attempt.is_valid():
            question_id = form_attempt.cleaned_data['hidden_question_id']
            question = Question.objects.get(id=question_id)
            # TODO: Need to figure out which question they are answering
            attempt = Attempt(attempt=form_attempt.cleaned_data['attempt'],
                              question=question,
                              correct=True,
                              user=request.user)
            try:
                attempt.save()
            except Exception as exception:
                pass
            # Show a page that shows their attempt, the correct answer, the question, and a NEXT button
            return render(request=request, 
                          template_name='show_question_and_answer.html', 
                          dictionary=dict(form_attempt=form_attempt, 
                                          question=question,
                                          answer=question.answer,
                                          attempt=attempt,
                                         ))
        else:
            # Assert: form is NOT valid
            # Need to return the errors to the template, and have the template show the errors.
            return render(request=request, 
                          template_name='show_question.html', 
                          dictionary=dict(form_attempt=form_attempt, 
                                         ))
    else:
        raise Exception("Unkown request.method=[%s]" % request.method)
