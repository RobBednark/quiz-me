import pytest
from django.utils import timezone
from questions.forms import QUERY_DUE, QUERY_FUTURE, QUERY_REINFORCE, QUERY_UNSEEN, QUERY_UNSEEN_THEN_DUE
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

# Template for assertions:
'''
        assert xx.question == ...

        assert xx.count_questions_due == 99
        assert xx.count_questions_matched_criteria == 99
        assert xx.count_questions_tagged == 99
        assert xx.count_recent_seen_mins_30 == 99
        assert xx.count_recent_seen_mins_60 == 99
        assert xx.count_times_question_seen == 99

        assert xx.tag_names_for_question == [TAG_NAME]
        assert xx.tag_names_selected == [TAG_NAME]
'''

class TestInit:
    def test_nq_initialization(self, user, tag):
        nq = NextQuestion(query_name=QUERY_UNSEEN, tag_ids_selected=[tag.id], user=user)
        assert nq._query_name == QUERY_UNSEEN
        assert nq._tag_ids_selected == [tag.id]
        assert nq._user == user

    def test_nq_tag_not_owned_by_user(self, user):
        other_user = User.objects.create(email="otheruser@example.com")
        other_tag = Tag.objects.create(name="other_tag", user=other_user)
        
        with pytest.raises(ValueError) as exc_info:
            NextQuestion(query_name=QUERY_UNSEEN, tag_ids_selected=[other_tag.id], user=user)
        assert str(exc_info.value) == f"Tag ids are not owned by user: [{other_tag.id}]."

    def test_nq_tag_does_not_exist(self, user):
        non_existent_tag_id = 9999
        
        with pytest.raises(ValueError) as exc_info:
            NextQuestion(query_name=QUERY_UNSEEN, tag_ids_selected=[non_existent_tag_id], user=user)
        assert str(exc_info.value) == f"Tag ids do not exist: [{non_existent_tag_id}]."

class Test__QUERY_UNSEEN:
    def test_get_nq_unseen(self, user, tag, question):
        QuestionTag.objects.create(question=question, tag=tag, enabled=True)
        
        nq = NextQuestion(query_name=QUERY_UNSEEN, tag_ids_selected=[tag.id], user=user)

        assert nq.question == question

        assert nq.count_questions_due == 0
        assert nq.count_questions_matched_criteria == 1
        assert nq.count_recent_seen_mins_30 == 0
        assert nq.count_recent_seen_mins_60 == 0
        assert nq.count_questions_tagged == 1
        assert nq.count_times_question_seen == 0
        
        assert nq.tag_names_selected == [tag.name]
        assert nq.tag_names_for_question == [tag.name]

    def test_get_nq_unseen_with_schedule(self, user, tag, question):
        QuestionTag.objects.create(question=question, tag=tag, enabled=True)
        Schedule.objects.create(user=user, question=question, date_show_next=timezone.now() - timezone.timedelta(days=1))
        
        nq = NextQuestion(query_name=QUERY_UNSEEN, tag_ids_selected=[tag.id], user=user)
        assert nq.question is None
        assert nq.count_questions_due == 1
        assert nq.count_questions_tagged == 1
        assert nq.count_times_question_seen == 0
        assert nq.tag_names_selected == [tag.name]
        assert nq.tag_names_for_question == []

