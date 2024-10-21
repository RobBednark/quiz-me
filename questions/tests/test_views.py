import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model

from questions.models import Question, Tag, Attempt, Schedule
from questions.forms import FormFlashcard, FormSelectTags, QUERY_UNSEEN
from questions.TagList import FIELD_NAME__TAG_ID_PREFIX

HTTP_STATUS_301_MOVED_PERMANENTLY = 301

@pytest.fixture
def user(db):
    User = get_user_model()
    return User.objects.create_user(email='testuser@example.com', password='12345')


@pytest.fixture
def authenticated_client(client, user):
    client.force_login(user=user)
    return client

@pytest.fixture
def tag(db, user):
    return Tag.objects.create(name='TestTag', user=user)

@pytest.fixture
def question(db, user, tag):
    question = Question.objects.create(question='Test Question', user=user)
    return question

def test_view_select_tags_get(authenticated_client):
    response = authenticated_client.get(reverse('select_tags'))
    assert response.status_code == 200
    assert 'select_tags.html' in [t.name for t in response.templates]
    assert isinstance(response.context['form_select_tags'], FormSelectTags)

def test_view_select_tags_post(authenticated_client, tag):
    QUERY_NAME = QUERY_UNSEEN
    FIELD_NAME = f'{FIELD_NAME__TAG_ID_PREFIX}{tag.id}'
    data = {
        'query_name': QUERY_NAME,
        FIELD_NAME: tag.name
    }
    response = authenticated_client.post(reverse('select_tags'), data)
    assert response.status_code == HTTP_STATUS_301_MOVED_PERMANENTLY
    assert response.url == f"{reverse('question')}?query_name={QUERY_NAME}&tag_ids_selected={tag.id}"

def test_view_question_get(authenticated_client, tag):
    response = authenticated_client.get(reverse('question'), {'tag_ids_selected': str(tag.id), 'query_name': QUERY_UNSEEN})
    assert response.status_code == 200
    assert 'question.html' in [t.name for t in response.templates]
    assert isinstance(response.context['form_flashcard'], FormFlashcard)

def test_view_flashcard_post(authenticated_client, question, tag):
    data = {
        'hidden_question_id': question.id,
        'hidden_query_name': QUERY_UNSEEN,
        'hidden_tag_ids_selected': str(tag.id),
        'attempt': 'Test Attempt',
        'percent_correct': 80,
        'percent_importance': 70,
        'interval_num': 1,
        'interval_unit': 'days'
    }
    response = authenticated_client.post(reverse('question'), data)
    assert response.status_code == HTTP_STATUS_301_MOVED_PERMANENTLY
    assert Attempt.objects.filter(question=question, user=question.user).exists()
    assert Schedule.objects.filter(question=question, user=question.user).exists()