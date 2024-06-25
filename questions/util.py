from questions import models


def assign_question_to_user(user, question, tag_name):
    tag = models.Tag.objects.create(name=tag_name)

    models.QuestionTag.objects.create(
        tag=tag,
        question=question,
        enabled=True
    )

    return tag


def schedule_question_for_user(user, question):
    schedule = models.Schedule.objects.create(
        user=user,
        question=question,
    )

    return schedule
