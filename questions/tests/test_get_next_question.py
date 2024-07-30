import math

from django.test import TestCase

from emailusername.models import User

from questions import models, util
from questions.get_next_question import get_next_question, NextQuestion

NUM_QUERIES_SCHEDULED_BEFORE_NOW = 3  # scheduled question is due to be shown before now
NUM_QUERIES_NO_QUESTIONS = 5  # number of queries expected when no questions are found

class TestGetNextQuestion(TestCase):

    def setUp(self):
        # Create a user
        self.PASSWORD = 'my_password'
        self.USERNAME = 'user@mydomain.com'
        self.query_prefs_obj = models.QueryPreferences.objects.create()
        self.user = User(email=self.USERNAME)
        self.user.set_password(self.PASSWORD)
        self.user.save()

    def test_user_with_no_questions(self):
        next_question = get_next_question(user=self.user, query_prefs_obj=self.query_prefs_obj, tags_selected=[])

        self.assertIsInstance(next_question, NextQuestion)
        self.assertIsNone(next_question.question)

    def test_user_with_one_unassociated_question(self):

        models.Question.objects.create(
            question='question #1',
        )

        # One untagged question that doesn't get returned because it has
        # no tags.

        next_question = get_next_question(self.user, query_prefs_obj=self.query_prefs_obj, tags_selected=[])

        self.assertIsInstance(next_question, NextQuestion)
        self.assertIsNone(next_question.question)

        questions = models.Question.objects.filter(user=self.user)
        self.assertEqual(questions.count(), 0)

    def test_user_with_one_question(self):
        question = models.Question.objects.create(
            question='question #1',
            user=self.user
        )
        tag = util.assign_question_to_user(user=self.user, question=question, tag_name='tag #1')
        util.schedule_question_for_user(self.user, question)

        next_question = get_next_question(self.user, query_prefs_obj=self.query_prefs_obj, tags_selected=models.Tag.objects.filter(pk=tag.pk))

        self.assertIsInstance(next_question, NextQuestion)
        self.assertIsNotNone(next_question.question)

        questions = models.Question.objects.filter(user=self.user)
        self.assertEqual(questions.count(), 1)

    def test_user_with_ten_questions(self):
        tag = models.Tag.objects.create(name='tag #1')
        for i in range(10):
            question = models.Question.objects.create(
                question=f'question {i}',
                user=self.user,
            )
            models.QuestionTag.objects.create(tag=tag, question=question, enabled=True)

        next_question = get_next_question(self.user, query_prefs_obj=self.query_prefs_obj, tags_selected=models.Tag.objects.filter(pk=tag.pk))

        self.assertIsInstance(next_question, NextQuestion)
        self.assertIsNotNone(next_question.question)

        questions = models.Question.objects.filter(user=self.user)
        self.assertEqual(questions.count(), 10)
        
class CreateData():
    NUM_QUESTIONS_TAG_GROUPS = 5
    NUM_QUESTIONS_PER_TAG = 10
    NUM_TAGS = 10
    NUM_USERS = 10
    def __init__(self) -> None:
        pass
    def create_data(self):
        for user_num in range(1, NUM_USERS+1):
            user_email = f"user_{user_num}@my_domain.com"
            user = User.objects.create(email=user_email)
            self._create_data_for_user(user=user)
    def _create_data_for_user(user):
        for tag_num in range(0, self.NUM_TAGS + 2):
            if tag_num == 0:
                # create questions without tags
                tag = None
            else:
                tag_name = f"tag {tag_num}"
                tag = Tag.objects.create(name=tag_name, user=user)
            self._create_data_for_tag(tag=tag, user=user)
    
    def _create_data_for_tag(self, tag, user):
        for question_num in range(1, self.NUM_QUESTIONS_PER_TAG + 1):
            question_name = f"question {question_num}"
            question = Question.objects.create(question=question_name, user=user)
            self._create_data_for_question(self, question, tag, user)
    
    def _create_data_for_question(self, question, user):
        # Create some questions with no tags           
        pass

                
                
