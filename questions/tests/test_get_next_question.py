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
from questions.models import Question, Tag, TagLineage, QuestionTag, Schedule
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
        QuestionTag.objects.create(question=question, tag=tag)
        
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
        # Ideally, we want to submit different QUERY_*'s with the same data (shown in the table below) and same tags
        # (TAG_IDS_SELECTED), and show that each query returns a different question.  The exception to this is the following
        # combination, which will always return the same question for given tag(s):
        #   QUERY_UNSEEN == QUERY_UNSEEN_THEN_OLDEST_DUE == QUERY_OLDEST_DUE_OR_UNSEEN

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
####        # | q18_tag8_oldest_viewed  | u1 | tag8      | -99w   | -88w       | -1s       | oldest viewed; q18.Sched.added > q19.Q.added
####        # | q19_tag8_newer_unseen   | u1 | tag8      | -1s    | (none)     | (none)    | to test UNSEEN_THEN_OLDEST with no matches
        
        # Types of questions each tag has:
        # --------------------------------
        # tag1: due, due_future, unseen
        # tag2: due, due_future, unseen
        # tag3: due, due_future, unseen
        # tag4: (no questions)
        # tag5: due        (to test QUERY_UNSEEN_THEN_OLDEST_DUE no unseen; and also to test several queries that pick None)
        # tag6: unseen     (to test several queries that pick None)
        # tag7: due_future (to test several queries that pick None)
        # tag8: oldest_viewed (NOT IMPLEMENTED YET)
        
        # tag5, tag6, tag7 are used to test:
        #     QUERY_UNSEEN_THEN_OLDEST_DUE
        #     picking None for various queries
        
        # Tags matching queries:
        # ----------------------
        # q1_unseen_older      (QUERY_UNSEEN)     (QUERY_UNSEEN_THEN_OLDEST_DUE)
        # q3_oldest_due        (QUERY_OLDEST_DUE) (QUERY_OLDEST_DUE_OR_UNSEEN)
        # q4_reinforce_newer   (QUERY_REINFORCE)
        # q6_future_oldest_due (QUERY_FUTURE)
        # q9_unseen_by_tag3    (QUERY_UNSEEN_BY_OLDEST_VIEWED_TAG)
        # q18_tag8_oldest_viewed
        
        # Overlapping queries:
        # --------------------
        #  QUERY_UNSEEN == QUERY_UNSEEN_THEN_OLDEST_DUE == QUERY_OLDEST_DUE_OR_UNSEEN

        
        # For by oldest-viewed tag (QUERY_UNSEEN_BY_OLDEST_VIEWED_TAG), create questions such that:
        #   Instead of selecting q1, it selects an unseen question with a different tag that has a newer Question.added, but that tag has a question with an older Schedule.datetime_added than Q1.Schedule.datetime_added
        # For QUERY_OLDEST_DUE_OR_UNSEEN, create questions such that:
        #   Instead of selecting qx, it selects qy, a question that has been seen, where qy.Schedule.datetime_added is older than
        #   qx.dateetime_added (which will be equivalent to QUERY_OLDEST_DUE)
        
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
####        q18_tag8_oldest_viewed = Question.objects.create(question="Question 18: oldest viewed, tag8", user=user)
####        q19_tag8_newer_unseen = Question.objects.create(question="Question 19: newer unseen, tag8", user=user)
        
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
####        q18_tag8_oldest_viewed.datetime_added = timezone.now() - timezone.timedelta(weeks=99)
####        q19_tag8_newer_unseen.datetime_added = timezone.now() - timezone.timedelta(seconds=1)
        
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
####        q18_tag8_oldest_viewed.save()
####        q19_tag8_newer_unseen.save()
    
        tag1 = tag
        tag2 = Tag.objects.create(name="tag 2", user=user)
        tag3 = Tag.objects.create(name="tag 3", user=user)
        tag4_no_questions = Tag.objects.create(name="tag 4 no questions", user=user)
        tag5_due = Tag.objects.create(name="tag 5 due", user=user)
        tag6_unseen = Tag.objects.create(name="tag 6 unseen", user=user)
        tag7_due_future = Tag.objects.create(name="tag 7 due future", user=user)
####        tag8_odoubt = Tag.objects.create(name="tag 8 odoubt", user=user)
        
