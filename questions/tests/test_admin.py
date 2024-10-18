import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from questions.models import Answer, Tag, Question, QuestionTag

@pytest.fixture
def admin_client(client, django_user_model):
    admin_user = django_user_model.objects.create_superuser(
        email='admin@example.com',
        password='adminpassword'
    )
    client.login(email='admin@example.com', password='adminpassword')
    return client

@pytest.mark.django_db
def test_answer_admin(admin_client):
    url = reverse('admin:questions_answer_changelist')
    response = admin_client.get(url)
    assert response.status_code == 200

@pytest.mark.django_db
def test_attempt_admin(admin_client):
    url = reverse('admin:questions_attempt_changelist')
    response = admin_client.get(url)
    assert response.status_code == 200

@pytest.mark.django_db
def test_tag_admin(admin_client):
    url = reverse('admin:questions_tag_changelist')
    response = admin_client.get(url)
    assert response.status_code == 200

@pytest.mark.django_db
def test_question_admin(admin_client):
    url = reverse('admin:questions_question_changelist')
    response = admin_client.get(url)
    assert response.status_code == 200

@pytest.mark.django_db
def test_questiontag_admin(admin_client):
    url = reverse('admin:questions_questiontag_changelist')
    response = admin_client.get(url)
    assert response.status_code == 200

@pytest.mark.django_db
def test_schedule_admin(admin_client):
    url = reverse('admin:questions_schedule_changelist')
    response = admin_client.get(url)
    assert response.status_code == 200

@pytest.mark.django_db
def test_taglineage_admin(admin_client):
    url = reverse('admin:questions_taglineage_changelist')
    response = admin_client.get(url)
    assert response.status_code == 200

@pytest.mark.django_db
def test_answer_admin_search(admin_client, django_user_model):
    admin_user = django_user_model.objects.get(email='admin@example.com')
    Answer.objects.create(answer="Test answer", user=admin_user)
    url = reverse('admin:questions_answer_changelist') + '?q=Test'
    response = admin_client.get(url)
    assert response.status_code == 200
    assert "Test answer" in response.content.decode()

@pytest.mark.django_db
def test_question_admin_tags_display(admin_client, django_user_model):
    admin_user = django_user_model.objects.get(email='admin@example.com')
    tag = Tag.objects.create(name="TestTag", user=admin_user)
    question = Question.objects.create(question="Test question", user=admin_user)
    QuestionTag.objects.create(question=question, tag=tag)
    url = reverse('admin:questions_question_change', args=[question.id])
    response = admin_client.get(url)
    assert response.status_code == 200
    assert "TestTag" in response.content.decode()