class Test__get_count_questions_due:
    def test_get_count_questions_due(self, user, tag, question):
        QuestionTag.objects.create(enabled=True, question=question, tag=tag, user=user)
        Schedule.objects.create(user=user, question=question, date_show_next=timezone.now() - timezone.timedelta(hours=1))
        
        nq = NextQuestion(query_name=QUERY_UNSEEN, tag_ids_selected=[tag.id], user=user)
        assert nq.count_questions_due == 1
        assert nq.count_questions_tagged == 1
        assert nq.count_times_question_seen == 0
        assert nq.question is None
        assert nq.tag_names_for_question == []
        assert nq.tag_names_selected == [tag.name]

    def test_count_questions_due_using_only_recent_schedule(self, tag, user):
        q1_not_due = Question.objects.create(question="Question 1", user=user)
        q2_due = Question.objects.create(question="Question 2", user=user)
        QuestionTag.objects.create(question=q1_not_due, tag=tag, enabled=True)
        QuestionTag.objects.create(question=q2_due, tag=tag, enabled=True)
        
        # Question 1: Old schedule due, newer schedule not due
        old_sched_due = Schedule.objects.create(
            user=user,
            question=q1_not_due,
            date_show_next=timezone.now() - timezone.timedelta(hours=2) # past (due)
        )
        old_sched_due.datetime_added = timezone.now() - timezone.timedelta(weeks=22) # older
        old_sched_due.save()
        
        new_sched_not_due = Schedule.objects.create(
            user=user,
            question=q1_not_due,
            date_show_next=timezone.now() + timezone.timedelta(hours=1) # future (not due)
        )
        new_sched_not_due.datetime_added = timezone.now() - timezone.timedelta(days=1) # newer
        new_sched_not_due.save()
        
        # Question 2: Old schedule not due, newer schedule due
        old_sched_not_due = Schedule.objects.create(
            user=user,
            question=q2_due,
            date_show_next=timezone.now() + timezone.timedelta(hours=2) # future (not due)
        )
        old_sched_not_due.datetime_added = timezone.now() - timezone.timedelta(weeks=10) # older
        old_sched_not_due.save()
        
        new_sched_due = Schedule.objects.create(
            user=user,
            question=q2_due,
            date_show_next=timezone.now() - timezone.timedelta(hours=1) # past (due)
        )
        new_sched_due.datetime_added = timezone.now() - timezone.timedelta(days=1) # newer
        new_sched_due.save()
        
        nq = NextQuestion(query_name=QUERY_DUE, tag_ids_selected=[tag.id], user=user)
        
        assert nq.question == q2_due
        assert nq.count_questions_tagged == 2
        assert nq.count_questions_due == 1
        assert nq.tag_names_for_question == [tag.name]
        assert nq.tag_names_selected == [tag.name]

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
        
        nq = NextQuestion(query_name=QUERY_UNSEEN, tag_ids_selected=[tag.id], user=user)
        
        assert nq.count_recent_seen_mins_30 == 3
        assert nq.count_recent_seen_mins_60 == 5

    def test_get_count_recent_schedules_empty(self, user):
        nq = NextQuestion(query_name=QUERY_UNSEEN, tag_ids_selected=[], user=user)
        
        assert nq.count_recent_seen_mins_30 == 0
        assert nq.count_recent_seen_mins_60 == 0
        assert nq.count_times_question_seen == 0

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
        
        nq = NextQuestion(query_name=QUERY_UNSEEN, tag_ids_selected=[], user=user)
        assert nq.question is None
        assert nq.count_recent_seen_mins_30 == 2
        assert nq.count_recent_seen_mins_60 == 2

class Test__QUERY_DUE:
    def test_get_nq_due_one_question(self, user, tag, question):
        QuestionTag.objects.create(question=question, tag=tag, enabled=True)
        Schedule.objects.create(user=user, question=question, date_show_next=timezone.now() - timezone.timedelta(hours=1))
        
        nq = NextQuestion(query_name=QUERY_DUE, tag_ids_selected=[tag.id], user=user)
        
        assert nq.question == question
        assert nq.count_questions_tagged == 1
        assert nq.count_times_question_seen == 1

        assert nq.tag_names_for_question == [tag.name]
        assert nq.tag_names_selected == [tag.name]

    def test_get_nq_due_multiple_questions(self, user, tag):
        question1 = Question.objects.create(question="Question 1 : -1h", user=user)
        question2 = Question.objects.create(question="Question 2 : -3h", user=user)
        question3 = Question.objects.create(question="Question 3 : -2h", user=user)
        
        QuestionTag.objects.create(question=question1, tag=tag, enabled=True)
        QuestionTag.objects.create(question=question2, tag=tag, enabled=True)
        QuestionTag.objects.create(question=question3, tag=tag, enabled=True)
        
        Schedule.objects.create(user=user, question=question1, date_show_next=timezone.now() - timezone.timedelta(hours=1))
        Schedule.objects.create(user=user, question=question2, date_show_next=timezone.now() - timezone.timedelta(hours=3))
        Schedule.objects.create(user=user, question=question3, date_show_next=timezone.now() - timezone.timedelta(hours=2))
        
        nq = NextQuestion(query_name=QUERY_DUE, tag_ids_selected=[tag.id], user=user)
        
        assert nq.question == question2
        assert nq.count_questions_tagged == 3
        assert nq.tag_names_for_question == [tag.name]
        assert nq.tag_names_selected == [tag.name]

    def test_get_nq_due_no_due_questions(self, user, tag, question):
        QuestionTag.objects.create(question=question, tag=tag, enabled=True)
        # date_show_next is in the future
        Schedule.objects.create(user=user, question=question, date_show_next=timezone.now() + timezone.timedelta(hours=1))
        
        nq = NextQuestion(query_name=QUERY_DUE, tag_ids_selected=[tag.id], user=user)
        
        assert nq.question is None
        assert nq.count_questions_tagged == 1
        assert nq.tag_names_for_question == []
        assert nq.tag_names_selected == [tag.name]

    def test_get_nq_due_multiple_tags(self, user):
        tag1 = Tag.objects.create(name="tag_1", user=user)
        tag2 = Tag.objects.create(name="tag_2", user=user)
        question1 = Question.objects.create(question="Question 1 - tag_1, -1h", user=user)
        question2 = Question.objects.create(question="Question 2 - tag_2, -2h, EXPECTED", user=user)
        
        QuestionTag.objects.create(question=question1, tag=tag1, enabled=True)
        QuestionTag.objects.create(question=question2, tag=tag2, enabled=True)
        
        Schedule.objects.create(user=user, question=question1, date_show_next=timezone.now() - timezone.timedelta(hours=1))
        Schedule.objects.create(user=user, question=question2, date_show_next=timezone.now() - timezone.timedelta(hours=2))
        
        nq = NextQuestion(query_name=QUERY_DUE, tag_ids_selected=[tag1.id, tag2.id], user=user)
        
        assert nq.question == question2
        assert nq.count_questions_tagged == 2
        assert nq.tag_names_for_question == [tag2.name]
        assert nq.tag_names_selected == [tag1.name, tag2.name]
    
