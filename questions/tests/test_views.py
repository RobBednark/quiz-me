from django.test import TestCase
from django.contrib.auth import get_user_model
from questions.models import Tag
from questions.views import TagList, FIELD_NAME__TAG_ID_PREFIX

User = get_user_model()

class TestTagList(TestCase):
    @classmethod
    def setUpClass(self):
        self.user = User.objects.create_user(email='testuser@example.com', password='testpass')
        self.tag1 = Tag.objects.create(name='Tag 1', user=self.user)
        self.tag2 = Tag.objects.create(name='Tag 2', user=self.user)
        self.tag3 = Tag.objects.create(name='Tag 3', user=self.user)
    
    @classmethod
    def tearDownClass(self):
        self.user.delete()
        self.tag1.delete()
        self.tag2.delete()
        self.tag3.delete()

    def test_init_with_id_comma_str(self):
        tag_list = TagList(id_comma_str='1,2,3')
        self.assertEqual(tag_list.as_id_int_list(), [1, 2, 3])
        self.assertEqual(tag_list.as_id_comma_str(), '1,2,3')

    def test_init_with_form_field_names(self):
        tag_list = TagList(form_field_names=[f'{FIELD_NAME__TAG_ID_PREFIX}1', f'{FIELD_NAME__TAG_ID_PREFIX}2'])
        self.assertEqual(tag_list.as_id_int_list(), [1, 2])

    def test_init_with_both_arguments_raises_exception(self):
        with self.assertRaises(Exception):
            TagList(id_comma_str='1,2', form_field_names=['field1', 'field2'])

    def test_init_with_no_arguments_raises_exception(self):
        with self.assertRaises(Exception):
            TagList()

    def test_as_id_comma_str(self):
        tag_list = TagList(id_comma_str='1,2,3')
        self.assertEqual(tag_list.as_id_comma_str(), '1,2,3')

    def test_as_form_fields_list(self):
        tag_list = TagList(id_comma_str=f'{self.tag1.id},{self.tag3.id}')
        result = tag_list.as_form_fields_list(self.user)
        expected = [
            {
                'tag_form_name': f'{FIELD_NAME__TAG_ID_PREFIX}{self.tag1.id}',
                'tag_form_label': 'Tag 1',
                'tag_id': self.tag1.id,
                'checked': 'checked'
            },
            {
                'tag_form_name': f'{FIELD_NAME__TAG_ID_PREFIX}{self.tag2.id}',
                'tag_form_label': 'Tag 2',
                'tag_id': self.tag2.id,
                'checked': ''
            },
            {
                'tag_form_name': f'{FIELD_NAME__TAG_ID_PREFIX}{self.tag3.id}',
                'tag_form_label': 'Tag 3',
                'tag_id': self.tag3.id,
                'checked': 'checked'
            }
        ]
        self.assertEqual(result, expected)

    def test_as_form_fields_list_empty(self):
        tag_list = TagList(id_comma_str='')
        result = tag_list.as_form_fields_list(self.user)
        self.assertEqual(len(result), 3)
        for item in result:
            self.assertEqual(item['checked'], '')

    def test_as_form_fields_list_sorting(self):
        Tag.objects.create(name='A Tag', user=self.user)
        tag_list = TagList(id_comma_str='')
        result = tag_list.as_form_fields_list(self.user)
        self.assertEqual(result[0]['tag_form_label'], 'A Tag')
