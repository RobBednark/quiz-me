import pytest
from django.utils import timezone
from questions.forms import QUERY_DUE, QUERY_UNSEEN
from questions.models import Question, Tag, QuestionTag, Schedule
from questions.get_next_question import NextQuestion
from emailusername.models import User

# Use the Django database for all the tests
pytestmark = pytest.mark.django_db

TAG_NAME = "tag 1"
@pytest.fixture
def user():
    return User.objects.create(email="testuser@example.com")

@pytest.fixture(autouse=True)
def tag(user):
    return Tag.objects.create(name=TAG_NAME, user=user)

@pytest.fixture
def question(user):
    return Question.objects.create(question="Test question", user=user)

class TestInit:
    def test_next_question_initialization(self, user, tag):
        next_question = NextQuestion(query_name=QUERY_UNSEEN, tag_ids_selected=[tag.id], user=user)
        assert next_question._query_name == QUERY_UNSEEN
        assert next_question._tag_ids_selected == [tag.id]
        assert next_question._user == user

    def test_next_question_tag_not_owned_by_user(self, user):
        other_user = User.objects.create(email="otheruser@example.com")
        other_tag = Tag.objects.create(name="other_tag", user=other_user)
        
        with pytest.raises(ValueError) as exc_info:
            NextQuestion(query_name=QUERY_UNSEEN, tag_ids_selected=[other_tag.id], user=user)
        assert str(exc_info.value) == f"Tag ids are not owned by user: [{other_tag.id}]."

    def test_next_question_tag_does_not_exist(self, user):
        non_existent_tag_id = 9999
        
        with pytest.raises(ValueError) as exc_info:
            NextQuestion(query_name=QUERY_UNSEEN, tag_ids_selected=[non_existent_tag_id], user=user)
        assert str(exc_info.value) == f"Tag ids do not exist: [{non_existent_tag_id}]."

class Test__QUERY_UNSEEN:
    def test_get_next_question_unseen(self, user, tag, question):
        QuestionTag.objects.create(question=question, tag=tag, enabled=True)
        
        next_question = NextQuestion(query_name=QUERY_UNSEEN, tag_ids_selected=[tag.id], user=user)

        assert next_question.count_questions_before_now == 0
        assert next_question.count_questions_tagged == 1
        assert next_question.count_times_question_seen == 0
        assert next_question.question == question
        assert next_question.tag_names_selected == [tag.name]
        assert next_question.tag_names_for_question == [tag.name]

    def test_get_next_question_unseen_with_schedule(self, user, tag, question):
        QuestionTag.objects.create(question=question, tag=tag, enabled=True)
        Schedule.objects.create(user=user, question=question, date_show_next=timezone.now() + timezone.timedelta(days=1))
        
        next_question = NextQuestion(query_name=QUERY_UNSEEN, tag_ids_selected=[tag.id], user=user)
        assert next_question.question is None
        assert next_question.count_questions_before_now == 0
        assert next_question.count_questions_tagged == 1
        assert next_question.count_times_question_seen == 0
        assert next_question.tag_names_selected == [tag.name]
        assert next_question.tag_names_for_question == []

def test_get_count_questions_before_now(user, tag, question):
    QuestionTag.objects.create(question=question, tag=tag, enabled=True)
    Schedule.objects.create(user=user, question=question, date_show_next=timezone.now() - timezone.timedelta(hours=1))
    
    next_question = NextQuestion(query_name=QUERY_UNSEEN, tag_ids_selected=[tag.id], user=user)
    next_question._get_count_questions_before_now()
    assert next_question.count_questions_before_now == 1
    assert next_question.count_questions_tagged == 1
    assert next_question.count_times_question_seen == 0
    assert next_question.question is None
    assert next_question.tag_names_for_question == []
    assert next_question.tag_names_selected == [tag.name]

def test_invalid_query_name(user, tag):
    with pytest.raises(ValueError) as exc_info:
        NextQuestion(query_name="invalid", tag_ids_selected=[tag.id], user=user)
    assert str(exc_info.value) == "Invalid query_name: [invalid]"

