from collections import defaultdict

from questions.models import QuestionTag, Tag, TagLineage

'''
The "hierarchy" data structure looks like this:
    {
        <tag_id>: {
            'children': set([<tag_id>, ...]),  # only immediate children
            'parents': set([<tag_id>, ...]),  # only immediate parents
            'ancestors': set([<tag_id>, ...]), # all ancestors
            'descendants': set([<tag_id>, ...]), # all descendants
            'descendants_and_self': set([<tag_id>, ...]), # all descendants plus <tag_id>
            'count_questions_all': <count>  # count of questions tagged with any tag in this tag's descendants (or this tag itself)
            'count_questions_tag': <count>  # count of questions with this tag
            'question_ids_for_all': set([<question_id>, ...]), # set of question ids tagged with this tag and/or any of its descendants
            'question_ids_for_tag': set([<question_id>, ...]), # set of question ids tagged with this tag
            'tag_name': <tag_name>,
        },
        ...
    }
'''

def get_tag_hierarchy(user):
    '''
    Return a "hierarchy" dict per the description at the top of this file.
    The graph can be cyclical (e.g., tag1 has child tag2, and tag2 has child tag1).
    count_questions_all must be careful not to double-count questions with multiple descendant tags.  e.g., use .filter(tag__in=[descendants+tag])
    '''
    
    def build_hierarchy(hierarchy, tag_id, tag_id_children, tag_id_parents, type_, visited):
        '''
        Recursive function to build either the ancestors or descendants for tag_id.

        Parameters:
        hierarchy (dict) - the hierarchy dict, per the structure above
        tag_id (Tag) - the tag id to build the ancestors or descendants for
        type_ (string) - 'ancestors' or 'descendants' (which ones to build)
        visited (set) - set of tag id's that have been visited; the initial call passes in an empty set, and recursive calls add on to this set

        Algorithm:

        visited.add(tag_id)
        Create hierarchy[tag_id] entry if not already created
        foreach parent of tag:
            if parent not in visited:
                recursively call build_hierarchy(parent, type_)
                add parent to: hierarchy[tag_id]['parents']
                add parent to: hierarchy[tag_id]['ancestors']
                add parent's ancestors to hierarchy[tag_id]['ancestors']

        Do the same for children/descendants
        '''
        
        visited.add(tag_id)
        if tag_id not in hierarchy:
            hierarchy[tag_id] = {
                'children': set(),
                'parents': set(),
                'ancestors': set(),
                'descendants': set(),
                'descendants_and_self': set(),
            }

        if type_ == 'ancestors':
            for parent_tag_id in tag_id_parents[tag_id]:
                if parent_tag_id not in visited:
                    build_hierarchy(hierarchy=hierarchy, tag_id=parent_tag_id, tag_id_children=tag_id_children, tag_id_parents=tag_id_parents, type_=type_, visited=visited)
                    hierarchy[tag_id]['parents'].add(parent_tag_id)
                    hierarchy[tag_id]['ancestors'].add(parent_tag_id)
                    hierarchy[tag_id]['ancestors'].update(hierarchy[parent_tag_id]['ancestors'])
        elif type_ == 'descendants':
            for child_tag_id in tag_id_children[tag_id]:
                if child_tag_id not in visited:
                    build_hierarchy(hierarchy=hierarchy, tag_id=child_tag_id, tag_id_children=tag_id_children, tag_id_parents=tag_id_parents, type_=type_, visited=visited)
                    hierarchy[tag_id]['children'].add(child_tag_id)
                    hierarchy[tag_id]['descendants'].update(hierarchy[child_tag_id]['descendants_and_self'])
                    hierarchy[tag_id]['descendants_and_self'].update(hierarchy[child_tag_id]['descendants_and_self'])
            hierarchy[tag_id]['descendants_and_self'].add(tag_id)  # add self
        else:
            raise ValueError(f'type_=[{type_}] but must be either "ancestors" or "descendants"')

    tags = Tag.objects.filter(user=user)
    tag_lineages = TagLineage.objects.filter(user=user).values('child_tag_id', 'parent_tag_id')
    tag_id_children = defaultdict(set)
    tag_id_parents = defaultdict(set)
    for tag_lineage in tag_lineages:
        tag_id_children[tag_lineage['parent_tag_id']].add(tag_lineage['child_tag_id'])
        tag_id_parents[tag_lineage['child_tag_id']].add(tag_lineage['parent_tag_id'])

    hierarchy = {}

    for type_ in ['ancestors', 'descendants']:
        for tag in tags:
            build_hierarchy(hierarchy=hierarchy, tag_id=tag.id, tag_id_children=tag_id_children, tag_id_parents=tag_id_parents, type_=type_, visited=set())

    question_tags = get_question_tags(user=user)

    for tag in tags:
        hierarchy[tag.id]['question_ids_for_tag'] = question_tags[tag.id]
        hierarchy[tag.id]['question_ids_for_all'] = set()
        for desc_tag_id in hierarchy[tag.id]['descendants_and_self']:
            hierarchy[tag.id]['question_ids_for_all'] |= question_tags[desc_tag_id]
        hierarchy[tag.id]['count_questions_tag'] = len(hierarchy[tag.id]['question_ids_for_tag'])
        hierarchy[tag.id]['count_questions_all'] = len(hierarchy[tag.id]['question_ids_for_all'])
        hierarchy[tag.id]['tag_name'] = tag.name

    return hierarchy

def get_question_tags(user):
    '''
    Return a dict of all question_id's for each tag_id.
    Use a single query, getting all QuestionTag's for <user>, and return them in a data structure like this:
    {
      <tag_id>: {<question_id>, <question_id>, ...},
      ...
    }
    If a tag has no questions, it will not be in the dict.

    Parameters:
      user (User Object) - the user to get the QuestionTag's for
    Returns:
      Data structure per above
    '''
    
    ret = defaultdict(set)
    for qt in QuestionTag.objects.filter(user=user).values('tag_id', 'question_id'):
        tag_id = qt['tag_id']
        ret[tag_id].add(qt['question_id'])
    return ret

def expand_all_tag_ids(hierarchy, tag_ids):
    '''
    Return a set of all tag id's consisting of tag_ids and their descendants.
    Parameters:
        hierarchy (dict) - the hierarchy dict, per the structure above
        tag_ids (iterable) - an iterable of Tag.id's (list, set, ...), e.g., [1, 2]
    Returns:
        expanded_tag_id_list (set) - a set of all tag id's consisting of tag_ids and their descendants
    '''
    expanded_tag_id_list = set()
    for tag_id in tag_ids:
        expanded_tag_id_list.update(hierarchy[tag_id]['descendants_and_self'])
    return expanded_tag_id_list

def get_all_questions_for_tag_ids(hierarchy, tag_ids):
    '''
    Return a set of all question id's consisting of questions for tag_ids and their descendants.
    Parameters:
        hierarchy (dict) - the hierarchy dict, per the structure above
        tag_ids (iterable) - an iterable of Tag.id's (list, set, ...), e.g., [1, 2]
    Returns:
        question_ids (set) - a set of all question id's consisting of questions for tag_ids and their descendants
    '''
    expanded_tag_id_list = expand_all_tag_ids(hierarchy, tag_ids)
    question_ids = set()
    for tag_id in expanded_tag_id_list:
        question_ids.update(hierarchy[tag_id]['question_ids_tag'])
    return question_ids