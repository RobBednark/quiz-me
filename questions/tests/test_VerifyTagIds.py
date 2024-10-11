import pytest

from questions.models import Question, Tag, QuestionTag, User
from questions.VerifyTagIds import VerifyTagIds

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

class TestVerifyTagIds:
    def test_all_tags_valid(self, user):
        tag1 = Tag.objects.create(name="tag1", user=user)
        tag2 = Tag.objects.create(name="tag2", user=user)
        QuestionTag.objects.create(tag=tag1, question=Question.objects.create(question="Q1", user=user), enabled=True)
        QuestionTag.objects.create(tag=tag2, question=Question.objects.create(question="Q2", user=user), enabled=True)
        
        # assert that the function does not raise an exception
        VerifyTagIds([tag1.id, tag2.id], user)

    def test_mixed_owned_and_unowned_tags(self, user):
        other_user = User.objects.create(email="other@example.com")
        tag1 = Tag.objects.create(name="tag1", user=user)
        tag2 = Tag.objects.create(name="tag2", user=other_user)
        
        with pytest.raises(ValueError) as exc_info:
            VerifyTagIds([tag1.id, tag2.id], user)
        assert f"Tag ids are not owned by user: [{tag2.id}]." in str(exc_info.value)

    def test_all_tags_not_owned(self, user):
        other_user = User.objects.create(email="other@example.com")
        tag1 = Tag.objects.create(name="tag1", user=other_user)
        tag2 = Tag.objects.create(name="tag2", user=other_user)
        
        with pytest.raises(ValueError) as exc_info:
            VerifyTagIds([tag1.id, tag2.id], user)
        assert f"Tag ids are not owned by user: [{tag1.id}, {tag2.id}]." in str(exc_info.value)

    def test_non_existent_tags(self, user):
        tag = Tag.objects.create(name="tag", user=user)
        non_existent_id = tag.id + 1000
        
        with pytest.raises(ValueError) as exc_info:
            VerifyTagIds([tag.id, non_existent_id], user)
        assert f"Tag ids do not exist: [{non_existent_id}]." in str(exc_info.value)

    def test_multiple_errors(self, user):
        other_user = User.objects.create(email="other@example.com")
        tag1 = Tag.objects.create(name="tag1", user=user)
        tag2 = Tag.objects.create(name="tag2", user=other_user)
        tag3 = Tag.objects.create(name="tag3", user=user)
        non_existent_id = tag3.id + 1000
        
        with pytest.raises(ValueError) as exc_info:
            VerifyTagIds([tag1.id, tag2.id, tag3.id, non_existent_id], user)
        error_message = str(exc_info.value)
        assert f"Tag ids are not owned by user: [{tag2.id}]." in error_message
        assert f"Tag ids do not exist: [{non_existent_id}]." in error_message

    def test_empty_tag_list(self, user):
        # assert that the function does not raise an exception
        VerifyTagIds([], user)

    def test_single_valid_tag(self, user):
        tag = Tag.objects.create(name="tag", user=user)
        QuestionTag.objects.create(tag=tag, question=Question.objects.create(question="Q", user=user), enabled=True)
        
        # assert that the function does not raise an exception
        VerifyTagIds([tag.id], user)