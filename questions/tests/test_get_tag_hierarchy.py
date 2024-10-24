import pytest

from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext

from questions.models import Question, QuestionTag, Tag, TagLineage
from questions.get_tag_hierarchy import expand_all_tag_ids, get_question_tags, get_tag_hierarchy

User = get_user_model()

@pytest.mark.django_db
class TestGetTagHierarchy:
    @pytest.fixture
    def user(self):
        return User.objects.create(email="testuser@example.com")

    @pytest.fixture
    def setup_tags(self, user):
        parent = Tag.objects.create(name="parent", user=user)
        child1 = Tag.objects.create(name="child1", user=user)
        child2 = Tag.objects.create(name="child2", user=user)
        grandchild = Tag.objects.create(name="grandchild", user=user)
    
        TagLineage.objects.create(parent_tag=parent, child_tag=child1, user=user)
        TagLineage.objects.create(parent_tag=parent, child_tag=child2, user=user)
        TagLineage.objects.create(parent_tag=child1, child_tag=grandchild, user=user)
    
        return parent, child1, child2, grandchild

    @pytest.fixture
    def setup_questions(self, user, setup_tags):
        parent, child1, child2, grandchild = setup_tags
        q1 = Question.objects.create(question="Q1", user=user)
        q2 = Question.objects.create(question="Q2", user=user)
        q3 = Question.objects.create(question="Q3", user=user)

        # Use QuestionTag.create(), not parent.add(), because the latter doesn't save a user
        QuestionTag.objects.create(tag=parent, question=q1, user=user)
        QuestionTag.objects.create(tag=child1, question=q2, user=user)
        QuestionTag.objects.create(tag=grandchild, question=q3, user=user)

        return q1, q2, q3

    def test_tag_hierarchy_structure(self, user, setup_tags):
        parent, child1, child2, grandchild = setup_tags
        with CaptureQueriesContext(connection) as context:
            assert len(context) == 0, "Should be 0 queries before the call to get_tag_hierarchy()"
            hierarchy = get_tag_hierarchy(user)
            assert len(context) == 20

        assert len(hierarchy) == 4
        assert all(tag_id in hierarchy for tag_id in [parent.id, child1.id, child2.id, grandchild.id])
        assert all(key in hierarchy[parent.id] for key in ['children', 'parents', 'ancestors', 'descendants', 'count_questions_all', 'count_questions_tag', 'tag_name'])

    def test_parent_child_relationships(self, user, setup_tags):
        parent, child1, child2, grandchild = setup_tags
        hierarchy = get_tag_hierarchy(user)

        assert hierarchy[parent.id]['children'] == {child1.id, child2.id}
        assert hierarchy[parent.id]['parents'] == set()

        assert hierarchy[child1.id]['children'] == {grandchild.id}
        assert hierarchy[child1.id]['parents'] == {parent.id}

        assert hierarchy[child2.id]['children'] == set()
        assert hierarchy[child2.id]['parents'] == {parent.id}

        assert hierarchy[grandchild.id]['children'] == set()
        assert hierarchy[grandchild.id]['parents'] == {child1.id}

    def test_ancestors_and_descendants(self, user, setup_tags):
        parent, child1, child2, grandchild = setup_tags
        hierarchy = get_tag_hierarchy(user)

        assert hierarchy[parent.id]['ancestors'] == set()
        assert hierarchy[parent.id]['descendants'] == {child1.id, child2.id, grandchild.id}
        assert hierarchy[parent.id]['descendants_and_self'] == {parent.id, child1.id, child2.id, grandchild.id}

        assert hierarchy[child1.id]['ancestors'] == {parent.id}
        assert hierarchy[child1.id]['descendants'] == {grandchild.id}
        assert hierarchy[child1.id]['descendants_and_self'] == {child1.id, grandchild.id}

        assert hierarchy[child2.id]['ancestors'] == {parent.id}
        assert hierarchy[child2.id]['descendants'] == set()
        assert hierarchy[child2.id]['descendants_and_self'] == {child2.id}

        assert hierarchy[grandchild.id]['ancestors'] == {parent.id, child1.id}
        assert hierarchy[grandchild.id]['descendants'] == set()
        assert hierarchy[grandchild.id]['descendants_and_self'] == {grandchild.id}

    def test_question_counts(self, user, setup_tags, setup_questions):
        parent, child1, child2, grandchild = setup_tags
        hierarchy = get_tag_hierarchy(user)

        assert hierarchy[parent.id]['count_questions_tag'] == 1
        assert hierarchy[parent.id]['count_questions_all'] == 3

        assert hierarchy[child1.id]['count_questions_tag'] == 1
        assert hierarchy[child1.id]['count_questions_all'] == 2

        assert hierarchy[grandchild.id]['count_questions_tag'] == 1
        assert hierarchy[grandchild.id]['count_questions_all'] == 1

        assert hierarchy[child2.id]['count_questions_tag'] == 0
        assert hierarchy[child2.id]['count_questions_all'] == 0

    def test_tag_names(self, user, setup_tags):
        parent, child1, child2, grandchild = setup_tags
        hierarchy = get_tag_hierarchy(user)

        assert hierarchy[parent.id]['tag_name'] == "parent"
        assert hierarchy[child1.id]['tag_name'] == "child1"
        assert hierarchy[child2.id]['tag_name'] == "child2"
        assert hierarchy[grandchild.id]['tag_name'] == "grandchild"

    def test_empty_hierarchy(self, user):
        hierarchy = get_tag_hierarchy(user)
        assert hierarchy == {}

    def test_multiple_users(self, user):
        other_user = User.objects.create(email="otheruser@example.com")
        Tag.objects.create(name="user1_tag", user=user)
        Tag.objects.create(name="user2_tag", user=other_user)

        user1_hierarchy = get_tag_hierarchy(user)
        user2_hierarchy = get_tag_hierarchy(other_user)

        assert len(user1_hierarchy) == 1
        assert len(user2_hierarchy) == 1
        assert list(user1_hierarchy.values())[0]['tag_name'] == "user1_tag"
        assert list(user2_hierarchy.values())[0]['tag_name'] == "user2_tag"

