from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Max, Min
from django.forms.models import modelformset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView

from .forms import FormAttempt
from .models import Attempt, Question, QuestionTag, Tag, User, UserTag

def next_question(user):
    ''' Find and return the next question for the currently logged-in user.
    '''
    '''
    TODO:
        Query for all questions that contain at least one of the UserTags
        Input:
            UserTags with enabled=True
        Output:
            questions that have one or more QuestionTag's 
            WHERE 
                QuestionTag.enabled=True
            AND
                QuestionTag.

    '''

    # Find all the tags that the user has selected
    user_tags = UserTag.objects.filter(user=user, enabled=True)
    # Find all the questions associated with selected tags
    question_tags = QuestionTag.objects.filter(enabled=True, tag__in=user_tags).select_related('question')
    # Find the newest attempt for each question.
    # If a question doesn't have any attempts, then the newest attempt will be None.
    #question_tags = question_tags.annotate(newest_attempt=Max('question__attempt_set__datetime_added'))
    question_tags = question_tags.annotate(attempt_newest=Max('question__attempt__datetime_added'))
    # Find the oldest attempt of all the newest attempts
    # Note that None (no attempt) for a question should count as the older than a question with an
    # attempt date.
    question_tags = question_tags.order_by('-attempt_newest')
    question = question_tags[0].question if question_tags else None
    return question


    #questions = Question.objects.filter(id__in=[qtag.question for qtag in question_tags])
    #questions = questions.annotate()
    # questions = Question.objects.filter(question__in=question_tags)
    # Select all questions with QuestionTag's that the user has enabled=True
    # Of those questions, get the question with the oldest attempt datetime_added
    # If a question has no attempts, consider that the oldest.
    # Find the oldest_attempt for each question.
    # Get the Min(oldest_attempt)
    # Need to use aggregation and either Max() or Min() function


    ### Previous code, which is being replaced by code above:
    try:
        last_attempt = Attempt.objects.filter(user=user).latest(field_name='datetime_added')
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




def _create_and_get_usertags(request):
    ModelFormset_UserTag = modelformset_factory(model=UserTag,
                                                extra=0,
                                                fields=('enabled',))
    user = request.user
    if request.method == 'GET':
        # Get the user, find all the tags, and create a form for each tag.
        #        GET:
        #            For each of the tags, show a checkbox.
        #            If there is no UserTag for that tag, then show the tag and default to False.

        # Get all the Tag's
        tags = Tag.objects.all()

        # Get all the UserTag's associated with this user
        qs_user_tags = UserTag.objects.filter(user=user)
        user_tags_by_tagname = { user_tag.tag.name : user_tag for user_tag in qs_user_tags }

        # Create UserTag's for any new tags
        for tag in tags:
            if not tag.name in user_tags_by_tagname:
                # There isn't a tag, so create one
                UserTag(user=user, tag=tag, enabled=False).save()

        modelformset_usertag = ModelFormset_UserTag(queryset=UserTag.objects.filter(user=user))
        for form in modelformset_usertag.forms:
            form.fields['enabled'].label = form.instance.tag.name

        return modelformset_usertag
    elif request.method == 'POST':
        modelformset_usertag = ModelFormset_UserTag(queryset=UserTag.objects.filter(user=user), data=request.POST)
        for form in modelformset_usertag.forms:
            form.fields['enabled'].label = form.instance.tag.name

        if modelformset_usertag.is_valid(): # All validation rules pass
            modelformset_usertag.save()
        else:
            # ASSERT: modelformset_usertag.is_valid() was called, so modelformset_usertag modified itself to contain
            # any errors, and these errors will be displayed in the form using the form.as_p
            # attribute.
            #  It puts the errors in form._errors and form.errors, 
            #   e.g., form.errors['sender'] == 'Enter a valid email address.'
            pass
        return modelformset_usertag




@login_required(login_url='/login')
def view_quiz(request):
    modelformset_usertag = _create_and_get_usertags(request=request)

    if request.method == 'GET':
        # For a GET, show the next question
        question = next_question(user=request.user)
        form_attempt = FormAttempt()
        if question:
            form_attempt.fields['hidden_question_id'].initial = question.id
        else:
            form_attempt.fields['hidden_question_id'].initial = None
        return render(request=request, 
                      template_name='show_question.html', 
                      dictionary=dict(form_attempt=form_attempt, 
                                      modelformset_usertag=modelformset_usertag,
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
                              user=request.user)
            try:
                attempt.save()
            except Exception as exception:
                pass
            # Show a page that shows their attempt, the correct answer, the question, and a NEXT button
            return render(request=request, 
                          template_name='show_question_and_answer.html', 
                          dictionary=dict(form_attempt=form_attempt, 
                                          modelformset_usertag=modelformset_usertag,
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
        raise Exception("Unknown request.method=[%s]" % request.method)
