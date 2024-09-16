import pytest
from django.utils import timezone
from questions.forms import QUERY_UNSEEN
from questions.models import Question, Tag, QuestionTag, Schedule
from questions.get_next_question import NextQuestion, TagNotOwnedByUserError, TagDoesNotExistError
from emailusername.models import User

# Use the Django database for all the tests
pytestmark = pytest.mark.django_db

@pytest.fixture
def user():
    return User.objects.create(email="testuser@example.com")

@pytest.fixture(autouse=True)
def tag(user):
    return Tag.objects.create(name="tag 1", user=user)

@pytest.fixture
def question(user):
    return Question.objects.create(question="Test question", user=user)

def test_next_question_initialization(user, tag):
    next_question = NextQuestion(query_name=QUERY_UNSEEN, tag_ids_selected=[tag.id], user=user)
    assert next_question._query_name == QUERY_UNSEEN
    assert next_question._tag_ids_selected == [tag.id]
    assert next_question._user == user

def test_next_question_tag_not_owned_by_user(user):
    other_user = User.objects.create(email="otheruser@example.com")
    other_tag = Tag.objects.create(name="other_tag", user=other_user)
    
    with pytest.raises(TagNotOwnedByUserError) as exc_info:
        NextQuestion(query_name=QUERY_UNSEEN, tag_ids_selected=[other_tag.id], user=user)
    assert str(exc_info.value) == f"The following tags are not owned by the user: {other_tag.id}"

def test_next_question_tag_does_not_exist(user):
    non_existent_tag_id = 9999
    
    with pytest.raises(TagDoesNotExistError) as exc_info:
        NextQuestion(query_name=QUERY_UNSEEN, tag_ids_selected=[non_existent_tag_id], user=user)
    assert str(exc_info.value) == f"The following tag IDs do not exist: [{non_existent_tag_id}]"

def test_get_next_question_unseen(user, tag, question):
    QuestionTag.objects.create(question=question, tag=tag, enabled=True)
    
    next_question = NextQuestion(query_name=QUERY_UNSEEN, tag_ids_selected=[tag.id], user=user)

    assert next_question.count_questions_before_now == 0
    assert next_question.count_questions_tagged == 1
    assert next_question.question == question
    assert next_question.tag_names_selected == [tag.name]
    assert next_question.tag_names_for_question == [tag.name]

def test_get_next_question_unseen_with_schedule(user, tag, question):
    QuestionTag.objects.create(question=question, tag=tag, enabled=True)
    Schedule.objects.create(user=user, question=question, date_show_next=timezone.now() + timezone.timedelta(days=1))
    
    next_question = NextQuestion(query_name=QUERY_UNSEEN, tag_ids_selected=[tag.id], user=user)
    assert next_question.question is None
    assert next_question.count_questions_before_now == 0
    assert next_question.count_questions_tagged == 1
    assert next_question.tag_names_selected == [tag.name]
    assert next_question.tag_names_for_question == []

def test_get_count_questions_before_now(user, tag, question):
    QuestionTag.objects.create(question=question, tag=tag, enabled=True)
    Schedule.objects.create(user=user, question=question, date_show_next=timezone.now() - timezone.timedelta(hours=1))
    
    next_question = NextQuestion(query_name=QUERY_UNSEEN, tag_ids_selected=[tag.id], user=user)
    next_question._get_count_questions_before_now()
    assert next_question.count_questions_before_now == 1
    assert next_question.count_questions_tagged == 1
    assert next_question.question is None
    assert next_question.tag_names_selected == [tag.name]
    assert next_question.tag_names_for_question == []

def test_invalid_query_name(user, tag):
    with pytest.raises(ValueError) as exc_info:
        NextQuestion(query_name="invalid", tag_ids_selected=[tag.id], user=user)
    assert str(exc_info.value) == "Invalid query_name: [invalid]"

def test_get_count_recent_schedules(question, tag, user):
    # Create schedules within the last 30 minutes
    for _ in range(3):
        schedule = Schedule.objects.create(
            user=user,
            question=question,
        )
        schedule.datetime_added = timezone.now() - timezone.timedelta(minutes=15)
        schedule.save()
    
    # Create schedules within the last 60 minutes but not in the last 30
    for _ in range(2):
        schedule = Schedule.objects.create(
            user=user,
            question=question,
        )
        schedule.datetime_added = timezone.now() - timezone.timedelta(minutes=45)
        schedule.save()
    
    # Create a schedule outside the 60-minute window
    schedule = Schedule.objects.create(
        user=user,
        question=question,
        datetime_added=timezone.now() - timezone.timedelta(hours=2)
    )
    schedule.datetime_added = timezone.now() - timezone.timedelta(minutes=75)
    schedule.save()
    
    next_question = NextQuestion(query_name=QUERY_UNSEEN, tag_ids_selected=[tag.id], user=user)
    
    assert next_question.count_recent_seen_mins_30 == 3
    assert next_question.count_recent_seen_mins_60 == 5

def test_get_count_recent_schedules_empty(user):
    next_question = NextQuestion(query_name=QUERY_UNSEEN, tag_ids_selected=[], user=user)
    
    assert next_question.count_recent_seen_mins_30 == 0
    assert next_question.count_recent_seen_mins_60 == 0

def test_get_count_recent_schedules_multiple_users(user, question):
    # Create schedules for the current user
    for _ in range(2):
        Schedule.objects.create(
            user=user,
            question=question,
            datetime_added=timezone.now() - timezone.timedelta(minutes=15)
        )
    
    # Create schedules for another user
    other_user = User.objects.create(email="otheruser@example.com")
    for _ in range(3):
        Schedule.objects.create(
            user=other_user,
            question=question,
            datetime_added=timezone.now() - timezone.timedelta(minutes=15)
        )
    
    next_question = NextQuestion(query_name=QUERY_UNSEEN, tag_ids_selected=[], user=user)
    assert next_question.count_recent_seen_mins_30 == 2
    assert next_question.count_recent_seen_mins_60 == 2