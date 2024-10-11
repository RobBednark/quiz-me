from questions.models import Tag

class VerifyTagIds:
    """
    Verify that the tag_ids are valid:
        - The tag_ids are owned by the user
        - The tag_ids exist
    """
    def __init__(self, tag_ids, user):
        self.tag_ids = tag_ids
        self.user = user
        error = ''

        tags_not_owned = self._tags_not_owned_by_user()
        if tags_not_owned:
            error += f'Tag ids are not owned by user: {tags_not_owned}.'

        tag_ids_dont_exist = self._tag_ids_that_dont_exist()
        if tag_ids_dont_exist:
            error += f'Tag ids do not exist: {tag_ids_dont_exist}.'

        if error:
            raise ValueError(error)
    def _tags_not_owned_by_user(self):
        """
        Return a list of all self.tag_ids that are not owned by self.user.
        """
        ids_not_owned_by_user = Tag.objects.filter(id__in=self.tag_ids).exclude(user=self.user).values_list('id', flat=True)
        return [int(tag_id) for tag_id in ids_not_owned_by_user]

    def _tag_ids_that_dont_exist(self):
        """
        Return a list of all self.tag_ids that do not exist.
        """
        existing_tag_ids = set(Tag.objects.filter(id__in=self.tag_ids).values_list('id', flat=True))
        non_existent_tag_ids = [int(tag_id) for tag_id in self.tag_ids if tag_id not in existing_tag_ids]
        return non_existent_tag_ids