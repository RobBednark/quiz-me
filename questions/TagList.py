import re

from questions.models import Tag

FIELD_NAME__TAG_ID_PREFIX = 'field_name__tag_id=' # e.g. field_name__tag_id=5

class TagList:
    def __init__(self, id_comma_str=None, form_field_names=None):
        # Must be called with either id_comma_str or form_field_names, but not both, else an exception is raised.
        # e.g., id_comma_str: a string of comma-separated int id's, e.g.,
        #   id_comma_str='1,2,3'
        # e.g., form_field_names: a list of the form-field names, where each name , e.g.,
        #   form_field_names=['id_form_name_1', 'id_form_name_2']
        if id_comma_str and form_field_names:
            raise Exception("Must be called with either id_comma_str or form_field_names argument, but not both")
        if (id_comma_str is None) and (form_field_names is None):
            raise Exception("One of the following two arguments must be specified: id_comma_str, form_field_names")

        self.id_int_list = []

        if id_comma_str:
            as_str_list = id_comma_str.split(',')
            self.id_int_list = [int(tag_id) for tag_id in as_str_list]
        elif form_field_names:
            for field_name in form_field_names:
                match = re.search(pattern=f"{FIELD_NAME__TAG_ID_PREFIX}(\\d+)$", string=field_name)
                if match:
                    tag_id = int(match.group(1))
                    self.id_int_list.append(tag_id)
    
    def as_id_comma_str(self):
        # e.g., "1,2"
        return ','.join([ str(id) for id in self.id_int_list])
    
    def as_id_int_list(self):
        # e.g., [1, 2]
        return self.id_int_list
    
    def as_form_fields_list(self, user):  # previously called get_tag_fields()
    # Get all tags for {user}.  Return a list of dicts, sorted by tag name, where each dict has the fields for one tag,
    # with tag_form_name and tag_form_label to be used in the HTML form.
    # e.g.,
    #  [
    #   { tag_form_name: 'id_form_name_3',  # the form name for the checkbox for this tag, where "3" is tag.id
    #     tag_form_label: 'my tag',  # the label for the checkbox for this tag, corresponding to tag.name
    #     tag_id: 3
    #   }
    #  ]
        tag_fields_list = []
        for tag in Tag.objects.filter(user=user):
            tag_form_name = f'{FIELD_NAME__TAG_ID_PREFIX}{tag.id}'
            # "checked" is the <select type="checkbox"> boolean attribute for whether the checkbox is checked.
            if tag.id in self.id_int_list:
                checked = 'checked'
            else:
                checked = ''
            tag_fields_list.append(dict(
                    tag_form_name=tag_form_name,
                    tag_form_label=tag.name,
                    tag_id=tag.id,
                    checked=checked
                    ))
        # sort by tag_form_label
        tag_fields_list.sort(key=lambda x: x['tag_form_label'])
        return tag_fields_list