####        TagLineage.objects.create(parent_tag=tag4_no_questions, child_tag=tag8_odoubt, user=user)

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
####        QuestionTag.objects.create(question=q18_tag8_oldest_viewed, tag=tag8_odoubt)
####        QuestionTag.objects.create(question=q19_tag8_newer_unseen, tag=tag8_odoubt)

        COUNT_QUESTIONS_WITH_TAG = 10
        COUNT_QUESTIONS_UNSEEN = 4
####        COUNT_QUESTIONS_UNSEEN_BY_OLDEST_VIEWED_TAG = 4 # (1 each for tag1, tag2, tag3, tag8)
        COUNT_QUESTIONS_UNSEEN_BY_OLDEST_VIEWED_TAG = 3 # (1 each for tag1, tag2, tag3)
####        COUNT_QUESTIONS_DUE = 4 # q3, q4, q5, q18 (not q8)
        COUNT_QUESTIONS_DUE = 3 # q3, q4, q5 (not q8)
        COUNT_QUESTIONS_OLDEST_DUE_OR_UNSEEN_BY_TAG = COUNT_QUESTIONS_DUE
        COUNT_QUESTIONS_REINFORCE = COUNT_QUESTIONS_DUE
        COUNT_QUESTIONS_UNSEEN_AND_DUE = COUNT_QUESTIONS_DUE + COUNT_QUESTIONS_UNSEEN
        COUNT_QUESTIONS_FUTURE = 3
        COUNT_RECENT_SEEN_MINS_30 = 5  # Sched.added q5, q6.a, q7, q8
        COUNT_RECENT_SEEN_MINS_60 = COUNT_RECENT_SEEN_MINS_30 + 2  # Sched.added q6, q15

        TAG_IDS_ALL = [tag1.id, tag2.id, tag3.id, tag4_no_questions.id]
####        TAG_IDS_ALL = [tag1.id, tag2.id, tag3.id, tag4_no_questions.id, tag8_odoubt.id]
        TAG3_NAME = tag3.name
        TAG_NAMES_ALL = [tag1.name, tag2.name, tag3.name, tag4_no_questions.name]
        TAG_NAMES_SELECTED = TAG_NAMES_ALL
        TAG_IDS_SELECTED = TAG_IDS_ALL
        TAG_NAMES_Q6_FUTURE_OLDEST_DUE = [tag1.name, tag2.name]
        TAG5_DUE_ONLY = tag5_due
        TAG6_UNSEEN_ONLY = tag6_unseen
        TAG7_DUE_FUTURE_ONLY = tag7_due_future
