import pytest
from django.utils import timezone
from questions.forms import QUERY_UNSEEN
from questions.models import Question, Tag, QuestionTag, Schedule
from questions.get_next_question import NextQuestion, TagNotOwnedByUserError, TagDoesNotExistError
from emailusername.models import User

pytestmark = pytest.mark.django_db

@pytest.fixture
def user():
    return User.objects.create(email="testuser@example.com")

@pytest.fixture
def tag(user):
    return Tag.objects.create(name="tag 1", user=user)

@pytest.fixture
def question(user):
    return Question.objects.create(question="Test question", user=user)

@pytest.mark.django_db
def test_next_question_initialization(user, tag):
    next_question = NextQuestion(query_name=QUERY_UNSEEN, tag_ids_selected=[tag.id], user=user)
    assert next_question._query_name == QUERY_UNSEEN
    assert next_question._tag_ids_selected == [tag.id]
    assert next_question._user == user

def test_next_question_tag_not_owned_by_user(user):
    other_user = User.objects.create(email="otheruser@example.com")
    other_tag = Tag.objects.create(name="other_tag", user=other_user)
    
    with pytest.raises(TagNotOwnedByUserError):
        NextQuestion(query_name=QUERY_UNSEEN, tag_ids_selected=[other_tag.id], user=user)

def test_next_question_tag_does_not_exist(user):
    non_existent_tag_id = 9999
    
    with pytest.raises(TagDoesNotExistError):
        NextQuestion(query_name=QUERY_UNSEEN, tag_ids_selected=[non_existent_tag_id], user=user)

def test_get_next_question_unseen(user, tag, question):
    QuestionTag.objects.create(question=question, tag=tag, enabled=True)
    
    next_question = NextQuestion(query_name=QUERY_UNSEEN, tag_ids_selected=[tag.id], user=user)
    assert next_question.question == question
    assert next_question.tag_names_selected == [tag.name]
    assert next_question.tag_names_for_question == [tag.name]

def test_get_next_question_unseen_with_schedule(user, tag, question):
    QuestionTag.objects.create(question=question, tag=tag, enabled=True)
    Schedule.objects.create(user=user, question=question, date_show_next=timezone.now() + timezone.timedelta(days=1))
    
    next_question = NextQuestion(query_name=QUERY_UNSEEN, tag_ids_selected=[tag.id], user=user)
    assert next_question.question is None

def test_get_count_questions_before_now(user, tag, question):
    QuestionTag.objects.create(question=question, tag=tag, enabled=True)
    Schedule.objects.create(user=user, question=question, date_show_next=timezone.now() - timezone.timedelta(hours=1))
    
    next_question = NextQuestion(query_name=QUERY_UNSEEN, tag_ids_selected=[tag.id], user=user)
    next_question._get_count_questions_before_now()
    assert next_question.count_questions_before_now == 1

def test_invalid_query_name(user, tag):
    with pytest.raises(ValueError):
        NextQuestion(query_name="invalid", tag_ids_selected=[tag.id], user=user)