class TestAllQueryTypesSameData:

    def test_different_results_for_query_seen_and_due(self, user, tag):
        # Create the following test data:
        #
        # | Question    | U  | Tags| Q added| S next  |Sched added|
        # |-------------|----|-----|--------|-------- |-----------|
        # | q1_future   | u1 | tag |        | -3m,+20m|-40m, -10m |
        # | q2_due      | u1 | tag |        | -10m    |-20m       |
        # | q3_unseen   | u1 | tag |        | (none)  | (none)    |
        # | q4_reinforce| u1 | tag |        | -5m     |-2h        |
        #
        # Notes:
        # U = User who created the question (i.e., Question.user field)
        # Tags = tags that are applied to the question via the QuestionTag model
        # Schedules = schedules associated with the question via the Schedule.question foreign key; the column value refers to the Schedule.date_show_next field; e.g., -1d = 1 day before now
        # Q added = when the question was added (relative to now); i.e., Question.datetime_added field; e.g., -2d = 2 days before now
        # S next = Schedule.date_show_next field; e.g., -1d = 1 day before now
        # Sched added = when the schedule was added (relative to now); i.e., Schedule.datetime_added field; e.g., -2d = 2 days before now

        # Create questions
        q1_future = Question.objects.create(question="Question 1: not due", user=user)
        q2_due = Question.objects.create(question="Question 2: due", user=user)
        q3_unseen = Question.objects.create(question="Question 3: unseen", user=user)
        q4_reinforce = Question.objects.create(question="Question 4: reinforce", user=user)
    
        # Create QuestionTags
        QuestionTag.objects.create(question=q1_future, tag=tag, enabled=True)
        QuestionTag.objects.create(question=q2_due, tag=tag, enabled=True)
        QuestionTag.objects.create(question=q3_unseen, tag=tag, enabled=True)
        QuestionTag.objects.create(question=q4_reinforce, tag=tag, enabled=True)
    
        # Create Schedules
        sched_q1_past = Schedule.objects.create(
            user=user,
            question=q1_future,
            date_show_next=timezone.now() - timezone.timedelta(minutes=3), # past
        )
        sched_q1_past.datetime_added = timezone.now() - timezone.timedelta(minutes=40)
        sched_q1_past.save()
        
        sched_q1_future = Schedule.objects.create(
            user=user,
            question=q1_future,
            date_show_next=timezone.now() + timezone.timedelta(minutes=20), # future
        )
        sched_q1_future.datetime_added = timezone.now() - timezone.timedelta(minutes=10)
        sched_q1_future.save()

        sched_q2_due = Schedule.objects.create(
            user=user,
            question=q2_due,
            date_show_next=timezone.now() - timezone.timedelta(minutes=10), # past
        )
        sched_q2_due.datetime_added = timezone.now() - timezone.timedelta(minutes=20)
        sched_q2_due.save()

        # q3_unseen: no schedule

        # q4_reinforce
        sched_q4_reinforce = Schedule.objects.create(
            user=user,
            question=q4_reinforce,
            date_show_next=timezone.now() - timezone.timedelta(minutes=5), # past
        )
        sched_q4_reinforce.datetime_added = timezone.now() - timezone.timedelta(hours=2)
        sched_q4_reinforce.save()
    

        # nq = "next question"
        # Test QUERY_DUE
        nq_due = NextQuestion(query_name=QUERY_DUE, tag_ids_selected=[tag.id], user=user)
        assert nq_due.question == q2_due
        assert nq_due.count_times_question_seen == 1
        assert nq_due.count_questions_due == 2
        assert nq_due.count_questions_matched_criteria == 2
        assert nq_due.count_questions_tagged == 4
        assert nq_due.count_recent_seen_mins_30 == 2
        assert nq_due.count_recent_seen_mins_60 == 3
        assert nq_due.tag_names_for_question == [TAG_NAME]
        assert nq_due.tag_names_selected == [TAG_NAME]
    
        # Test QUERY_UNSEEN
        nq_unseen = NextQuestion(query_name=QUERY_UNSEEN, tag_ids_selected=[tag.id], user=user)
        assert nq_unseen.question == q3_unseen
        assert nq_unseen.count_times_question_seen == 0
        assert nq_unseen.count_questions_due == 2
        assert nq_unseen.count_questions_matched_criteria == 1
        assert nq_unseen.count_questions_tagged == 4
        assert nq_unseen.count_recent_seen_mins_30 == 2
        assert nq_unseen.count_recent_seen_mins_60 == 3
        assert nq_unseen.tag_names_for_question == [TAG_NAME]
        assert nq_unseen.tag_names_selected == [TAG_NAME]

        # Test QUERY_UNSEEN_THEN_DUE
        nq_unseen_then_due = NextQuestion(query_name=QUERY_UNSEEN_THEN_DUE, tag_ids_selected=[tag.id], user=user)
        assert nq_unseen_then_due.question == q3_unseen
        assert nq_unseen_then_due.count_times_question_seen == 0
        assert nq_unseen_then_due.count_questions_due == 2
        assert nq_unseen_then_due.count_questions_matched_criteria == 3
        assert nq_unseen_then_due.count_questions_tagged == 4
        assert nq_unseen_then_due.count_recent_seen_mins_30 == 2
        assert nq_unseen_then_due.count_recent_seen_mins_60 == 3
        assert nq_unseen_then_due.tag_names_for_question == [TAG_NAME]
        assert nq_unseen_then_due.tag_names_selected == [TAG_NAME]
        
        # Test QUERY_FUTURE
        nq_future = NextQuestion(query_name=QUERY_FUTURE, tag_ids_selected=[tag.id], user=user)
        assert nq_future.question == q1_future
        assert nq_future.count_times_question_seen == 2
        assert nq_future.count_questions_due == 2
        assert nq_future.count_questions_matched_criteria == 1
        assert nq_future.count_questions_tagged == 4
        assert nq_future.count_recent_seen_mins_30 == 2
        assert nq_future.count_recent_seen_mins_60 == 3
        assert nq_future.tag_names_for_question == [TAG_NAME]
        assert nq_future.tag_names_selected == [TAG_NAME]
        
        # Test QUERY_REINFORCE
        nq_reinforce = NextQuestion(query_name=QUERY_REINFORCE, tag_ids_selected=[tag.id], user=user)
        assert nq_reinforce.question == q4_reinforce
        assert nq_reinforce.count_times_question_seen == 1
        assert nq_reinforce.count_questions_due == 2
        assert nq_reinforce.count_questions_matched_criteria == 2
        assert nq_reinforce.count_questions_tagged == 4
        assert nq_reinforce.count_recent_seen_mins_30 == 2
        assert nq_reinforce.count_recent_seen_mins_60 == 3
        assert nq_reinforce.tag_names_for_question == [TAG_NAME]
        assert nq_reinforce.tag_names_selected == [TAG_NAME]
        
        # Verify different results
        assert nq_unseen.question != nq_due.question
        assert nq_unseen.question == nq_unseen_then_due.question
        assert nq_future.question != nq_unseen_then_due.question
        assert nq_future.question != nq_due.question
        assert nq_unseen.question != nq_due.question != nq_future.question != nq_reinforce.question