####        TAG_NAMES_Q18_TAG8_OLDEST_VIEWED = [tag8_odoubt.name]
    
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
        nq_oldest_due = NextQuestion(query_name=QUERY_OLDEST_DUE, tag_ids_selected=TAG_IDS_SELECTED, user=user)
        assert nq_oldest_due.question == q3_oldest_due
        assert nq_oldest_due.count_times_question_seen == 1
        assert nq_oldest_due.count_questions_due == COUNT_QUESTIONS_DUE
        assert nq_oldest_due.count_questions_matched_criteria == COUNT_QUESTIONS_DUE
        assert nq_oldest_due.count_questions_tagged == COUNT_QUESTIONS_WITH_TAG
        assert nq_oldest_due.count_questions_unseen == COUNT_QUESTIONS_UNSEEN
        assert nq_oldest_due.count_recent_seen_mins_30 == COUNT_RECENT_SEEN_MINS_30
        assert nq_oldest_due.count_recent_seen_mins_60 == COUNT_RECENT_SEEN_MINS_60
        assert nq_oldest_due.tag_names_for_question == [TAG_NAME]
        assert nq_oldest_due.tag_names_selected == TAG_NAMES_SELECTED
    
        # Test QUERY_UNSEEN
        nq_unseen = NextQuestion(query_name=QUERY_UNSEEN, tag_ids_selected=TAG_IDS_SELECTED, user=user)
        assert nq_unseen.question == q1_unseen_older
        assert nq_unseen.count_times_question_seen == 0
        assert nq_unseen.count_questions_due == COUNT_QUESTIONS_DUE
        assert nq_unseen.count_questions_matched_criteria == COUNT_QUESTIONS_UNSEEN
        assert nq_unseen.count_questions_tagged == COUNT_QUESTIONS_WITH_TAG
        assert nq_unseen.count_questions_unseen == COUNT_QUESTIONS_UNSEEN
        assert nq_unseen.count_recent_seen_mins_30 == COUNT_RECENT_SEEN_MINS_30
        assert nq_unseen.count_recent_seen_mins_60 == COUNT_RECENT_SEEN_MINS_60
        assert nq_unseen.tag_names_for_question == [TAG_NAME]
        assert nq_unseen.tag_names_selected == TAG_NAMES_SELECTED

        # Test QUERY_UNSEEN_THEN_OLDEST_DUE
        nq_unseen_then_oldest_due = NextQuestion(query_name=QUERY_UNSEEN_THEN_OLDEST_DUE, tag_ids_selected=TAG_IDS_SELECTED, user=user)
        assert nq_unseen_then_oldest_due.question == q1_unseen_older
        assert nq_unseen_then_oldest_due.count_times_question_seen == 0
        assert nq_unseen_then_oldest_due.count_questions_due == COUNT_QUESTIONS_DUE
        assert nq_unseen_then_oldest_due.count_questions_matched_criteria == COUNT_QUESTIONS_UNSEEN_AND_DUE
        assert nq_unseen_then_oldest_due.count_questions_tagged == COUNT_QUESTIONS_WITH_TAG
        assert nq_unseen_then_oldest_due.count_questions_unseen == COUNT_QUESTIONS_UNSEEN
        assert nq_unseen_then_oldest_due.count_recent_seen_mins_30 == COUNT_RECENT_SEEN_MINS_30
        assert nq_unseen_then_oldest_due.count_recent_seen_mins_60 == COUNT_RECENT_SEEN_MINS_60
        assert nq_unseen_then_oldest_due.tag_names_for_question == [TAG_NAME]
        assert nq_unseen_then_oldest_due.tag_names_selected == TAG_NAMES_SELECTED
        
        # Test QUERY_FUTURE
        nq_future = NextQuestion(query_name=QUERY_FUTURE, tag_ids_selected=TAG_IDS_SELECTED, user=user)
        assert nq_future.question == q6_future_oldest_due
        assert nq_future.count_times_question_seen == 2
        assert nq_future.count_questions_due == COUNT_QUESTIONS_DUE
        assert nq_future.count_questions_matched_criteria == COUNT_QUESTIONS_FUTURE
        assert nq_future.count_questions_tagged == COUNT_QUESTIONS_WITH_TAG
        assert nq_future.count_questions_unseen == COUNT_QUESTIONS_UNSEEN
        assert nq_future.count_recent_seen_mins_30 == COUNT_RECENT_SEEN_MINS_30
        assert nq_future.count_recent_seen_mins_60 == COUNT_RECENT_SEEN_MINS_60
        assert nq_future.tag_names_for_question == TAG_NAMES_Q6_FUTURE_OLDEST_DUE
        assert nq_future.tag_names_selected == TAG_NAMES_SELECTED
        
        # Test QUERY_REINFORCE
        nq_reinforce = NextQuestion(query_name=QUERY_REINFORCE, tag_ids_selected=TAG_IDS_SELECTED, user=user)
        assert nq_reinforce.question == q4_reinforce_newer
        assert nq_reinforce.count_times_question_seen == 1
        assert nq_reinforce.count_questions_due == COUNT_QUESTIONS_DUE
        assert nq_reinforce.count_questions_matched_criteria == COUNT_QUESTIONS_REINFORCE
        assert nq_reinforce.count_questions_tagged == COUNT_QUESTIONS_WITH_TAG
        assert nq_reinforce.count_questions_unseen == COUNT_QUESTIONS_UNSEEN
        assert nq_reinforce.count_recent_seen_mins_30 == COUNT_RECENT_SEEN_MINS_30
        assert nq_reinforce.count_recent_seen_mins_60 == COUNT_RECENT_SEEN_MINS_60
        assert nq_reinforce.tag_names_for_question == [TAG_NAME]
        assert nq_reinforce.tag_names_selected == TAG_NAMES_SELECTED

        # Test QUERY_OLDEST_DUE_OR_UNSEEN  (same results as QUERY_UNSEEN)
        nq_oldest_due_or_unseen = NextQuestion(query_name=QUERY_OLDEST_DUE_OR_UNSEEN, tag_ids_selected=TAG_IDS_SELECTED, user=user)
        assert nq_oldest_due_or_unseen.question == q1_unseen_older
        assert nq_oldest_due_or_unseen.count_times_question_seen == 0
        assert nq_oldest_due_or_unseen.count_questions_due == COUNT_QUESTIONS_DUE
        assert nq_oldest_due_or_unseen.count_questions_matched_criteria == COUNT_QUESTIONS_WITH_TAG
        assert nq_oldest_due_or_unseen.count_questions_tagged == COUNT_QUESTIONS_WITH_TAG
        assert nq_oldest_due_or_unseen.count_questions_unseen == COUNT_QUESTIONS_UNSEEN
        assert nq_oldest_due_or_unseen.count_recent_seen_mins_30 == COUNT_RECENT_SEEN_MINS_30
        assert nq_oldest_due_or_unseen.count_recent_seen_mins_60 == COUNT_RECENT_SEEN_MINS_60
        assert nq_oldest_due_or_unseen.tag_names_for_question == [tag1.name]
        assert nq_oldest_due_or_unseen.tag_names_selected == TAG_NAMES_SELECTED
        
        # Test QUERY_OLDEST_DUE_OR_UNSEEN_BY_TAG (odoubt)