class TestCountRecentSchedules:
    def test_get_count_recent_schedules(self, question, tag, user):
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

    def test_get_count_recent_schedules_empty(self, user):
        next_question = NextQuestion(query_name=QUERY_UNSEEN, tag_ids_selected=[], user=user)
        
        assert next_question.count_recent_seen_mins_30 == 0
        assert next_question.count_recent_seen_mins_60 == 0
        assert next_question.count_times_question_seen == 0

    def test_get_count_recent_schedules_multiple_users(self, user, question):
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
        assert next_question.question is None
        assert next_question.count_recent_seen_mins_30 == 2
        assert next_question.count_recent_seen_mins_60 == 2

def test_get_next_question_due_one_question(user, tag, question):
    QuestionTag.objects.create(question=question, tag=tag, enabled=True)
    Schedule.objects.create(user=user, question=question, date_show_next=timezone.now() - timezone.timedelta(hours=1))
    
    next_question = NextQuestion(query_name=QUERY_DUE, tag_ids_selected=[tag.id], user=user)
    
    assert next_question.question == question
    assert next_question.count_questions_tagged == 1
    assert next_question.tag_names_for_question == [tag.name]
    assert next_question.tag_names_selected == [tag.name]

class Test__QUERY_DUE:
    def test_get_next_question_due_multiple_questions(self, user, tag):
        question1 = Question.objects.create(question="Question 1 : -3h", user=user)
        question2 = Question.objects.create(question="Question 2 : -1h", user=user)
        question3 = Question.objects.create(question="Question 3 : -2h", user=user)
        
        QuestionTag.objects.create(question=question1, tag=tag, enabled=True)
        QuestionTag.objects.create(question=question2, tag=tag, enabled=True)
        QuestionTag.objects.create(question=question3, tag=tag, enabled=True)
        
        Schedule.objects.create(user=user, question=question1, date_show_next=timezone.now() - timezone.timedelta(hours=2))
        Schedule.objects.create(user=user, question=question2, date_show_next=timezone.now() - timezone.timedelta(hours=1))
        Schedule.objects.create(user=user, question=question3, date_show_next=timezone.now() - timezone.timedelta(hours=3))
        
        next_question = NextQuestion(query_name=QUERY_DUE, tag_ids_selected=[tag.id], user=user)
        
        assert next_question.question == question3
        assert next_question.count_questions_tagged == 3
        assert next_question.tag_names_for_question == [tag.name]
        assert next_question.tag_names_selected == [tag.name]

    def test_get_next_question_due_no_due_questions(self, user, tag, question):
        QuestionTag.objects.create(question=question, tag=tag, enabled=True)
        # date_show_next is in the future
        Schedule.objects.create(user=user, question=question, date_show_next=timezone.now() + timezone.timedelta(hours=1))
        
        next_question = NextQuestion(query_name=QUERY_DUE, tag_ids_selected=[tag.id], user=user)
        
        assert next_question.question is None
        assert next_question.count_questions_tagged == 1
        assert next_question.tag_names_for_question == []
        assert next_question.tag_names_selected == [tag.name]

    def test_get_next_question_due_multiple_tags(self, user):
        tag1 = Tag.objects.create(name="tag 1", user=user)
        tag2 = Tag.objects.create(name="tag 2", user=user)
        question1 = Question.objects.create(question="Question 1 - tag 1, -1h", user=user)
        question2 = Question.objects.create(question="Question 2 - tag 2, -2h, EXPECTED", user=user)
        
        QuestionTag.objects.create(question=question1, tag=tag1, enabled=True)
        QuestionTag.objects.create(question=question2, tag=tag2, enabled=True)
        
        Schedule.objects.create(user=user, question=question1, date_show_next=timezone.now() - timezone.timedelta(hours=1))
        Schedule.objects.create(user=user, question=question2, date_show_next=timezone.now() - timezone.timedelta(hours=2))
        
        next_question = NextQuestion(query_name=QUERY_DUE, tag_ids_selected=[tag1.id, tag2.id], user=user)
        
        assert next_question.question == question2
        assert next_question.count_questions_tagged == 2
        assert next_question.tag_names_for_question == [tag2.name]
        assert next_question.tag_names_selected == [tag1.name, tag2.name]
    
    class TestAllQueryTypesSameData:

        def test_different_results_for_query_seen_and_due(self, user, tag):
            # Create the following test data:
            #
            # | Que | U  | Tags   | Schedules | added |
            # |-----|----|--------|-----------|-------|
            # | q1  | u1 | t1     | None      | -2d   |
            # | q2  | u1 | t1,t2  | -1d       | -3d   |
            # | q3  | u1 | t2     | -1d       | -1d   |
            # | q4  | u1 | t3     | -1d       | -1d   |
            # | -   | u1 | t4     |           |       |
            # | q5  | u2 | t5     | None      | -1d   |
            # | q6  | u1 | t1     | None      | -4d   |
            #
            # Notes:
            # Que = Question
            # U = User who created the question (i.e., Question.user field)
            # Tags = tags that are applied to the question via the QuestionTag model
            # Schedules = schedules associated with the question via the Schedule.question foreign key; the column value refers to the Schedule.date_show_next field; e.g., -1d = 1 day before now
            # added = when the question was added (relative to now); i.e., Question.datetime_added field; e.g., -2d = 2 days before now

            # Create questions
            question_not_due = Question.objects.create(question="Question 1: not due", user=user)
            question_due = Question.objects.create(question="Question 2: due", user=user)
            question_unseen = Question.objects.create(question="Question 3: unseen", user=user)
        
            # Create QuestionTags
            QuestionTag.objects.create(question=question_not_due, tag=tag, enabled=True)
            QuestionTag.objects.create(question=question_due, tag=tag, enabled=True)
            QuestionTag.objects.create(question=question_unseen, tag=tag, enabled=True)
        
            # Create Schedules
            sched_future = Schedule.objects.create(
                user=user,
                question=question_not_due,
                date_show_next=timezone.now() + timezone.timedelta(minutes=20), # future
            )
            sched_future.datetime_added = timezone.now() - timezone.timedelta(minutes=20)
            sched_future.save()
            sched_past = Schedule.objects.create(
                user=user,
                question=question_due,
                date_show_next=timezone.now() - timezone.timedelta(minutes=20), # past
                datetime_added=timezone.now() - timezone.timedelta(minutes=40)
            )
            sched_past.datetime_added = timezone.now() - timezone.timedelta(minutes=40)
            sched_past.save()
            # question_unseen: no schedule
        
            # Test QUERY_UNSEEN
            next_question_unseen = NextQuestion(query_name=QUERY_UNSEEN, tag_ids_selected=[tag.id], user=user)
            assert next_question_unseen.question == question_unseen
            assert next_question_unseen.count_times_question_seen == 0
            assert next_question_unseen.count_questions_before_now == 1
            assert next_question_unseen.count_questions_matching == 1
            assert next_question_unseen.count_questions_tagged == 3
            assert next_question_unseen.count_recent_seen_mins_30 == 1
            assert next_question_unseen.count_recent_seen_mins_60 == 2
            assert next_question_unseen.tag_names_for_question == [TAG_NAME]
            assert next_question_unseen.tag_names_selected == [TAG_NAME]

        
            # Test QUERY_DUE
            next_question_due = NextQuestion(query_name=QUERY_DUE, tag_ids_selected=[tag.id], user=user)
            assert next_question_due.question == question_due
            assert next_question_unseen.count_times_question_seen == 2
            assert next_question_unseen.count_questions_before_now == 1
            assert next_question_unseen.count_questions_matching == 1
            assert next_question_unseen.count_questions_tagged == 3
            assert next_question_unseen.count_recent_seen_mins_30 == 1
            assert next_question_unseen.count_recent_seen_mins_60 == 2
            assert next_question_unseen.tag_names_for_question == [TAG_NAME]
            assert next_question_unseen.tag_names_selected == [TAG_NAME]
        
            # Verify different results
            assert next_question_unseen != next_question_due
        