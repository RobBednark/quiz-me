from questions.models import Tag, Question, TagLineage

def get_tag_hierarchy(user):
    '''
    Return a dict of tag hierarchies for a given user of the form:
    {
        <tag_id>: {
            'children': set([<tag_id>, ...]),  # only immediate children
            'parents': set([<tag_id>, ...]),  # only immediate parents
            'ancestors': set([<tag_id>, ...]), # all ancestors
            'descendants': set([<tag_id>, ...]), # all descendants
            'descendants_and_self': set([<tag_id>, ...]), # all descendants plus <tag_id>
            'count_questions_all': <count>  # count of questions tagged with any tag in this tag's descendants (or this tag itself)
            'count_questions_tag': <count>  # count of questions with this tag
            'tag_name': <tag_name>,
        },
        ...
    }
    
    The graph can be cyclical (e.g., tag1 has child tag2, and tag2 has child tag1).
    count_questions_all must be careful not to double-count questions with multiple descendant tags.  e.g., use .filter(tag__in=[descendants+tag])
    '''
    
    def build_hierarchy(hierarchy, tag, type_, visited):
        '''
        Recursive function to build either the ancestors or descendants for tag.

        Parameters:
        hierarchy (dict) - the hierarchy dict, per the structure above
        tag (Tag) - the tag to build the ancestors or descendants for
        type_ (string) - 'ancestors' or 'descendants' (which ones to build)
        visited (set) - set of tag.id's that have been visited; the initial call passes in an empty set, and recursive calls add on to this set

        Algorithm:

        visited.add(tag.id)
        Create hierarchy[tag.id] entry if not already created
        foreach parent of tag:
            if parent not in visited:
                recursively call build_hierarchy(parent, type_)
                add parent to: hierarchy[tag.id]['parents']
                add parent to: hierarchy[tag.id]['ancestors']
                add parent's ancestors to hierarchy[tag.id]['ancestors']

        Do the same for children/descendants
        '''
        
        visited.add(tag.id)
        if tag.id not in hierarchy:
            hierarchy[tag.id] = {
                'children': set(),
                'parents': set(),
                'ancestors': set(),
                'descendants': set(),
                'descendants_and_self': set(),
            }
        hierarchy[tag.id]['tag_name'] = tag.name

        if type_ == 'ancestors':
            for parent_tag_2_child in tag.parents.all():
                parent_tag = parent_tag_2_child.parent_tag
                if parent_tag.id not in visited:
                    build_hierarchy(hierarchy=hierarchy, tag=parent_tag, type_=type_, visited=visited)
                    hierarchy[tag.id]['parents'].add(parent_tag.id)
                    hierarchy[tag.id]['ancestors'].add(parent_tag.id)
                    hierarchy[tag.id]['ancestors'].update(hierarchy[parent_tag.id]['ancestors'])
        elif type_ == 'descendants':
            for child_tag_2_parent in tag.children.all():
                child_tag = child_tag_2_parent.child_tag
                if child_tag.id not in visited:
                    build_hierarchy(hierarchy=hierarchy, tag=child_tag, type_=type_, visited=visited)
                    hierarchy[tag.id]['children'].add(child_tag.id)
                    # hierarchy[tag.id]['descendants'].add(child_tag.id)
                    hierarchy[tag.id]['descendants'].update(hierarchy[child_tag.id]['descendants_and_self'])
                    hierarchy[tag.id]['descendants_and_self'].update(hierarchy[child_tag.id]['descendants_and_self'])
            hierarchy[tag.id]['descendants_and_self'].add(tag.id)  # add self
        else:
            raise ValueError(f'type_=[{type_}] but must be either "ancestors" or "descendants"')

    tags = Tag.objects.filter(user=user)
    hierarchy = {}

    for type_ in ['ancestors', 'descendants']:
        for tag in tags:
            build_hierarchy(hierarchy=hierarchy, tag=tag, type_=type_, visited=set())

    # Add count_questions_all and count_questions_tag
    for tag in tags:
        hierarchy[tag.id]['count_questions_all'] = Question.objects.filter(
            tag__id__in=hierarchy[tag.id]['descendants_and_self']
            ).distinct().count()

        hierarchy[tag.id]['count_questions_tag'] = tag.questions.distinct().count()

    return hierarchy

def expand_all_tag_ids(hierarchy, tag_ids):
    '''
    Given a hierarchy dict, expand all tag id's in tag_ids.
    Parameters:
        hierarchy (dict) - the hierarchy dict, per the structure above
        tag_ids (iterable) - an iterable of Tag.id's (list, set, ...), e.g., [1, 2]
    '''
    expanded_tag_id_list = set()
    for tag_id in tag_ids:
        expanded_tag_id_list.update(hierarchy[tag_id]['descendants_and_self'])
    return expanded_tag_id_list