#####        nq_odoubt = NextQuestion(query_name=QUERY_OLDEST_DUE_OR_UNSEEN_BY_TAG, tag_ids_selected=TAG_IDS_SELECTED, user=user)
#####        assert nq_odoubt.question == q18_tag8_oldest_viewed
#####        assert nq_odoubt.count_times_question_seen == 1
#####        assert nq_odoubt.count_questions_due == COUNT_QUESTIONS_DUE
#####        assert nq_odoubt.count_questions_matched_criteria == COUNT_QUESTIONS_OLDEST_DUE_OR_UNSEEN_BY_TAG
#####        assert nq_odoubt.count_questions_tagged == COUNT_QUESTIONS_WITH_TAG
#####        assert nq_odoubt.count_questions_unseen == COUNT_QUESTIONS_UNSEEN
#####        assert nq_odoubt.count_recent_seen_mins_30 == COUNT_RECENT_SEEN_MINS_30
#####        assert nq_odoubt.count_recent_seen_mins_60 == COUNT_RECENT_SEEN_MINS_60
#####        assert nq_odoubt.tag_names_for_question == TAG_NAMES_Q18_TAG8_OLDEST_VIEWED
#####        assert nq_odoubt.tag_names_selected == TAG_NAMES_SELECTED
        
        # Test QUERY_UNSEEN_BY_OLDEST_VIEWED_TAG
        nq_unseen_by_tag = NextQuestion(query_name=QUERY_UNSEEN_BY_OLDEST_VIEWED_TAG, tag_ids_selected=TAG_IDS_SELECTED, user=user)
        assert nq_unseen_by_tag.question == q9_unseen_by_tag3
        assert nq_unseen_by_tag.count_times_question_seen == 0
        assert nq_unseen_by_tag.count_questions_due == COUNT_QUESTIONS_DUE
        assert nq_unseen_by_tag.count_questions_matched_criteria == COUNT_QUESTIONS_UNSEEN_BY_OLDEST_VIEWED_TAG
        assert nq_unseen_by_tag.count_questions_tagged == COUNT_QUESTIONS_WITH_TAG
        assert nq_unseen_by_tag.count_questions_unseen == COUNT_QUESTIONS_UNSEEN
        assert nq_unseen_by_tag.count_recent_seen_mins_30 == COUNT_RECENT_SEEN_MINS_30
        assert nq_unseen_by_tag.count_recent_seen_mins_60 == COUNT_RECENT_SEEN_MINS_60
        assert nq_unseen_by_tag.tag_names_for_question == [TAG3_NAME]
        assert nq_unseen_by_tag.tag_names_selected == TAG_NAMES_SELECTED
        
        # Verify different results
        assert nq_unseen.question != nq_oldest_due.question
        assert nq_unseen.question == nq_unseen_then_oldest_due.question
        assert nq_unseen.question == nq_unseen_then_oldest_due.question == nq_oldest_due_or_unseen.question
        assert nq_future.question != nq_unseen_then_oldest_due.question
        assert nq_future.question != nq_oldest_due.question
