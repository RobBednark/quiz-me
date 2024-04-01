from django.core.management.base import BaseCommand
import questions.models as models

CR = chr(13)


class Command(BaseCommand):
    help = "run this script"

    def handle(self, *args, **options):
        questions = models.Question.objects.all()
        # tags = models.Tag.objects.all()
        # question_tags = models.QuestionTag.objects.all()
        # user_tags = models.UserTag.objects.all()
        # user = models.User.objects.all()[0]
        # user_tags = models.UserTag.objects.filter(enabled=True, user=user)
        # question_tags = models.QuestionTag.objects.filter(tag__in=user_tags, enabled=True)
        for num, question in enumerate(questions.order_by('id')):
            question_ = question.question.replace(CR, '')
            print("\n=== [%s] of [%s] ============================= id=[%s] ==" % (num + 1, len(questions), question.id))
            print('Q: ', question_)
            print('questiontag_set : %s' % [str(question_tag.tag.name) for question_tag in question.questiontag_set.all()])
            print('datetime_added  =[%s]' % question.datetime_added)
            print('datetime_updated=[%s]' % question.datetime_updated)
            if question.answer:
                print("---------------------------------------------- id=[%s] --" % question.answer.id)
                answer_ = question.answer.answer.replace(CR, '')
                print('A:')
                print(answer_)
            else:
                print("-" * 80)
                print("(no answer)")