class TestExpandAllTagIds:

    @pytest.fixture
    def sample_hierarchy(self):
        return {
            1: {'descendants_and_self': {1, 2, 3}},
            2: {'descendants_and_self': {2, 3}},
            3: {'descendants_and_self': {3}},
            4: {'descendants_and_self': {4, 5}},
            5: {'descendants_and_self': {5}},
        }
    
    def test_expand_single_tag(self, sample_hierarchy):
        result = expand_all_tag_ids(sample_hierarchy, [1])
        assert result == {1, 2, 3}
    
    def test_expand_multiple_tags(self, sample_hierarchy):
        result = expand_all_tag_ids(sample_hierarchy, [1, 4])
        assert result == {1, 2, 3, 4, 5}
    
    def test_expand_leaf_tag(self, sample_hierarchy):
        result = expand_all_tag_ids(sample_hierarchy, [3])
        assert result == {3}
    
    def test_expand_empty_list(self, sample_hierarchy):
        result = expand_all_tag_ids(sample_hierarchy, [])
        assert result == set()
    
    def test_expand_all_tags(self, sample_hierarchy):
        result = expand_all_tag_ids(sample_hierarchy, [1, 2, 3, 4, 5])
        assert result == {1, 2, 3, 4, 5}
    
    def test_expand_duplicate_tags(self, sample_hierarchy):
        result = expand_all_tag_ids(sample_hierarchy, [1, 1, 2, 2])
        assert result == {1, 2, 3}
    
    def test_expand_nonexistent_tag(self, sample_hierarchy):
        with pytest.raises(KeyError):
            expand_all_tag_ids(sample_hierarchy, [6])

@pytest.mark.django_db
class TestGetQuestionTags:
    @pytest.fixture
    def user(self):
        return User.objects.create(email="testuser@example.com")

    @pytest.fixture
    def setup_question_tags(self, user):
        tag1 = Tag.objects.create(name="tag1", user=user)
        tag2 = Tag.objects.create(name="tag2", user=user)
        q1 = Question.objects.create(question="Q1", user=user)
        q2 = Question.objects.create(question="Q2", user=user)
        q3 = Question.objects.create(question="Q3", user=user)
        
        QuestionTag.objects.create(question=q1, tag=tag1, user=user)
        QuestionTag.objects.create(question=q2, tag=tag1, user=user)
        QuestionTag.objects.create(question=q2, tag=tag2, user=user)
        QuestionTag.objects.create(question=q3, tag=tag2, user=user)
        
        return tag1, tag2, q1, q2, q3

    def test_get_question_tags_basic(self, user, setup_question_tags):
        tag1, tag2, q1, q2, q3 = setup_question_tags
        result = get_question_tags(user)
        
        assert result == {tag1.id: {q1.id, q2.id}, tag2.id: {q2.id, q3.id}}

    def test_get_question_tags_empty(self, user):
        result = get_question_tags(user)
        assert result == {}

    def test_get_question_tags_single_question(self, user):
        tag = Tag.objects.create(name="tag", user=user)
        question = Question.objects.create(question="Q", user=user)
        QuestionTag.objects.create(question=question, tag=tag, user=user)
        
        result = get_question_tags(user)
        assert result == {tag.id: {question.id}}

    def test_get_question_tags_multiple_users(self, user):
        user1 = user
        user2 = User.objects.create(email="user2@user2.com")
        user1_tag = Tag.objects.create(name="user1 tag", user=user1)
        user2_tag = Tag.objects.create(name="user2 tag", user=user2)
        user1_q = Question.objects.create(question="Q1", user=user1)
        user2_q = Question.objects.create(question="Q2", user=user2)
        
        QuestionTag.objects.create(question=user1_q, tag=user1_tag, user=user1)
        QuestionTag.objects.create(question=user2_q, tag=user2_tag, user=user2)
        
        result = get_question_tags(user=user1)
        assert result == {user1_tag.id: {user1_q.id}}

    def test_get_question_tags_query_count(self, user, setup_question_tags):
        with CaptureQueriesContext(connection) as context:
            get_question_tags(user)
            assert len(context) == 1, "Should only make one database query"
    
    def test_tag_with_no_questions(self, user):
        tag = Tag.objects.create(name="tag", user=user)
        result = get_question_tags(user)
        assert result == {}