####        assert q9_unseen_by_tag3 ...
        assert (   nq_unseen.question
                != nq_oldest_due.question
                != nq_future.question
                != nq_reinforce.question
                != nq_unseen_by_tag.question
####                != nq_odoubt.question
                != nq_oldest_due_or_unseen.question
        )


        ############################################################
        # # Test QUERY_UNSEEN_THEN_OLDEST_DUE, no unseen
        ############################################################
        nq_unseen_then_oldest_due = NextQuestion(query_name=QUERY_UNSEEN_THEN_OLDEST_DUE, tag_ids_selected=[TAG5_DUE_ONLY.id], user=user)
        assert nq_unseen_then_oldest_due.question == q15_tag5_due_nm
        assert nq_unseen_then_oldest_due.count_times_question_seen == 1
        assert nq_unseen_then_oldest_due.count_questions_due == 1
        assert nq_unseen_then_oldest_due.count_questions_matched_criteria == 1
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
        assert nq_oldest_due_or_unseen.count_questions_matched_criteria == 2
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
        assert nq_oldest_due_None.count_questions_matched_criteria == 0
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
        assert nq_unseen_none.count_questions_matched_criteria == 0
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
        assert nq_unseen_then_oldest_due.count_questions_matched_criteria == 0
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
        assert nq_future.count_questions_matched_criteria == 0
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
        assert nq_reinforce.count_questions_matched_criteria == 0
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
        assert nq_oldest_due_or_unseen.count_questions_matched_criteria == 0
        assert nq_oldest_due_or_unseen.count_questions_tagged == 0
        assert nq_oldest_due_or_unseen.count_questions_unseen == 0
        assert nq_oldest_due_or_unseen.count_recent_seen_mins_30 == COUNT_RECENT_SEEN_MINS_30
        assert nq_oldest_due_or_unseen.count_recent_seen_mins_60 == COUNT_RECENT_SEEN_MINS_60
        assert nq_oldest_due_or_unseen.tag_names_for_question == []
        assert nq_oldest_due_or_unseen.tag_names_selected == tag_names_selected

        # Test QUERY_UNSEEN_BY_OLDEST_VIEWED_TAG picks None
####        tag_ids_selected = [tag4_no_questions.id]
####        tag_names_selected = sorted([tag4_no_questions.name])
####        nq_unseen_by_tag = NextQuestion(query_name=QUERY_UNSEEN_BY_OLDEST_VIEWED_TAG, tag_ids_selected=tag_ids_selected, user=user)
####        assert nq_unseen_by_tag.question is None
####        assert nq_unseen_by_tag.count_times_question_seen == 0
####        assert nq_unseen_by_tag.count_questions_due == 1
####        assert nq_unseen_by_tag.count_questions_matched_criteria == 0
####        assert nq_unseen_by_tag.count_questions_tagged == 2
####        assert nq_unseen_by_tag.count_questions_unseen == 0
####        assert nq_unseen_by_tag.count_recent_seen_mins_30 == COUNT_RECENT_SEEN_MINS_30
####        assert nq_unseen_by_tag.count_recent_seen_mins_60 == COUNT_RECENT_SEEN_MINS_60
####        assert nq_unseen_by_tag.tag_names_for_question == []
####        assert nq_unseen_by_tag.tag_names_selected == tag_names_selected

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
        assert nq.count_questions_matched_criteria == 2
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
        assert nq.count_questions_matched_criteria == 2
        assert nq.count_questions_unseen == 2
        assert nq.tag_names_for_question == [tag1.name]
        assert set(nq.tag_names_selected) == set([tag1.name, tag2.name])

    def test_get_nq_unseen_by_oldest_viewed_tag_mixed_schedules(self, user):
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
        QuestionTag.objects.create(question=q4, tag=tag2)

        Schedule.objects.create(user=user, question=q1, datetime_added=timezone.now() - timezone.timedelta(days=3))

        nq = NextQuestion(query_name=QUERY_UNSEEN_BY_OLDEST_VIEWED_TAG, tag_ids_selected=[tag1.id, tag2.id, tag3.id], user=user)

        assert nq.question == q2
        assert nq.count_questions_tagged == 4
        assert nq.count_questions_matched_criteria == 2
        assert nq.count_questions_unseen == 3
        assert nq.tag_names_for_question == [tag2.name]
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
        assert nq.count_questions_matched_criteria == 0
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
        assert nq.count_questions_matched_criteria == 2
        assert nq.count_questions_unseen == 2
        assert nq.tag_names_for_question == [tag1.name]
        assert set(nq.tag_names_selected) == set([tag1.name, tag2.name])