class TestsCreateMany(TestCase):
    @classmethod
    def setUp(cls):
        NUM_QUESTIONS_TAG_GROUPS = 5
        NUM_QUESTIONS = 100
        NUM_TAGS = 100
        NUM_USERS = 100

        question_tags = {}  # key: "question 1 tag 1" value: QuestionTag object
        cls.questions = {}  # key: "question 1" value: Question object
        schedules = {}
        tag2questions = {}  # key: "tag 1"  value: list of Question objects
        question2tags = {}  # key: "question 1"  value: list of Tag objects
        question_objs = []  # list of Question objects
        tags = {}  # key: "tag 1" value: Tag object
        user_objs = []  # list of User objects
        users = {}  # key: "user_1@my_domain.com" value: User object
        user1 = None  # will arbitrarily be the first user

        for idx in range(NUM_USERS):
            idx = idx + 1
            user_email = f"user_{idx}@my_domain.com"
            user_obj = User.objects.create(email=user_email)
            users[user_email] = user_obj
            user_objs.append(user_obj)
        user1 = user_objs[0]

        for idx in range(NUM_QUESTIONS):
            question_name = f"question {idx}"
            # question = Question.objects.create(question=question_name, user=)
            cls.questions[question_name] = question
            question2tags[question_name] = []
            
        for idx in range(NUM_TAGS):
            tag_name = f"tag {idx}"
            tag = Tag.objects.create(name=tag_name)
            tags[tag_name] = tag
            tag2questions[tag_name] = []

        # for each group of n questions , choose n random tags for that group, e.g.,
        # group 1: 0 tags
        #   q1: 0 tags
        #   q2: 0 tags
        #   ...
        # group 2: 1 tag
        #   q21: 1 tag
        #   ...
        # group 3: 2 tags
        # ...
        num_per_group = NUM_QUESTIONS // NUM_QUESTIONS_TAG_GROUPS
        # group_num = 2,3,...,NUM_QUESTIONS_TAG_GROUPS
        # (skip group 1 because it will have 0 tags)
        # first_n_questions = list(cls.questions.values())[0:NUM_QUESTIONS_TAG_GROUPS-1)]
        for question_obj in question_objects
            group_num = math.ceil(question_num / NUM_QUESTIONS_TAG_GROUPS)  # e.g., 6 / 5 = 2
            num_tags = group_num - 1
            # use a set to avoid picking same tag more than once
            tag_num_set = set(list(range(1, NUM_TAGS_QUESTIONS + 1)))
            for _ in range(num_tags):
                tag_num = random.randint(1, len(tag_num_set) + 1)
                tag_num_set.remove(tag_num)
                tag_name = f"tag {tag_num}"
                tag = tags[tag_name]
                question_name = f"question {question_num}"
                question = cls.questions[question_name]
                question_tag = QuestionTag.objects.create(
                    question=question, tag=tag, enabled=True
                )
                question_tags[question_name + tag_name] = question_tag
                question2tags[question_name].append(tag)
                tag2questions[tag_name].append(question)
# for each question
#   group = ...
#   num_tags = group - 1
#   for tag in num_tags:

#           schedule = Schedule.objects.create(
#               user=user,
#               question=question,
#               interval_num=1,
#               interval_unit='months',
#               date_show_next=datetime.now(tz=pytz.utc) + timedelta(days=i)
#           )
        # use faker to get a random time, e.g.,
        # fake.date_time_between(start_date='-30y', end_date='now')
        # datetime.datetime(2007, 2, 28, 11, 28, 16)
        
    @classmethod
    def tearDownClass(cls):
        super(TestCase, cls).tearDownClass()
        tear_down_all()
    
    def test_1(self):
        print(f"len(TestsCreateMany.questions) = {len(TestsCreateMany.questions)}")
def tear_down_all():
        Answer.objects.all().delete()
        Attempt.objects.all().delete()
        Question.objects.all().delete()
        QuestionTag.objects.all().delete()
        Schedule.objects.all().delete()
        Tag.objects.all().delete()
        User.objects.all().delete()
