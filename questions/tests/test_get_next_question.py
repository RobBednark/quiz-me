import pytest
from django.utils import timezone
from questions.forms import (
   QUERY_FUTURE,
   QUERY_OLDEST_DUE,
   QUERY_OLDEST_DUE_OR_UNSEEN_BY_TAG,
   QUERY_OLDEST_DUE_OR_UNSEEN,
   QUERY_REINFORCE,
   QUERY_UNSEEN,
   QUERY_UNSEEN_BY_OLDEST_VIEWED_TAG,
   QUERY_UNSEEN_THEN_OLDEST_DUE,
)
from questions.models import Question, Tag, QuestionTag, Schedule
from questions.get_next_question import NextQuestion
from emailusername.models import User

# Use the Django database for all the tests
pytestmark = pytest.mark.django_db

TAG_1_NAME = "tag 1"
@pytest.fixture
def user():
    return User.objects.create(email="testuser@example.com")

@pytest.fixture(autouse=True)
def tag(user):
    return Tag.objects.create(name=TAG_1_NAME, user=user)

@pytest.fixture
def question(user):
    return Question.objects.create(question="Test question", user=user)

# Template for assertions:
'''
        assert xx.question == ...

        assert xx.count_questions_due == 99
        assert xx.count_questions_tagged == 99
        assert xx.count_recent_seen_mins_30 == 99
        assert xx.count_recent_seen_mins_60 == 99
        assert xx.count_times_question_seen == 99

        assert xx.tag_names_for_question == [TAG_1_NAME]
        assert xx.tag_names_selected == [TAG_1_NAME]
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
        QuestionTag.objects.create(question=question, tag=tag)
        
        nq = NextQuestion(query_name=QUERY_UNSEEN, tag_ids_selected=[tag.id], user=user)

        assert nq.question == question

        assert nq.count_questions_due == 0
        assert nq.count_recent_seen_mins_30 == 0
        assert nq.count_recent_seen_mins_60 == 0
        assert nq.count_questions_tagged == 1
        assert nq.count_times_question_seen == 0
        
        assert nq.tag_names_selected == [tag.name]
        assert nq.tag_names_for_question == [tag.name]

    def test_get_nq_unseen_with_schedule(self, user, tag, question):
        QuestionTag.objects.create(question=question, tag=tag)
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
        QuestionTag.objects.create(question=question, tag=tag, user=user)
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
        q2_oldest_due = Question.objects.create(question="Question 2", user=user)
        QuestionTag.objects.create(question=q1_not_due, tag=tag)
        QuestionTag.objects.create(question=q2_oldest_due, tag=tag)
        
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
            question=q2_oldest_due,
            date_show_next=timezone.now() + timezone.timedelta(hours=2) # future (not due)
        )
        old_sched_not_due.datetime_added = timezone.now() - timezone.timedelta(weeks=10) # older
        old_sched_not_due.save()
        
        new_sched_due = Schedule.objects.create(
            user=user,
            question=q2_oldest_due,
            date_show_next=timezone.now() - timezone.timedelta(hours=1) # past (due)
        )
        new_sched_due.datetime_added = timezone.now() - timezone.timedelta(days=1) # newer
        new_sched_due.save()
        
        nq = NextQuestion(query_name=QUERY_OLDEST_DUE, tag_ids_selected=[tag.id], user=user)
        
        assert nq.question == q2_oldest_due
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

class Test__QUERY_OLDEST_DUE:
    def test_get_nq_oldest_due_one_question(self, user, tag, question):
        QuestionTag.objects.create(question=question, tag=tag)
        Schedule.objects.create(user=user, question=question, date_show_next=timezone.now() - timezone.timedelta(hours=1))
        
        nq = NextQuestion(query_name=QUERY_OLDEST_DUE, tag_ids_selected=[tag.id], user=user)
        
        assert nq.question == question
        assert nq.count_questions_tagged == 1
        assert nq.count_times_question_seen == 1

        assert nq.tag_names_for_question == [tag.name]
        assert nq.tag_names_selected == [tag.name]

    def test_get_nq_oldest_due_multiple_questions(self, user, tag):
        question1 = Question.objects.create(question="Question 1 : -1h", user=user)
        question2 = Question.objects.create(question="Question 2 : -3h", user=user)
        question3 = Question.objects.create(question="Question 3 : -2h", user=user)
        
        QuestionTag.objects.create(question=question1, tag=tag)
        QuestionTag.objects.create(question=question2, tag=tag)
        QuestionTag.objects.create(question=question3, tag=tag)
        
        Schedule.objects.create(user=user, question=question1, date_show_next=timezone.now() - timezone.timedelta(hours=1))
        Schedule.objects.create(user=user, question=question2, date_show_next=timezone.now() - timezone.timedelta(hours=3))
        Schedule.objects.create(user=user, question=question3, date_show_next=timezone.now() - timezone.timedelta(hours=2))
        
        nq = NextQuestion(query_name=QUERY_OLDEST_DUE, tag_ids_selected=[tag.id], user=user)
        
        assert nq.question == question2
        assert nq.count_questions_tagged == 3
        assert nq.tag_names_for_question == [tag.name]
        assert nq.tag_names_selected == [tag.name]

    def test_get_nq_oldest_due_no_due_questions(self, user, tag, question):
        QuestionTag.objects.create(question=question, tag=tag)
        # date_show_next is in the future
        Schedule.objects.create(user=user, question=question, date_show_next=timezone.now() + timezone.timedelta(hours=1))
        
        nq = NextQuestion(query_name=QUERY_OLDEST_DUE, tag_ids_selected=[tag.id], user=user)
        
        assert nq.question is None
        assert nq.count_questions_tagged == 1
        assert nq.tag_names_for_question == []
        assert nq.tag_names_selected == [tag.name]

    def test_get_nq_oldest_due_multiple_tags(self, user):
        tag1 = Tag.objects.create(name="tag_1", user=user)
        tag2 = Tag.objects.create(name="tag_2", user=user)
        question1 = Question.objects.create(question="Question 1 - tag_1, -1h", user=user)
        question2 = Question.objects.create(question="Question 2 - tag_2, -2h, EXPECTED", user=user)
        
        QuestionTag.objects.create(question=question1, tag=tag1)
        QuestionTag.objects.create(question=question2, tag=tag2)
        
        Schedule.objects.create(user=user, question=question1, date_show_next=timezone.now() - timezone.timedelta(hours=1))
        Schedule.objects.create(user=user, question=question2, date_show_next=timezone.now() - timezone.timedelta(hours=2))
        
        nq = NextQuestion(query_name=QUERY_OLDEST_DUE, tag_ids_selected=[tag1.id, tag2.id], user=user)
        
        assert nq.question == question2
        assert nq.count_questions_tagged == 2
        assert nq.tag_names_for_question == [tag2.name]
        assert nq.tag_names_selected == [tag1.name, tag2.name]
    
class TestAllQueryTypesSameData:

    def test_different_results_for_query_seen_and_due(self, user, tag):
        # Ideally, we want to test each of the QUERY_*'s with the same data (shown in the table below) and same tags
        # (TAG_IDS_COMMON), and show that each query returns a different question.  The exceptions to this are the following
        # queries, which return the same question for the given tag(s):
        #   QUERY_UNSEEN == QUERY_UNSEEN_THEN_OLDEST_DUE  (always true)
        #   QUERY_UNSEEN == QUERY_UNSEEN_THEN_OLDEST_DUE == QUERY_OLDEST_DUE_OR_UNSEEN == QUERY_OLDEST_DUE_OR_UNSEEN_BY_TAG (true for this set of data)
        
        #   Q: Will these always return the same question for the given tag(s)?
        #      QUERY_OLDEST_DUE_OR_UNSEEN
        #      QUERY_OLDEST_DUE_OR_UNSEEN_BY_TAG
        #   A: No.  
        #       QUERY_OLDEST_DUE_OR_UNSEEN_BY_TAG looks at Schedule.added ("oldest viewed")
        #       QUERY_OLDEST_DUE_OR_UNSEEN        looks at Schedule.next

        # Test data:
        # ----------
        #
        # | Question                | U  | Tags      | Q.added| Sched.added| S.next    | Notes
        # |-------------------------|----|-----------|--------|------------|-----------|------------------------------------------
        # | q1_unseen_older         | u1 | tag1      | -99w   | (none)     | (none)    | oldest Ques.added
        # | q2_unseen_newer_nm      | u1 | tag2      | -8w    | (none)     | (none)    | no matches; q2.Ques.added < q1
        # | q3_oldest_due           | u1 | tag1      | -7w    | -8w        | -9w       | oldest Sched.next
        # | q4_reinforce_newer      | u1 | tag1      | -8w    | -6w        | -1s       | newest Sched.next < now; q4.Sched.next > q5
        # | q5_reinforce_older_nm   | u1 | tag1,tag2 | -6w    | -15m       | -6w       | no matches; q3 < q5.Sched.next < q4
        # | q6_future_oldest_due    | u1 | tag1,tag2 | -1d    | -45m, -10m | -10w,+1m  | now < q6.Sched.next < q7
        # | q7_future_newest_due_nm | u1 | tag1      | -2d    | -2m        | +2m       | no matches; q7.Sched.next > q6
        # | q8_due_by_tag3_nm       | u1 | tag3      | -3s    | -10w,-9w   | -5s,+9w   | oldest Sched.added; q8.Sched.next > q1-7; no match, but this triggers q9 to be picked because of the oldest Sched.added; future due
        # | q9_unseen_by_tag3       | u1 | tag3      | -2s    | (none)     | (none)    | q10 > q9.Ques.added > q1-q8
        # | q10_unseen_by_tag3_nm   | u1 | tag3      | -1s    | (none)     | (none)    | no matches; oldest Ques.added
        # | q11_untag_unseen_old_nm | u1 | (none)    | -99w   | (none)     | (none)    | no matches; untagged; oldest Ques.added
        # | q12_untag_unseen_new_nm | u1 | (none)    | 0      | (none)     | (none)    | no matches; untagged; newest Ques.added
        # | q13_untag_due_before_nm | u1 | (none)    | -99w   | -99w       | -1h       | no matches; untagged
        # | q14_untag_due_after_nm  | u1 | (none)    | 0      | 0          | +1m       | no matches; untagged
        # | q15_tag5_due_nm         | u1 | tag5      | -2d    | -45m       | -1w       | to test UNSEEN_BY_TAG and UNSEEN with no matches
        # | q16_tag6_unseen_nm      | u1 | tag6      | -1h    | (none)     | (none)    | to test DUE with no matches
        # | q17_tag7_due_future_nm  | u1 | tag7      | -1h    | -1d        | +1h       | to test UNSEEN_THEN_OLDEST with no matches
        
        # Types of questions each tag has:
        # --------------------------------
        # tag1: due, due_future, unseen
        # tag2: due, due_future, unseen
        # tag3: due, due_future, unseen
        # tag4: (no questions)
        # tag5: due        (to test QUERY_UNSEEN_THEN_OLDEST_DUE no unseen; and also to test several queries that pick None)
        # tag6: unseen     (to test several queries that pick None)
        # tag7: due_future (to test several queries that pick None)
        
        # tag5, tag6, tag7 are used to test:
        #     QUERY_UNSEEN_THEN_OLDEST_DUE
        #     picking None for various queries
        
        # Tags matching queries:
        # ----------------------
        # q1_unseen_older      QUERY_UNSEEN      QUERY_UNSEEN_THEN_OLDEST_DUE  QUERY_OLDEST_DUE_OR_UNSEEN_BY_TAG
        # q3_oldest_due        QUERY_OLDEST_DUE  QUERY_OLDEST_DUE_OR_UNSEEN
        # q4_reinforce_newer   QUERY_REINFORCE
        # q6_future_oldest_due QUERY_FUTURE
        # q9_unseen_by_tag3    QUERY_UNSEEN_BY_OLDEST_VIEWED_TAG

        # "Oldest viewed" is the older of unseen.added or schedule.added
        
        # Dates by tag:
        # -----|--------|--------|--------|--------|--------| -------|--------|
        # Tag  | Oldest | Oldest | Oldest | Oldest | Newest | Newest | Oldest |
        #      | unseen | due    | Sched  | viewed | Sched  | unseen | due or |
        #      | added  | S.next | added  |        | added  | added  | unseen |
        # -----|--------|--------|--------|--------| -------| -------|--------|
        # tag1 | -99w   | -9w    | -8w    | -2m    | -2m    | -99w   | -99w   |
        # tag2 | -8w    | -6w    | -15m   | -10m   | -10m   | -8w    | -8w    |
        # tag3 | -3s    | +9w    | -9w    | -2s    | -9w    | -2s    | -3s    |
        # tag4 | none   | none   | none   | none   | none   | none   | none   |
        # -----|--------|--------|--------|--------| -------| -------|--------|
        
        # Overlapping queries:
        # --------------------
        #  QUERY_UNSEEN == QUERY_UNSEEN_THEN_OLDEST_DUE == QUERY_OLDEST_DUE_OR_UNSEEN == QUERY_OLDEST_DUE_OR_UNSEEN_BY_TAG

        
        # For by oldest-viewed tag (QUERY_UNSEEN_BY_OLDEST_VIEWED_TAG), create questions such that:
        #   Instead of selecting q1, it selects an unseen question with a different tag that has a newer Question.added, but that tag has a question with an older Schedule.datetime_added than Q1.Schedule.datetime_added

        # For QUERY_OLDEST_DUE_OR_UNSEEN, create questions such that:
        #   Instead of selecting qx, it selects qy, a question that has been seen, where qy.Schedule.datetime_added is older than
        #   qx.dateetime_added (which will be equivalent to QUERY_OLDEST_DUE)
        
        #### For QUERY_OLDEST_DUE_OR_UNSEEN_BY_TAG, the question for create questions such that:
        ####   a) Instead of selecting q1_unseen_older (tag1) , it selects a due question with a different tag that has an older Schedule.date_show_next than q1_unseen_older.datetime_added
        ####   - and also the inverse: - 
        ####  
        
        # Notes:
        # U = User who created the question (i.e., Question.user field)
        # Tags = tags that are applied to the question via the QuestionTag model
        # Schedules = schedules associated with the question via the Schedule.question foreign key; the column value refers to the Schedule.date_show_next field; e.g., -1d = 1 day before now
        # Q added = when the question was added (relative to now); i.e., Question.datetime_added field; e.g., -2d = 2 days before now
        # S next = Schedule.date_show_next field; e.g., -1d = 1 day before now
        # Sched added = when the schedule was added (relative to now); i.e., Schedule.datetime_added field; e.g., -2d = 2 days before now
        # nm = no match; i.e., this question won't match any QUERY_*

        # Create questions
        q1_unseen_older= Question.objects.create(question="Question 1: unseen older", user=user)
        q2_unseen_newer= Question.objects.create(question="Question 2: unseen newer", user=user)
        q3_oldest_due = Question.objects.create(question="Question 3: oldest due", user=user)
        q4_reinforce_newer = Question.objects.create(question="Question 4: reinforce newer", user=user)
        q5_reinforce_older = Question.objects.create(question="Question 5: reinforce older", user=user)
        q6_future_oldest_due = Question.objects.create(question="Question 6: future oldest", user=user)
        q7_future_newest_due = Question.objects.create(question="Question 7: future newest", user=user)
        q8_due_by_tag3_nm = Question.objects.create(question="Question 8: seen by tag3 nm", user=user)
        q9_unseen_by_tag3 = Question.objects.create(question="Question 9: unseen by tag3", user=user)
        q10_unseen_by_tag3_nm = Question.objects.create(question="Question 10: unseen by tag3 nm", user=user)
        q11_untag_unseen_old_nm = Question.objects.create(question="Question 11: untagged unseen older nm", user=user)
        q12_untag_unseen_new_nm = Question.objects.create(question="Question 12: untagged unseen newer nm", user=user)
        q13_untag_due_before_nm = Question.objects.create(question="Question 13: untagged due before now nm", user=user)
        q14_untag_due_after_nm = Question.objects.create(question="Question 14: untagged due after now nm", user=user)
        q15_tag5_due_nm = Question.objects.create(question="Question 15: due, tag5 nm", user=user)
        q16_tag6_unseen_nm = Question.objects.create(question="Question 16: unseen, tag6 nm", user=user)
        q17_tag7_due_future_nm = Question.objects.create(question="Question 17: due_future, tag7 nm", user=user)
        
        q1_unseen_older.datetime_added = timezone.now() - timezone.timedelta(weeks=99)
        q2_unseen_newer.datetime_added = timezone.now() - timezone.timedelta(weeks=8)
        q3_oldest_due.datetime_added = timezone.now() - timezone.timedelta(weeks=7)
        q4_reinforce_newer.datetime_added = timezone.now() - timezone.timedelta(weeks=8)
        q5_reinforce_older.datetime_added = timezone.now() - timezone.timedelta(weeks=6)
        q6_future_oldest_due.datetime_added = timezone.now() - timezone.timedelta(days=1)
        q7_future_newest_due.datetime_added = timezone.now() - timezone.timedelta(days=2)
        q8_due_by_tag3_nm.datetime_added = timezone.now() - timezone.timedelta(seconds=3)
        q9_unseen_by_tag3.datetime_added = timezone.now() - timezone.timedelta(seconds=2)
        q10_unseen_by_tag3_nm.datetime_added = timezone.now() - timezone.timedelta(seconds=1)
        q11_untag_unseen_old_nm.datetime_added = timezone.now() - timezone.timedelta(weeks=99)
        q12_untag_unseen_new_nm.datetime_added = timezone.now()
        q13_untag_due_before_nm.datetime_added = timezone.now() - timezone.timedelta(weeks=99)
        q14_untag_due_after_nm.datetime_added = timezone.now()
        q15_tag5_due_nm.datetime_added = timezone.now() - timezone.timedelta(days=2)
        q16_tag6_unseen_nm.datetime_added = timezone.now() - timezone.timedelta(hours=1)
        q17_tag7_due_future_nm.datetime_added = timezone.now() - timezone.timedelta(hours=1)
        
        q1_unseen_older.save()
        q2_unseen_newer.save()
        q3_oldest_due.save()
        q4_reinforce_newer.save()
        q5_reinforce_older.save()
        q6_future_oldest_due.save()
        q7_future_newest_due.save()
        q8_due_by_tag3_nm.save()
        q9_unseen_by_tag3.save()
        q10_unseen_by_tag3_nm.save()
        q11_untag_unseen_old_nm.save()
        q12_untag_unseen_new_nm.save()
        q13_untag_due_before_nm.save()
        q14_untag_due_after_nm.save()
        q15_tag5_due_nm.save()
        q16_tag6_unseen_nm.save()
        q17_tag7_due_future_nm.save()
    
        tag1 = tag
        tag2 = Tag.objects.create(name="tag 2", user=user)
        tag3 = Tag.objects.create(name="tag 3", user=user)
        tag4_no_questions = Tag.objects.create(name="tag 4 no questions", user=user)
        tag5_due = Tag.objects.create(name="tag 5 due", user=user)
        tag6_unseen = Tag.objects.create(name="tag 6 unseen", user=user)
        tag7_due_future = Tag.objects.create(name="tag 7 due future", user=user)
        
        # Create QuestionTags
        QuestionTag.objects.create(question=q1_unseen_older, tag=tag1)
        QuestionTag.objects.create(question=q2_unseen_newer, tag=tag2)
        QuestionTag.objects.create(question=q3_oldest_due, tag=tag1)
        QuestionTag.objects.create(question=q4_reinforce_newer, tag=tag1)
        QuestionTag.objects.create(question=q5_reinforce_older, tag=tag1)
        QuestionTag.objects.create(question=q5_reinforce_older, tag=tag2)  # 2nd tag
        QuestionTag.objects.create(question=q6_future_oldest_due, tag=tag1)
        QuestionTag.objects.create(question=q6_future_oldest_due, tag=tag2) # 2nd tag
        QuestionTag.objects.create(question=q7_future_newest_due, tag=tag1)
        QuestionTag.objects.create(question=q8_due_by_tag3_nm, tag=tag3)
        QuestionTag.objects.create(question=q9_unseen_by_tag3, tag=tag3)
        QuestionTag.objects.create(question=q10_unseen_by_tag3_nm, tag=tag3)
        QuestionTag.objects.create(question=q15_tag5_due_nm, tag=tag5_due)
        QuestionTag.objects.create(question=q16_tag6_unseen_nm, tag=tag6_unseen)
        QuestionTag.objects.create(question=q17_tag7_due_future_nm, tag=tag7_due_future)

        COUNT_QUESTIONS_WITH_TAG = 10
        COUNT_QUESTIONS_UNSEEN = 4
        COUNT_QUESTIONS_DUE = 3 # q3, q4, q5 (not q8)
        COUNT_RECENT_SEEN_MINS_30 = 5  # Sched.added q5, q6.a, q7, q8
        COUNT_RECENT_SEEN_MINS_60 = COUNT_RECENT_SEEN_MINS_30 + 2  # Sched.added q6, q15

        TAG_IDS_ALL = [tag1.id, tag2.id, tag3.id, tag4_no_questions.id]
        # "COMMON" means testing each of the queries with the same common set of tags
        TAG_NAMES_COMMON = [tag1.name, tag2.name, tag3.name, tag4_no_questions.name]
        TAG_IDS_COMMON = TAG_IDS_ALL
        TAG_NAMES_Q6_FUTURE_OLDEST_DUE = [tag1.name, tag2.name]
        TAG5_DUE_ONLY = tag5_due
        TAG6_UNSEEN_ONLY = tag6_unseen
        TAG7_DUE_FUTURE_ONLY = tag7_due_future
    
        sched_q3_oldest_due = Schedule.objects.create(user=user,
            question=q3_oldest_due, date_show_next=timezone.now() - timezone.timedelta(weeks=9)) # past
        sched_q3_oldest_due.datetime_added = timezone.now() - timezone.timedelta(weeks=8)
        sched_q3_oldest_due.save()
        
        sched_q4_reinforce_newer = Schedule.objects.create(user=user,
            question=q4_reinforce_newer, date_show_next=timezone.now() - timezone.timedelta(seconds=1)) # past
        sched_q4_reinforce_newer.datetime_added = timezone.now() - timezone.timedelta(minutes=6)
        sched_q4_reinforce_newer.save()
        
        sched_q5_reinforce_older = Schedule.objects.create(user=user,
            question=q5_reinforce_older, date_show_next=timezone.now() - timezone.timedelta(weeks=6)) # past
        sched_q5_reinforce_older.datetime_added = timezone.now() - timezone.timedelta(minutes=15)
        sched_q5_reinforce_older.save()

        sched_q6_future_oldest_due_1 = Schedule.objects.create(user=user,
            question=q6_future_oldest_due, date_show_next=timezone.now() - timezone.timedelta(weeks=10)) # past
        sched_q6_future_oldest_due_1.datetime_added = timezone.now() - timezone.timedelta(minutes=45)
        sched_q6_future_oldest_due_1.save()
        
        sched_q6_future_oldest_due_2 = Schedule.objects.create(user=user,
            question=q6_future_oldest_due, date_show_next=timezone.now() + timezone.timedelta(minutes=1)) # future
        sched_q6_future_oldest_due_2.datetime_added = timezone.now() - timezone.timedelta(minutes=10)
        sched_q6_future_oldest_due_2.save()

        sched_q7_future_newest_due = Schedule.objects.create(user=user,
            question=q7_future_newest_due, date_show_next=timezone.now() + timezone.timedelta(minutes=2)) # future
        sched_q7_future_newest_due.datetime_added = timezone.now() - timezone.timedelta(minutes=2)
        sched_q7_future_newest_due.save()
        
        sched_q8_due_by_tag3_nm_1 = Schedule.objects.create(user=user,
            question=q8_due_by_tag3_nm, date_show_next=timezone.now() - timezone.timedelta(seconds=5)) # past
        sched_q8_due_by_tag3_nm_1.datetime_added = timezone.now() - timezone.timedelta(weeks=10)
        sched_q8_due_by_tag3_nm_1.save()
        
        sched_q8_due_by_tag3_nm_2 = Schedule.objects.create(user=user,
            question=q8_due_by_tag3_nm, date_show_next=timezone.now() + timezone.timedelta(weeks=9)) # future
        sched_q8_due_by_tag3_nm_2.datetime_added = timezone.now() - timezone.timedelta(weeks=9)
        sched_q8_due_by_tag3_nm_2.save()
        
        sched_13_untag_due_before_nm = Schedule.objects.create(user=user,
           question=q13_untag_due_before_nm, date_show_next=timezone.now() - timezone.timedelta(weeks=99))
        sched_13_untag_due_before_nm.datetime_added = timezone.now() - timezone.timedelta(weeks=99)
        sched_13_untag_due_before_nm.save()

        sched_14_untag_due_after_nm = Schedule.objects.create(user=user,
           question=q14_untag_due_after_nm, date_show_next=timezone.now() + timezone.timedelta(minutes=1))
        sched_14_untag_due_after_nm.datetime_added = timezone.now()
        sched_14_untag_due_after_nm.save()

        sched_15_tag5_due_nm = Schedule.objects.create(user=user,
           question=q15_tag5_due_nm, date_show_next=timezone.now() - timezone.timedelta(weeks=1))
        sched_15_tag5_due_nm.datetime_added = timezone.now() - timezone.timedelta(minutes=45)
        sched_15_tag5_due_nm.save()

        sched_17_tag7_due_future_nm = Schedule.objects.create(user=user,
            question=q17_tag7_due_future_nm, date_show_next=timezone.now() + timezone.timedelta(hours=1))
        sched_17_tag7_due_future_nm.datetime_added = timezone.now() - timezone.timedelta(days=1)
        sched_17_tag7_due_future_nm.save()

        # nq = "next question"
        
        ############################################################
        # NextQuestion queries with the same tag_ids_selected, where almost all of them should return a different question.
        ############################################################
        
        # Test QUERY_OLDEST_DUE
        nq_oldest_due = NextQuestion(query_name=QUERY_OLDEST_DUE, tag_ids_selected=TAG_IDS_COMMON, user=user)
        assert nq_oldest_due.question == q3_oldest_due
        assert nq_oldest_due.count_times_question_seen == 1
        assert nq_oldest_due.count_questions_due == COUNT_QUESTIONS_DUE
        assert nq_oldest_due.count_questions_tagged == COUNT_QUESTIONS_WITH_TAG
        assert nq_oldest_due.count_questions_unseen == COUNT_QUESTIONS_UNSEEN
        assert nq_oldest_due.count_recent_seen_mins_30 == COUNT_RECENT_SEEN_MINS_30
        assert nq_oldest_due.count_recent_seen_mins_60 == COUNT_RECENT_SEEN_MINS_60
        assert nq_oldest_due.tag_names_for_question == [TAG_1_NAME]
        assert nq_oldest_due.tag_names_selected == TAG_NAMES_COMMON
    
        # Test QUERY_UNSEEN
        nq_unseen = NextQuestion(query_name=QUERY_UNSEEN, tag_ids_selected=TAG_IDS_COMMON, user=user)
        assert nq_unseen.question == q1_unseen_older
        assert nq_unseen.count_times_question_seen == 0
        assert nq_unseen.count_questions_due == COUNT_QUESTIONS_DUE
        assert nq_unseen.count_questions_tagged == COUNT_QUESTIONS_WITH_TAG
        assert nq_unseen.count_questions_unseen == COUNT_QUESTIONS_UNSEEN
        assert nq_unseen.count_recent_seen_mins_30 == COUNT_RECENT_SEEN_MINS_30
        assert nq_unseen.count_recent_seen_mins_60 == COUNT_RECENT_SEEN_MINS_60
        assert nq_unseen.tag_names_for_question == [TAG_1_NAME]
        assert nq_unseen.tag_names_selected == TAG_NAMES_COMMON

        # Test QUERY_UNSEEN_THEN_OLDEST_DUE
        nq_unseen_then_oldest_due = NextQuestion(query_name=QUERY_UNSEEN_THEN_OLDEST_DUE, tag_ids_selected=TAG_IDS_COMMON, user=user)
        assert nq_unseen_then_oldest_due.question == q1_unseen_older
        assert nq_unseen_then_oldest_due.count_times_question_seen == 0
        assert nq_unseen_then_oldest_due.count_questions_due == COUNT_QUESTIONS_DUE
        assert nq_unseen_then_oldest_due.count_questions_tagged == COUNT_QUESTIONS_WITH_TAG
        assert nq_unseen_then_oldest_due.count_questions_unseen == COUNT_QUESTIONS_UNSEEN
        assert nq_unseen_then_oldest_due.count_recent_seen_mins_30 == COUNT_RECENT_SEEN_MINS_30
        assert nq_unseen_then_oldest_due.count_recent_seen_mins_60 == COUNT_RECENT_SEEN_MINS_60
        assert nq_unseen_then_oldest_due.tag_names_for_question == [TAG_1_NAME]
        assert nq_unseen_then_oldest_due.tag_names_selected == TAG_NAMES_COMMON
        
        # Test QUERY_FUTURE
        nq_future = NextQuestion(query_name=QUERY_FUTURE, tag_ids_selected=TAG_IDS_COMMON, user=user)
        assert nq_future.question == q6_future_oldest_due
        assert nq_future.count_times_question_seen == 2
        assert nq_future.count_questions_due == COUNT_QUESTIONS_DUE
        assert nq_future.count_questions_tagged == COUNT_QUESTIONS_WITH_TAG
        assert nq_future.count_questions_unseen == COUNT_QUESTIONS_UNSEEN
        assert nq_future.count_recent_seen_mins_30 == COUNT_RECENT_SEEN_MINS_30
        assert nq_future.count_recent_seen_mins_60 == COUNT_RECENT_SEEN_MINS_60
        assert nq_future.tag_names_for_question == TAG_NAMES_Q6_FUTURE_OLDEST_DUE
        assert nq_future.tag_names_selected == TAG_NAMES_COMMON
        
        # Test QUERY_REINFORCE
        nq_reinforce = NextQuestion(query_name=QUERY_REINFORCE, tag_ids_selected=TAG_IDS_COMMON, user=user)
        assert nq_reinforce.question == q4_reinforce_newer
        assert nq_reinforce.count_times_question_seen == 1
        assert nq_reinforce.count_questions_due == COUNT_QUESTIONS_DUE
        assert nq_reinforce.count_questions_tagged == COUNT_QUESTIONS_WITH_TAG
        assert nq_reinforce.count_questions_unseen == COUNT_QUESTIONS_UNSEEN
        assert nq_reinforce.count_recent_seen_mins_30 == COUNT_RECENT_SEEN_MINS_30
        assert nq_reinforce.count_recent_seen_mins_60 == COUNT_RECENT_SEEN_MINS_60
        assert nq_reinforce.tag_names_for_question == [TAG_1_NAME]
        assert nq_reinforce.tag_names_selected == TAG_NAMES_COMMON

        # Test QUERY_OLDEST_DUE_OR_UNSEEN  (same results as QUERY_UNSEEN)
        nq_oldest_due_or_unseen = NextQuestion(query_name=QUERY_OLDEST_DUE_OR_UNSEEN, tag_ids_selected=TAG_IDS_COMMON, user=user)
        assert nq_oldest_due_or_unseen.question == q1_unseen_older
        assert nq_oldest_due_or_unseen.count_times_question_seen == 0
        assert nq_oldest_due_or_unseen.count_questions_due == COUNT_QUESTIONS_DUE
        assert nq_oldest_due_or_unseen.count_questions_tagged == COUNT_QUESTIONS_WITH_TAG
        assert nq_oldest_due_or_unseen.count_questions_unseen == COUNT_QUESTIONS_UNSEEN
        assert nq_oldest_due_or_unseen.count_recent_seen_mins_30 == COUNT_RECENT_SEEN_MINS_30
        assert nq_oldest_due_or_unseen.count_recent_seen_mins_60 == COUNT_RECENT_SEEN_MINS_60
        assert nq_oldest_due_or_unseen.tag_names_for_question == [tag1.name]
        assert nq_oldest_due_or_unseen.tag_names_selected == TAG_NAMES_COMMON
        
        # Test QUERY_OLDEST_DUE_OR_UNSEEN_BY_TAG (odoubt)
        nq_odoubt = NextQuestion(query_name=QUERY_OLDEST_DUE_OR_UNSEEN_BY_TAG, tag_ids_selected=TAG_IDS_COMMON, user=user)
        assert nq_odoubt.oldest_viewed_tag == tag2
        assert nq_odoubt.question == q2_unseen_newer
        assert nq_odoubt.count_times_question_seen == 0
        assert nq_odoubt.count_questions_due == COUNT_QUESTIONS_DUE
        assert nq_odoubt.count_questions_tagged == COUNT_QUESTIONS_WITH_TAG
        assert nq_odoubt.count_questions_unseen == COUNT_QUESTIONS_UNSEEN
        assert nq_odoubt.count_recent_seen_mins_30 == COUNT_RECENT_SEEN_MINS_30
        assert nq_odoubt.count_recent_seen_mins_60 == COUNT_RECENT_SEEN_MINS_60
        assert nq_odoubt.tag_names_for_question == [tag2.name]
        assert nq_odoubt.tag_names_selected == TAG_NAMES_COMMON
        
        # Test QUERY_UNSEEN_BY_OLDEST_VIEWED_TAG
        nq_unseen_by_tag = NextQuestion(query_name=QUERY_UNSEEN_BY_OLDEST_VIEWED_TAG, tag_ids_selected=TAG_IDS_COMMON, user=user)
        assert nq_odoubt.oldest_viewed_tag == tag2
        assert nq_unseen_by_tag.question == q2_unseen_newer
        assert nq_unseen_by_tag.count_times_question_seen == 0
        assert nq_unseen_by_tag.count_questions_due == COUNT_QUESTIONS_DUE
        assert nq_unseen_by_tag.count_questions_tagged == COUNT_QUESTIONS_WITH_TAG
        assert nq_unseen_by_tag.count_questions_unseen == COUNT_QUESTIONS_UNSEEN
        assert nq_unseen_by_tag.count_recent_seen_mins_30 == COUNT_RECENT_SEEN_MINS_30
        assert nq_unseen_by_tag.count_recent_seen_mins_60 == COUNT_RECENT_SEEN_MINS_60
        assert nq_unseen_by_tag.tag_names_for_question == [tag2.name]
        assert nq_unseen_by_tag.tag_names_selected == TAG_NAMES_COMMON
        
        # All actual nq_* questions returned by all queries above:
        #   nq_unseen                 == q1_unseen_older
        #   nq_unseen_then_oldest_due == q1_unseen_older
        #   nq_oldest_due_or_unseen   == q1_unseen_older
        #   nq_odoubt                 == q2_unseen_newer
        #   nq_unseen_by_tag          == q2_unseen_newer
        #   nq_oldest_due             == q3_oldest_due
        #   nq_reinforce              == q4_reinforce_newer
        #   nq_future                 == q6_future_oldest_due

        # Verify same and different groups of results

        # same: q1
        assert (nq_unseen.question ==
                nq_unseen_then_oldest_due.question ==
                nq_oldest_due_or_unseen.question
        )

        # same: q2
        assert (nq_odoubt.question == 
                nq_unseen_by_tag.question)

        # different: q1, q2, q3, q4, q5, q6
        assert (   nq_unseen.question # q1
                != nq_odoubt.question # q2
                != nq_oldest_due.question # q3
                != nq_reinforce.question # q4
                != nq_future.question # q6
        )

        ############################################################
        # # Test QUERY_UNSEEN_THEN_OLDEST_DUE, no unseen
        ############################################################
        nq_unseen_then_oldest_due = NextQuestion(query_name=QUERY_UNSEEN_THEN_OLDEST_DUE, tag_ids_selected=[TAG5_DUE_ONLY.id], user=user)
        assert nq_unseen_then_oldest_due.question == q15_tag5_due_nm
        assert nq_unseen_then_oldest_due.count_times_question_seen == 1
        assert nq_unseen_then_oldest_due.count_questions_due == 1
        assert nq_unseen_then_oldest_due.count_questions_tagged == 1
        assert nq_unseen_then_oldest_due.count_questions_unseen == 0
        assert nq_unseen_then_oldest_due.count_recent_seen_mins_30 == COUNT_RECENT_SEEN_MINS_30
        assert nq_unseen_then_oldest_due.count_recent_seen_mins_60 == COUNT_RECENT_SEEN_MINS_60
        assert nq_unseen_then_oldest_due.tag_names_for_question == [TAG5_DUE_ONLY.name]
        assert nq_unseen_then_oldest_due.tag_names_selected == [TAG5_DUE_ONLY.name]
        
        ############################################################
        # Test QUERY_OLDEST_DUE_OR_UNSEEN picks oldest due when unseen.Question.added > oldest_due.Schedule.next
        ############################################################
        tag_ids_selected = [tag5_due.id, tag6_unseen.id]
        tag_names_selected = sorted([tag5_due.name, tag6_unseen.name])
        nq_oldest_due_or_unseen = NextQuestion(query_name=QUERY_OLDEST_DUE_OR_UNSEEN, tag_ids_selected=tag_ids_selected, user=user)
        assert nq_oldest_due_or_unseen.question == q15_tag5_due_nm
        assert nq_oldest_due_or_unseen.count_times_question_seen == 1
        assert nq_oldest_due_or_unseen.count_questions_due == 1
        assert nq_oldest_due_or_unseen.count_questions_tagged == 2
        assert nq_oldest_due_or_unseen.count_questions_unseen == 1
        assert nq_oldest_due_or_unseen.count_recent_seen_mins_30 == COUNT_RECENT_SEEN_MINS_30
        assert nq_oldest_due_or_unseen.count_recent_seen_mins_60 == COUNT_RECENT_SEEN_MINS_60
        assert nq_oldest_due_or_unseen.tag_names_for_question == [tag5_due.name]
        assert nq_oldest_due_or_unseen.tag_names_selected == tag_names_selected

        ############################################################
        # NextQuestion queries with the different tag_ids_selected, where each should return a None question
        ############################################################

        # Test QUERY_OLDEST_DUE picks None
        nq_oldest_due_None = NextQuestion(query_name=QUERY_OLDEST_DUE, tag_ids_selected=[TAG6_UNSEEN_ONLY.id, tag4_no_questions.id], user=user)
        assert nq_oldest_due_None.question is None
        assert nq_oldest_due_None.count_times_question_seen == 0
        assert nq_oldest_due_None.count_questions_due == 0
        assert nq_oldest_due_None.count_questions_tagged == 1
        assert nq_oldest_due_None.count_questions_unseen == 1
        assert nq_oldest_due_None.count_recent_seen_mins_30 == COUNT_RECENT_SEEN_MINS_30
        assert nq_oldest_due_None.count_recent_seen_mins_60 == COUNT_RECENT_SEEN_MINS_60
        assert nq_oldest_due_None.tag_names_for_question == []
        assert nq_oldest_due_None.tag_names_selected == sorted([TAG6_UNSEEN_ONLY.name, tag4_no_questions.name])
        
        # Test QUERY_UNSEEN picks None
        nq_unseen_none = NextQuestion(query_name=QUERY_UNSEEN, tag_ids_selected=[TAG5_DUE_ONLY.id], user=user)
        assert nq_unseen_none.question is None
        assert nq_unseen_none.count_times_question_seen == 0
        assert nq_unseen_none.count_questions_due == 1
        assert nq_unseen_none.count_questions_tagged == 1
        assert nq_unseen_none.count_questions_unseen == 0
        assert nq_unseen_none.count_recent_seen_mins_30 == COUNT_RECENT_SEEN_MINS_30
        assert nq_unseen_none.count_recent_seen_mins_60 == COUNT_RECENT_SEEN_MINS_60
        assert nq_unseen_none.tag_names_for_question == []
        assert nq_unseen_none.tag_names_selected == [TAG5_DUE_ONLY.name]

        # Test QUERY_UNSEEN_THEN_OLDEST_DUE picks None
        nq_unseen_then_oldest_due = NextQuestion(query_name=QUERY_UNSEEN_THEN_OLDEST_DUE, tag_ids_selected=[TAG7_DUE_FUTURE_ONLY.id], user=user)
        assert nq_unseen_then_oldest_due.question is None
        assert nq_unseen_then_oldest_due.count_times_question_seen == 0
        assert nq_unseen_then_oldest_due.count_questions_due == 0
        assert nq_unseen_then_oldest_due.count_questions_tagged == 1
        assert nq_unseen_then_oldest_due.count_questions_unseen == 0
        assert nq_unseen_then_oldest_due.count_recent_seen_mins_30 == COUNT_RECENT_SEEN_MINS_30
        assert nq_unseen_then_oldest_due.count_recent_seen_mins_60 == COUNT_RECENT_SEEN_MINS_60
        assert nq_unseen_then_oldest_due.tag_names_for_question == []
        assert nq_unseen_then_oldest_due.tag_names_selected == [TAG7_DUE_FUTURE_ONLY.name]
        
        # Test QUERY_FUTURE picks None
        tag_ids_selected = [tag4_no_questions.id, tag5_due.id]
        tag_names_selected = sorted([tag4_no_questions.name, tag5_due.name])
        nq_future = NextQuestion(query_name=QUERY_FUTURE, tag_ids_selected=tag_ids_selected, user=user)
        assert nq_future.question is None
        assert nq_future.count_times_question_seen == 0
        assert nq_future.count_questions_due == 1
        assert nq_future.count_questions_tagged == 1
        assert nq_future.count_questions_unseen == 0
        assert nq_future.count_recent_seen_mins_30 == COUNT_RECENT_SEEN_MINS_30
        assert nq_future.count_recent_seen_mins_60 == COUNT_RECENT_SEEN_MINS_60
        assert nq_future.tag_names_for_question == []
        assert nq_future.tag_names_selected == tag_names_selected
        
        # Test QUERY_REINFORCE picks None
        tag_ids_selected = [tag4_no_questions.id, tag6_unseen.id, tag7_due_future.id]
        tag_names_selected = sorted([tag4_no_questions.name, tag6_unseen.name, tag7_due_future.name])
        nq_reinforce = NextQuestion(query_name=QUERY_REINFORCE, tag_ids_selected=tag_ids_selected, user=user)
        assert nq_reinforce.question is None
        assert nq_reinforce.count_times_question_seen == 0
        assert nq_reinforce.count_questions_due == 0
        assert nq_reinforce.count_questions_tagged == 2
        assert nq_reinforce.count_questions_unseen == 1
        assert nq_reinforce.count_recent_seen_mins_30 == COUNT_RECENT_SEEN_MINS_30
        assert nq_reinforce.count_recent_seen_mins_60 == COUNT_RECENT_SEEN_MINS_60
        assert nq_reinforce.tag_names_for_question == []
        assert nq_reinforce.tag_names_selected == tag_names_selected

        # Test QUERY_OLDEST_DUE_OR_UNSEEN picks None
        tag_ids_selected = [tag4_no_questions.id]
        tag_names_selected = sorted([tag4_no_questions.name])
        nq_oldest_due_or_unseen = NextQuestion(query_name=QUERY_OLDEST_DUE_OR_UNSEEN, tag_ids_selected=tag_ids_selected, user=user)
        assert nq_oldest_due_or_unseen.question is None
        assert nq_oldest_due_or_unseen.count_times_question_seen == 0
        assert nq_oldest_due_or_unseen.count_questions_due == 0
        assert nq_oldest_due_or_unseen.count_questions_tagged == 0
        assert nq_oldest_due_or_unseen.count_questions_unseen == 0
        assert nq_oldest_due_or_unseen.count_recent_seen_mins_30 == COUNT_RECENT_SEEN_MINS_30
        assert nq_oldest_due_or_unseen.count_recent_seen_mins_60 == COUNT_RECENT_SEEN_MINS_60
        assert nq_oldest_due_or_unseen.tag_names_for_question == []
        assert nq_oldest_due_or_unseen.tag_names_selected == tag_names_selected

        # Test QUERY_UNSEEN_BY_OLDEST_VIEWED_TAG picks None
        tag_ids_selected = [tag4_no_questions.id]
        tag_names_selected = sorted([tag4_no_questions.name])
        nq_unseen_by_tag = NextQuestion(query_name=QUERY_UNSEEN_BY_OLDEST_VIEWED_TAG, tag_ids_selected=tag_ids_selected, user=user)
        assert nq_unseen_by_tag.question is None
        assert nq_unseen_by_tag.count_times_question_seen == 0
        assert nq_unseen_by_tag.count_questions_due == 0
        assert nq_unseen_by_tag.count_questions_tagged == 0
        assert nq_unseen_by_tag.count_questions_unseen == 0
        assert nq_unseen_by_tag.count_recent_seen_mins_30 == COUNT_RECENT_SEEN_MINS_30
        assert nq_unseen_by_tag.count_recent_seen_mins_60 == COUNT_RECENT_SEEN_MINS_60
        assert nq_unseen_by_tag.tag_names_for_question == []
        assert nq_unseen_by_tag.tag_names_selected == tag_names_selected

class TestQueryUnseenByOldestViewedTag:
    def test_get_nq_unseen_by_oldest_viewed_tag(self, user):
        tag1 = Tag.objects.create(name="tag1", user=user)
        tag2 = Tag.objects.create(name="tag2", user=user)
        tag3 = Tag.objects.create(name="tag3", user=user)

        q1 = Question.objects.create(question="Q1", user=user)
        q2 = Question.objects.create(question="Q2", user=user)
        q3 = Question.objects.create(question="Q3", user=user)
        q4 = Question.objects.create(question="Q4", user=user)

        QuestionTag.objects.create(question=q1, tag=tag1)
        QuestionTag.objects.create(question=q2, tag=tag2)
        QuestionTag.objects.create(question=q3, tag=tag3)
        QuestionTag.objects.create(question=q4, tag=tag1)

        Schedule.objects.create(user=user, question=q1, datetime_added=timezone.now() - timezone.timedelta(days=3))
        Schedule.objects.create(user=user, question=q2, datetime_added=timezone.now() - timezone.timedelta(days=2))

        nq = NextQuestion(query_name=QUERY_UNSEEN_BY_OLDEST_VIEWED_TAG, tag_ids_selected=[tag1.id, tag2.id, tag3.id], user=user)

        assert nq.question == q3
        assert nq.count_questions_tagged == 4
        assert nq.count_questions_unseen == 2
        assert nq.tag_names_for_question == [tag3.name]
        assert set(nq.tag_names_selected) == set([tag1.name, tag2.name, tag3.name])

    def test_get_nq_unseen_by_oldest_viewed_tag_no_schedules(self, user):
        tag1 = Tag.objects.create(name="tag1", user=user)
        tag2 = Tag.objects.create(name="tag2", user=user)

        q1 = Question.objects.create(question="Q1", user=user)
        q2 = Question.objects.create(question="Q2", user=user)

        QuestionTag.objects.create(question=q1, tag=tag1)
        QuestionTag.objects.create(question=q2, tag=tag2)

        nq = NextQuestion(query_name=QUERY_UNSEEN_BY_OLDEST_VIEWED_TAG, tag_ids_selected=[tag1.id, tag2.id], user=user)

        assert nq.question == q1
        assert nq.count_questions_tagged == 2
        assert nq.count_questions_unseen == 2
        assert nq.tag_names_for_question == [tag1.name]
        assert set(nq.tag_names_selected) == set([tag1.name, tag2.name])

    def test_get_nq_unseen_by_oldest_viewed_tag_mixed_schedules(self, user):
        tag1 = Tag.objects.create(name="tag1", user=user)
        tag2 = Tag.objects.create(name="tag2", user=user)  # q2, q5
        tag3 = Tag.objects.create(name="tag3", user=user)  # q3, q4

        q1_tag1 = Question.objects.create(question="Q1", user=user) # newest seen/due
        q2_tag2 = Question.objects.create(question="Q2", user=user) # oldest last-viewed-time unseen
        q3_oldest_tag3 = Question.objects.create(question="Q3", user=user) # oldest unseen for tag3
        q4_tag3 = Question.objects.create(question="Q4", user=user)
        q5_tag2 = Question.objects.create(question="Q5", user=user) # newest last-viewed-time unseen for tag2

        QuestionTag.objects.create(question=q1_tag1, tag=tag1)  # oldest seen/due
        QuestionTag.objects.create(question=q2_tag2, tag=tag2)
        QuestionTag.objects.create(question=q3_oldest_tag3, tag=tag3)
        QuestionTag.objects.create(question=q4_tag3, tag=tag3)
        QuestionTag.objects.create(question=q5_tag2, tag=tag2)

        # q1_tag1 has have an older schedule than the other unseen questions.dateadded
        schedule = Schedule.objects.create(user=user, question=q1_tag1, datetime_added=timezone.now() - timezone.timedelta(weeks=999))

        nq = NextQuestion(query_name=QUERY_UNSEEN_BY_OLDEST_VIEWED_TAG, tag_ids_selected=[tag1.id, tag2.id, tag3.id], user=user)

        # q1_tag1 is the oldest tag (per the schedule.dateadded),
        # but it has no unseen questions.  
        # tag2's newest last-viewed-time unseen is q5_tag2,
        # which is newer than tag3's q3,
        # therefore, tag3 is the oldest viewed tag.
        # tag3's q3_oldest_tag3 is q4_tag3,
        # therefore, q3_oldest_tag3 is the next question.
        assert nq.oldest_viewed_tag == tag3
        assert nq.question == q3_oldest_tag3
        assert schedule.datetime_added > q4_tag3.datetime_added
        assert q5_tag2.datetime_added > q4_tag3.datetime_added
        assert q3_oldest_tag3.datetime_added < q4_tag3.datetime_added
        assert nq.count_questions_tagged == 5
        assert nq.count_questions_unseen == 4
        assert nq.tag_names_for_question == [tag3.name]
        assert set(nq.tag_names_selected) == set([tag1.name, tag2.name, tag3.name])

    def test_get_nq_unseen_by_oldest_viewed_tag_all_seen(self, user):
        tag1 = Tag.objects.create(name="tag1", user=user)
        tag2 = Tag.objects.create(name="tag2", user=user)

        q1 = Question.objects.create(question="Q1", user=user)
        q2 = Question.objects.create(question="Q2", user=user)

        QuestionTag.objects.create(question=q1, tag=tag1)
        QuestionTag.objects.create(question=q2, tag=tag2)

        Schedule.objects.create(user=user, question=q1, datetime_added=timezone.now() - timezone.timedelta(days=2))
        Schedule.objects.create(user=user, question=q2, datetime_added=timezone.now() - timezone.timedelta(days=1))

        nq = NextQuestion(query_name=QUERY_UNSEEN_BY_OLDEST_VIEWED_TAG, tag_ids_selected=[tag1.id, tag2.id], user=user)

        assert nq.question is None
        assert nq.count_questions_tagged == 2
        assert nq.count_questions_unseen == 0
        assert nq.tag_names_for_question == []
        assert set(nq.tag_names_selected) == set([tag1.name, tag2.name])

    def test_get_nq_unseen_by_oldest_viewed_tag_multiple_questions_per_tag(self, user):
        tag1 = Tag.objects.create(name="tag1", user=user)
        tag2 = Tag.objects.create(name="tag2", user=user)

        q1 = Question.objects.create(question="Q1", user=user)
        q2 = Question.objects.create(question="Q2", user=user)
        q3 = Question.objects.create(question="Q3", user=user)
        q4 = Question.objects.create(question="Q4", user=user)

        QuestionTag.objects.create(question=q1, tag=tag1)
        QuestionTag.objects.create(question=q2, tag=tag1)
        QuestionTag.objects.create(question=q3, tag=tag2)
        QuestionTag.objects.create(question=q4, tag=tag2)

        Schedule.objects.create(user=user, question=q1, datetime_added=timezone.now() - timezone.timedelta(days=3))
        Schedule.objects.create(user=user, question=q3, datetime_added=timezone.now() - timezone.timedelta(days=2))

        nq = NextQuestion(query_name=QUERY_UNSEEN_BY_OLDEST_VIEWED_TAG, tag_ids_selected=[tag1.id, tag2.id], user=user)

        assert nq.question == q2
        assert nq.count_questions_tagged == 4
        assert nq.count_questions_unseen == 2
        assert nq.tag_names_for_question == [tag1.name]
        assert set(nq.tag_names_selected) == set([tag1.name, tag2.name])

class TestOldestDueOrUnseen:
    def test_get_next_question_oldest_due_or_unseen_by_tag(self, user):
        # Create test user and tags
        tag1_due = Tag.objects.create(name="tag1", user=user)
        tag2_unseen = Tag.objects.create(name="tag2", user=user)
        tag3_none = Tag.objects.create(name="tag3", user=user)
        
        q1_tag1 = Question.objects.create(
            user=user,
            question="Q1"
        )
        q1_tag1.datetime_added = timezone.now() - timezone.timedelta(weeks=99)
        q1_tag1.save()
        q1_tag1.questiontag_set.create(tag=tag1_due)
        
        q2_tag2 = Question.objects.create(
            user=user,
            question="Q2"
        )
        q2_tag2.datetime_added = timezone.now() - timezone.timedelta(weeks=55)
        q2_tag2.save()
        q2_tag2.questiontag_set.create(tag=tag2_unseen)
        
        q1_tag1_sched = Schedule.objects.create(
            question=q1_tag1,
            user=user,
            date_show_next=timezone.now() - timezone.timedelta(weeks=99)
        )
        q1_tag1_sched.datetime_added = timezone.now() - timezone.timedelta(weeks=11)
        q1_tag1_sched.save()
        
        # assert: tag2/q2 datetime_added=-55w is older than tag1/q1 Sched.datetime_added=-11w 
        assert q1_tag1_sched.datetime_added > q2_tag2.datetime_added  # -11w > -55w

        nq = NextQuestion(
            query_name=QUERY_OLDEST_DUE_OR_UNSEEN_BY_TAG,
            tag_ids_selected=[tag1_due.id, tag2_unseen.id, tag3_none.id],
            user=user
        )
        assert nq.oldest_viewed_tag == tag2_unseen
        assert nq.question == q2_tag2

        nq = NextQuestion(
            query_name=QUERY_UNSEEN_BY_OLDEST_VIEWED_TAG,
            tag_ids_selected=[tag1_due.id, tag2_unseen.id, tag3_none.id],
            user=user
        )
        assert nq.oldest_viewed_tag == tag2_unseen
        assert nq.question == q2_tag2
        
        # Now reverse them
        q2_tag2.datetime_added = timezone.now() - timezone.timedelta(weeks=22)
        q2_tag2.save()
        q1_tag1_sched.datetime_added = timezone.now() - timezone.timedelta(weeks=55)
        q1_tag1_sched.date_show_next = timezone.now() - timezone.timedelta(weeks=0)
        q1_tag1_sched.save()
        # assert: tag2/q2 datetime_added=-22w is newer than tag1/q1 Sched.datetime_added=-55w 
        assert q2_tag2.datetime_added > q1_tag1_sched.datetime_added  # -22w < -55w
        nq = NextQuestion(
            query_name=QUERY_OLDEST_DUE_OR_UNSEEN_BY_TAG,
            tag_ids_selected=[tag1_due.id, tag2_unseen.id, tag3_none.id],
            user=user
        )
        assert nq.oldest_viewed_tag == tag1_due
        assert nq.question == q1_tag1

        # Still the same results for QUERY_UNSEEN_BY_OLDEST_VIEWED_TAG, because tag1_due has no unseen questions
        nq = NextQuestion(
            query_name=QUERY_UNSEEN_BY_OLDEST_VIEWED_TAG,
            tag_ids_selected=[tag1_due.id, tag2_unseen.id, tag3_none.id],
            user=user
        )
        assert nq.oldest_viewed_tag == tag2_unseen
        assert nq.question == q2_tag2
        
        
### TODO: add a test for QUERY_UNSEEN_BY_OLDEST_VIEWED_TAG and QUERY_OLDEST_DUE_OR_UNSEEN_BY_TAG where there's:
### 1. tag1_none   with no questions
### 2. tag2_due    with only due questions, and the oldest due question is older than the oldest tag3_unseen question
### 3. tag3_unseen with only unseen questions, and the oldest unseen question is newer than the oldest tag2_due question
### 4. tag4_both   with both due and unseen questions, and the oldest due question is newer than the oldest tag3_unseen question