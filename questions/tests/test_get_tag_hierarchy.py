import pytest
from django.contrib.auth import get_user_model
from questions.models import Question, Tag, TagLineage
from questions.get_tag_hierarchy import expand_all_tag_ids, get_tag_hierarchy

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

        parent.questions.add(q1)
        child1.questions.add(q2)
        grandchild.questions.add(q3)

        return q1, q2, q3

    def test_tag_hierarchy_structure(self, user, setup_tags):
        parent, child1, child2, grandchild = setup_tags
        hierarchy = get_tag_hierarchy(user)

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
